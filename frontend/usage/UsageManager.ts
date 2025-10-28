import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import type { DayBucket, InteractionStats, StopRouteUsage, StopUsage, TimeBucket, Usage, PredictedStop } from './usageModels';
import haversine from "haversine-distance";


function getTimeBucket(date: Date): TimeBucket {
    const hour = date.getHours();
    if (hour >= 5 && hour < 10) return "morning";
    if (hour >= 10 && hour < 14) return "midday";
    if (hour >= 14 && hour < 18) return "afternoon";
    if (hour >= 18 && hour < 22) return "evening";
    return "night";
}

function getDayBucket(date: Date): DayBucket {
    const days: DayBucket[] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    return days[date.getDay()];
}



export interface UsageDB extends DBSchema {
    routes: {
        key: number; // routeId
        value: Usage['routes'][string];
    }
    stops: {
        key: string; // stopId
        value: Usage['stops'][string];
    }
    meta: {
        key: string;
        value: { version: number, learningEnabled: boolean };
    }
}

export default class UsageManager {
    private static instance: UsageManager;
    private db!: IDBPDatabase<UsageDB>;


    private constructor() { }

    static async getInstance() {
        if (!UsageManager.instance) {
            UsageManager.instance = new UsageManager();
            await UsageManager.instance.initDB();
        }
        return UsageManager.instance;
    }

    isUsageEnabled(): boolean {
        try {
            const usageToggle = localStorage.getItem('usageToggle') === 'true';
            return usageToggle;
        } catch (e) {
            console.error("Error accessing usage toggle setting:", e);
            return true;
        }
    }


    private async initDB() {
        this.db = await openDB<UsageDB>('nextbus-usage', 1, {
            upgrade(db) {
                db.createObjectStore('routes');
                db.createObjectStore('stops');
                db.createObjectStore('meta');
            }
        });
        // load localStorage flags if needed
        const usageToggle = localStorage.getItem('usageToggle');
        if (usageToggle === null) {
            localStorage.setItem('usageToggle', 'true');
        }
    }

    async getAllUsage(): Promise<Usage> {
        const routesArray = await this.db.getAll('routes');
        const stopsArray = await this.db.getAll('stops');

        const routes: { [routeId: string]: Usage['routes'][string] } = {};
        routesArray.forEach((route) => {
            routes[route.id.toString()] = route;
        });

        const stops: { [stopId: string]: Usage['stops'][string] } = {};
        stopsArray.forEach((stop) => {
            stops[stop.id] = stop;
        });

        routesArray.sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
        stopsArray.sort((a, b) => (b.score ?? 0) - (a.score ?? 0));

        return { routes, stops };
    }

    async clearAllUsage() {
        await this.db.clear('routes');
        await this.db.clear('stops');
    }

    private computeScore(stats: InteractionStats): number {
        let score = 0;
        for (const day in stats) {
            const times = stats[day as DayBucket]!;
            for (const time in times) {
                const s = times[time as TimeBucket]!;
                score += s.tracked * 5 + s.filter * 3 + s.tapped;
            }
        }
        return score;
    }

    async logStop(stopId: string, stopName: string, stopLat: number, stopLon: number, favourite: boolean, interactionType: 'filter' | 'tracked' | 'tapped', date: Date = new Date()) {
        if (!(this.isUsageEnabled())) {
            console.log("Usage tracking is disabled; not logging stop interaction");
            return;
        }
        const day = getDayBucket(date);
        const time = getTimeBucket(date);

        console.log(`Logging stop ${stopId} (${stopName}) fav ${favourite} interaction ${interactionType} at ${day} ${time}`);

        const stop = await this.db.get('stops', stopId) || {
            id: stopId,
            name: stopName,
            lat: stopLat,
            lon: stopLon,
            favourite: favourite,
            lastActive: date.getTime(),
            routes: {} as { [routeId: string]: StopRouteUsage },
            score: 0,
            interactions: {} as InteractionStats
        };

        const timeSinceLastActive = date.getTime() - stop.lastActive;

        // update lastActive only if more than 2 minutes have passed
        if (timeSinceLastActive < 2 * 60 * 1000) {
            console.log(`Not updating lastActive for stop ${stopId} as only ${timeSinceLastActive / 1000}s have passed since last active`);
            return;
        }


        stop.lastActive = date.getTime();
        stop.favourite = favourite;

        if (!stop.interactions[day]) stop.interactions[day] = {};
        if (!stop.interactions[day]![time]) stop.interactions[day]![time] = { filter: 0, tracked: 0, tapped: 0 };
        stop.interactions[day]![time][interactionType] += 1;

        stop.score = this.computeScore(stop.interactions);

        await this.db.put('stops', stop, stopId);
    }

    async logRoute(stopId: string,
        stopName: string,
        stopLat: number,
        stopLon: number,
        routeId: number,
        lineName: string,
        description: string,
        destination: string | null,
        interactionType: 'filter' | 'tracked' | 'tapped',
        date: Date = new Date()
    ) {
        if (!(this.isUsageEnabled())) {
            console.log("Usage tracking is disabled; not logging route interaction");
            return;
        }
        const day = getDayBucket(date);
        const time = getTimeBucket(date);

        console.log(`Logging route interaction: stop ${stopId} (${stopName}), route ${routeId} (${lineName}), destination ${destination}, interaction ${interactionType} at ${day} ${time}`);

        const stop = await this.db.get('stops', stopId) || {
            id: stopId,
            name: stopName,
            lat: stopLat,
            lon: stopLon,
            favourite: false,
            lastActive: 0,
            routes: {} as { [lineName: string]: StopRouteUsage },
            interactions: {} as InteractionStats,
            score: 0
        };

        stop.lastActive = date.getTime();

        if (!destination) {
            destination = description;
        }
        if (!stop.routes[lineName]) stop.routes[lineName] = { destinations: {} };
        const dests = stop.routes[lineName].destinations;
        if (!dests[destination]) dests[destination] = { score: 0, interactions: {} };

        const stats = dests[destination].interactions;
        if (!stats[day]) stats[day] = {};
        if (!stats[day]![time]) stats[day]![time] = { filter: 0, tracked: 0, tapped: 0 };
        stats[day]![time][interactionType] += 1;

        dests[destination].score = this.computeScore(stats);

        await this.db.put('stops', stop, stopId);

        const route = await this.db.get('routes', routeId) || {
            id: routeId,
            lineName,
            description,
            stops: [],
            favourite: false,
            lastActive: 0,
            score: 0,
            interactions: {} as InteractionStats,
        };

        const timeSinceLastActive = date.getTime() - route.lastActive;

        // update lastActive only if more than 2 minutes have passed
        if (timeSinceLastActive < 2 * 60 * 1000) {
            console.log(`Not updating lastActive for route ${route.lineName} as only ${timeSinceLastActive / 1000}s have passed since last active`);
            return;
        }

        route.lastActive = date.getTime();
        if (!route.interactions) route.interactions = {};
        if (!route.interactions[day]) route.interactions[day] = {};
        if (!route.interactions[day]![time]) route.interactions[day]![time] = { filter: 0, tracked: 0, tapped: 0 };
        route.interactions[day]![time][interactionType] += 1;

        route.score = this.computeScore(route.interactions);

        if (!route.stops.includes(stopId)) route.stops.push(stopId);

        await this.db.put('routes', route, routeId);
    }

    scoreStop(stop: StopUsage, date: Date, distance: number): number {
        const day = getDayBucket(date);
        const time = getTimeBucket(date);

        const interactions = stop.interactions?.[day as DayBucket]?.[time as TimeBucket];
        let dayTimeScore = 0;
        if (interactions) {
            dayTimeScore += interactions.tracked * 5 + interactions.filter * 3 + interactions.tapped;
        }

        let effectiveScore = stop.score / 5 + dayTimeScore; // base score plus day/time score

        effectiveScore *= 1 / (1 + distance / 500); // distance decay: half score at 500m

        if (stop.favourite) effectiveScore *= 1.2; // favourite boost
        const decayFactor = 0.5 + 0.5 * (stop.lastActive / date.getTime()); // simple 0.5–1 scaling
        effectiveScore *= decayFactor;

        return effectiveScore;
    }

    async predictStopAndRoutes(
        lat?: number,
        lon?: number,
        date: Date = new Date()
    ): Promise<Array<
        PredictedStop
    >> {
        // gets the top 3 stops and the most likely routes for the given location and time

        const day = getDayBucket(date);
        const time = getTimeBucket(date);


        const allStops = await this.db.getAll('stops') as StopUsage[];

        const scoredStops = allStops.map(stop => {
            let distance = 0;
            if (lat !== undefined && lon !== undefined) {
                distance = haversine([lat, lon], [stop.lat, stop.lon]);
            }
            const effectiveScore = this.scoreStop(stop, date, distance);

            return { stopId: stop.id, stop, stopName: stop.name, score: effectiveScore };
        });

        scoredStops.sort((a, b) => b.score - a.score);

        const topStops = scoredStops.slice(0, 3);

        const results = topStops.map(({ stopId, stop, stopName, score }) => {
            const routes: { lineName: string; destination: string; score: number }[] = [];

            let maxRouteScore = 0;

            for (const [lineName, routeUsage] of Object.entries(stop.routes)) {
                for (const [destination, destUsage] of Object.entries(routeUsage.destinations)) {
                    const interactions = destUsage.interactions?.[day]?.[time];
                    let dayTimeScore = 0;
                    if (interactions) {
                        dayTimeScore = interactions.filter * 5 + interactions.tracked * 3 + interactions.tapped;
                    }
                    let routeScore = destUsage.score / 5 + dayTimeScore;
                    if (routeScore > 0) routes.push({ lineName, destination, score: routeScore });
                    if (routeScore > maxRouteScore) maxRouteScore = routeScore;
                }
            }

            routes.sort((a, b) => b.score - a.score);

            const topRoutes = routes.slice(0, 2);

            const routeBoostFactor = 0.3; // 30% of top route score
            const boostedScore = score + maxRouteScore * routeBoostFactor;

            return { stopId, stopName, score: boostedScore, topRoutes };
        });

        return results;

    }
}
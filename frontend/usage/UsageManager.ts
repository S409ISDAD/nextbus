import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import type { DayBucket, Interaction, StopUsage, TimeBucket, Usage, PredictedStop } from './usageModels';
import haversine from "haversine-distance";
import { USAGE_TRACKING } from '../src/settings';


function getTimeBucket(date: Date): TimeBucket {
    const hour = date.getHours();
    if (hour >= 5 && hour < 11) return "morning";
    if (hour >= 11 && hour < 14) return "midday";
    if (hour >= 14 && hour < 18) return "afternoon";
    if (hour >= 18 && hour < 22) return "evening";
    return "night";
}

function getDayBucket(date: Date): DayBucket {
    return [0, 6].includes(date.getDay()) ? "weekend" : "weekday";
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

    private computeScore(interactions: Interaction[], now: number = Date.now()): number {
        const WEIGHTS = { tracked: 5, filter: 3, tapped: 1 };
        const DECAY_HALF_LIFE = 7 * 24 * 60 * 60 * 1000; // 7 days
        const decay = (t: number) => Math.exp(-t / DECAY_HALF_LIFE);

        let score = 0;
        for (const i of interactions) {
            const age = now - i.timestamp;
            const w = WEIGHTS[i.action] ?? 1;
            score += w * decay(age);
        }
        return score;
    }

    async logStop(
        stopId: string,
        stopName: string,
        stopLat: number,
        stopLon: number,
        favourite: boolean,
        interactionType: 'filter' | 'tracked' | 'tapped',
        date: Date = new Date(),
    ) {
        if (!(this.isUsageEnabled() && USAGE_TRACKING)) {
            console.log("Usage tracking is disabled; not logging stop interaction");
            return;
        }

        const day = getDayBucket(date);
        const time = getTimeBucket(date);

        console.log(`Logging stop ${stopId} (${stopName}) fav ${favourite} interaction ${interactionType} at ${day} ${time}`);

        const stop = (await this.db.get('stops', stopId)) || {
            id: stopId,
            name: stopName,
            lat: stopLat,
            lon: stopLon,
            favourite,
            lastActive: 0,
            routes: {},
            interactions: [],
            score: 0,
        };

        const timeSinceLastActive = date.getTime() - stop.lastActive;

        // update lastActive only if more than 2 minutes have passed
        if (timeSinceLastActive < 2 * 60 * 1000) {
            console.log(`Not updating lastActive for stop ${stopId} as only ${timeSinceLastActive / 1000}s have passed since last active`);
            return;
        }

        const interaction: Interaction = {
            timestamp: date.getTime(),
            action: interactionType,
            timeBucket: time,
            dayType: day,
        };

        stop.interactions.push(interaction);
        stop.lastActive = date.getTime();
        stop.favourite = favourite;
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

        if (!(this.isUsageEnabled() && USAGE_TRACKING)) {
            console.log("Usage tracking is disabled; not logging route interaction");
            return;
        }
        const dayType = getDayBucket(date);
        const timeBucket = getTimeBucket(date);

        console.log(`Logging route interaction: stop ${stopId} (${stopName}), route ${routeId} (${lineName}), destination ${destination}, interaction ${interactionType} at ${dayType} ${timeBucket}`);

        const interaction: Interaction = {
            timestamp: date.getTime(),
            action: interactionType,
            timeBucket,
            dayType,
        };

        const stop = (await this.db.get('stops', stopId)) || {
            id: stopId,
            name: stopName,
            lat: stopLat,
            lon: stopLon,
            favourite: false,
            lastActive: 0,
            routes: {},
            interactions: [],
            score: 0,
        };


        stop.lastActive = date.getTime();
        stop.interactions.push(interaction);

        if (!destination) destination = description;
        if (!stop.routes[lineName]) stop.routes[lineName] = { destinations: {} };
        if (!stop.routes[lineName].destinations[destination])
            stop.routes[lineName].destinations[destination] = { score: 0, interactions: [] };

        const dest = stop.routes[lineName].destinations[destination];
        dest.interactions.push(interaction);
        dest.score = this.computeScore(dest.interactions);
        stop.score = this.computeScore(stop.interactions);

        await this.db.put('stops', stop, stopId);

        const route = (await this.db.get('routes', routeId)) || {
            id: routeId,
            lineName,
            description,
            stops: [],
            favourite: false,
            lastActive: 0,
            score: 0,
            interactions: [],
        };

        const timeSinceLastActive = date.getTime() - route.lastActive;

        // update lastActive only if more than 2 minutes have passed
        if (timeSinceLastActive < 2 * 60 * 1000) {
            console.log(`Not updating lastActive for route ${route.lineName} as only ${timeSinceLastActive / 1000}s have passed since last active`);
            return;
        }


        route.lastActive = date.getTime();
        if (!route.interactions) route.interactions = [];
        route.interactions.push(interaction);
        route.score = this.computeScore(route.interactions);
        if (!route.stops.includes(stopId)) route.stops.push(stopId);

        await this.db.put('routes', route, routeId);
    }

    scoreStop(stop: StopUsage, date: Date, distance: number): number {
        const recencyScore = this.computeScore(stop.interactions, date.getTime());
        let effectiveScore = stop.score * 0.6 + recencyScore * 0.4;

        effectiveScore *= 1 / (1 + distance / 500); // distance decay
        if (stop.favourite) effectiveScore *= 1.2;

        // mild recency scaling
        const decayFactor = 0.5 + 0.5 * (stop.lastActive / date.getTime());
        effectiveScore *= decayFactor;

        return effectiveScore;
    }


    async predictStopAndRoutes(
        lat?: number,
        lon?: number,
        date: Date = new Date()
    ): Promise<PredictedStop[]> {
        // gets the top 3 stops and the most likely routes for the given location and time

        const dayType = getDayBucket(date);
        const timeBucket = getTimeBucket(date);

        const now = date.getTime();

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

        let results = topStops.map(({ stopId, stop, stopName, score }) => {
            const routes: { lineName: string; destination: string; score: number }[] = [];
            let maxRouteScore = 0;

            for (const [lineName, routeUsage] of Object.entries(stop.routes)) {
                for (const [destination, destUsage] of Object.entries(routeUsage.destinations)) {
                    const relevant = destUsage.interactions.filter(
                        i => i.dayType === dayType && i.timeBucket === timeBucket
                    );

                    // if there are relevant interactions, compute score based on them
                    let routeTemporalScore = 0;
                    if (relevant.length > 0) {
                        routeTemporalScore = this.computeScore(relevant, now);
                    } else {
                        // no relevant interactions, fall back to overall interactions
                        // use a small fraction of full dest score to avoid 0
                        routeTemporalScore = this.computeScore(destUsage.interactions, now) * 0.25;
                    }

                    if (routeTemporalScore > 0) {
                        routes.push({ lineName, destination, score: routeTemporalScore });
                        if (routeTemporalScore > maxRouteScore) maxRouteScore = routeTemporalScore;
                    }
                }
            }

            if (routes.length === 0) {
                // no route data, return empty
                return null;
            }

            routes.sort((a, b) => b.score - a.score);
            const topRoutes = routes.slice(0, 2);

            // 3) Boost stop by top route(s)
            const routeBoostFactor = 0.3; // tuneable
            const boostedScore = score + maxRouteScore * routeBoostFactor;

            return { stopId, stopName, score: boostedScore, topRoutes };
        });

        results = results.filter((r): r is PredictedStop => r !== null);

        return results as PredictedStop[];

    }
}
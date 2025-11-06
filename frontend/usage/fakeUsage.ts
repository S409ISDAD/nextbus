import UsageManager from "./UsageManager";

const usageManager = UsageManager.getInstance();

function randomChoice<T>(arr: T[]): T {
    return arr[Math.floor(Math.random() * arr.length)];
}

function randomBetween(min: number, max: number): number {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

const commonPatterns = [
    {
        stop: { id: "1900HA110364", name: "New Alresford Robertson Road (adj)", lat: 51.08332, lon: -1.1687 },
        route: { id: 1895, number: "64", name: "Winchester - Alton" },
        dest: "Alton",
        typicalHour: 9,
        variance: 20, // minutes
        days: [1, 2, 3, 4, 5], // weekdays
    },
    {
        stop: { id: "1900HA020369", name: "Alton Rail Station (Stop R)", lat: 51.15184, lon: -0.96769 },
        route: { id: 1895, number: "64", name: "Winchester - Alton" },
        dest: "Winchester",
        typicalHour: 16,
        variance: 30,
        days: [1, 2, 3, 4, 5],
    },
    {
        stop: { id: "1900HA030512", name: "Winchester Bus Station (Stand E)", lat: 51.06352, lon: -1.31223 },
        route: { id: 1703, number: "1", name: "City Centre Loop" },
        dest: "Winchester City",
        typicalHour: 11,
        variance: 60,
        days: [6, 0], // weekend
    },
];

const rareTrips = [
    {
        stop: { id: "1900PO004121", name: "Portsmouth The Hard Interchange", lat: 50.79853, lon: -1.10735 },
        route: { id: 4001, number: "X4", name: "Portsmouth - Southampton" },
        dest: "Southampton",
    },
    {
        stop: { id: "1900SO100029", name: "Southampton Central Station", lat: 50.90733, lon: -1.41439 },
        route: { id: 4012, number: "Bluestar 1", name: "Southampton - Winchester" },
        dest: "Winchester",
    },
];

async function simulateUsageLogs(startDate: Date, days: number) {
    for (let d = 0; d < days; d++) {
        const date = new Date(startDate);
        date.setUTCDate(date.getUTCDate() + d);
        const weekday = date.getUTCDay();

        for (const pattern of commonPatterns) {
            if (!pattern.days.includes(weekday)) continue;
            const time = new Date(date);
            time.setUTCHours(pattern.typicalHour);
            time.setUTCMinutes(randomBetween(-pattern.variance, pattern.variance) + 30);
            const action: 'tapped' | 'tracked' | 'filter' = randomChoice(['tapped', 'tracked', 'filter']);

            await (await usageManager).logStop(
                pattern.stop.id,
                pattern.stop.name,
                pattern.stop.lat,
                pattern.stop.lon,
                true,
                "tapped",
                time
            );

            await (await usageManager).logRoute(
                pattern.stop.id,
                pattern.stop.name,
                pattern.stop.lat,
                pattern.stop.lon,
                pattern.route.id,
                pattern.route.number,
                pattern.route.name,
                pattern.dest,
                "tracked",
                time
            );
        }

        // Inject 10% chance of one-off or odd trip
        if (Math.random() < 0.1) {
            const rare = randomChoice(rareTrips);
            const rareTime = new Date(date);
            rareTime.setUTCHours(randomBetween(6, 22), randomBetween(0, 59));
            await (await usageManager).logStop(
                rare.stop.id,
                rare.stop.name,
                rare.stop.lat,
                rare.stop.lon,
                true,
                "tapped",
                rareTime
            );
            await (await usageManager).logRoute(
                rare.stop.id,
                rare.stop.name,
                rare.stop.lat,
                rare.stop.lon,
                rare.route.id,
                rare.route.number,
                rare.route.name,
                rare.dest,
                "tracked",
                rareTime
            );
        }
    }
}

async function testUsageLearningSimulation() {
    const manager = await usageManager;
    await manager.clearAllUsage();

    const start = new Date("2025-08-01T00:00:00Z");
    await simulateUsageLogs(start, 140); // 20 weeks

    // Run predictions for varied times
    const testCases = [
        { label: "Morning commute", time: new Date("2025-11-11T08:45:00Z"), loc: [51.08332, -1.1687] },
        { label: "Afternoon return", time: new Date("2025-11-11T16:10:00Z"), loc: [51.15184, -0.96769] },
        { label: "Weekend trip", time: new Date("2025-11-09T11:00:00Z"), loc: [51.06352, -1.31223] },
        { label: "Off-peak evening", time: new Date("2025-11-10T21:30:00Z"), loc: [51.15184, -0.96769] },
    ];

    for (const { label, time, loc } of testCases) {
        const predicted = await manager.predictStopAndRoutes(loc[0], loc[1], time);
        console.log(`\n=== ${label} (${time.toISOString()}) ===`);
        for (const p of predicted) {
            console.log(
                `${p.stopName} — score ${p.score.toFixed(2)} | routes: ${p.topRoutes
                    .map(r => `${r.lineName}→${r.destination} (${r.score.toFixed(2)})`)
                    .join(", ")}`
            );
        }
    }
}

export { testUsageLearningSimulation };
export type TimeBucket = "morning" | "midday" | "afternoon" | "evening" | "night";
export type DayBucket = "weekday" | "weekend";


export type Interaction = {
    timestamp: number;            // unix ms
    action: 'tracked' | 'tapped' | 'filter';
    timeBucket: TimeBucket;       // morning, midday, etc.
    dayType: DayBucket;         // weekday or weekend
};


export interface DestinationUsage {
    score: number;               // weighted sum of interactions for quick ranking
    interactions: Interaction[];
}

export interface StopRouteUsage {
    destinations: {
        [destinationName: string]: DestinationUsage;
    }
}

export interface StopUsage {
    id: string;
    name: string;
    lat: number;
    lon: number;
    interactions: Interaction[];
    favourite: boolean;
    score: number;                    // weighted sum for ranking
    lastActive: number;               // unix timestamp
    routes: {
        [lineName: string]: StopRouteUsage;
    }
}

export interface RouteUsage {
    id: number;
    lineName: string;
    description: string;
    stops: string[];                  // optional list of stopIds
    favourite: boolean;
    lastActive: number;               // unix timestamp
    score: number;                    // weighted sum for ranking
    interactions?: Interaction[];  // optional aggregated across stops
}

export interface Usage {
    routes: {
        [routeId: string]: RouteUsage;
    };
    stops: {
        [stopId: string]: StopUsage;
    };
}

export interface PredictedStop {
    stopId: string;
    stopName: string;
    score: number;
    topRoutes: { lineName: string; destination: string; score: number }[];
}
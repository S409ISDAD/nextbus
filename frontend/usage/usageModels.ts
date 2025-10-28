export type TimeBucket = "morning" | "midday" | "afternoon" | "evening" | "night";
export type DayBucket = "Mon" | "Tue" | "Wed" | "Thu" | "Fri" | "Sat" | "Sun";


export type InteractionStats = {
    [day in DayBucket]?: {
        [time in TimeBucket]?: {
            filter: number;
            tracked: number;
            tapped: number;
        }
    }
};


export interface DestinationUsage {
    score: number;               // weighted sum of interactions for quick ranking
    interactions: InteractionStats;
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
    interactions: InteractionStats;
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
    interactions?: InteractionStats;  // optional aggregated across stops
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
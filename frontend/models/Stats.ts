export interface Stats {
    total_active: number;
    unique_active: number;
    total_buses: number;
    total_stops: number;
}

export interface StatsTimeSeries {
    timestamp: string;
    unique: number;
}
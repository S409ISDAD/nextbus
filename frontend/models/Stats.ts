export interface Stats {
    total_active: number;
    unique_active: number;
}

export interface StatsTimeSeries {
    timestamp: string;
    total: number;
    unique: number;
}
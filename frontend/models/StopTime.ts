export interface StopTime {
    stop_id: string
    name: string;
    aimed_departure_time: Date;
    actual_departure_time?: Date;
}
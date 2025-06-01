export interface StopTime {
    stop_id: string
    name: string;
    aimed_time: Date;
    expt_time?: Date;
    actual_time?: Date;
}
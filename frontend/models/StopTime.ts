export interface StopTime {
    stop_id: string
    name: string;
    aimed_time: Date;
    expt_time?: Date;
    coords: number[];
    track: number[][];
    set_down: boolean;
}
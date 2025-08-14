export interface StopTime {
    stop_id: string
    name: string;
    aimed_time: string;
    expt_time?: string;
    departed?: boolean;
    coords: number[];
    track: number[][];
    set_down: boolean;
    timing_status: "PTP" | "OTH";
}
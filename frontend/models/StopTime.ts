export interface StopTime {
    stop_id: string;
    name: string;
    aimed_time: string;
    expt_time?: string;
    departed: boolean;
    coords: number[];
    track?: number[][];
    set_down: boolean;
    pick_up: boolean;
    timing_status: "OTH" | "PTP" | "TIP";
    call_condition?: string;
    track_distance?: number;
}
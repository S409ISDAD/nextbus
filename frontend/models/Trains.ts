import type { Prediction } from "./Bus";

export interface Location {
    name: string;
    crs: string;
    tiploc: string | string[];
    country?: string;
    system?: string;
}

export interface OriginDestination {
    tiploc: string | string[];
    description: string;
    workingTime: string;
    publicTime: string;
}

export interface LocationDetail {
    realtimeActivated?: boolean;
    tiploc: string | string[];
    crs: string;
    description: string;
    wttBookedArrival?: string;
    wttBookedDeparture?: string;
    gbttBookedArrival?: string;
    gbttBookedDeparture?: string;
    origin: OriginDestination[];
    destination: OriginDestination[];
    isCall: boolean;
    isPublicCall: boolean;
    realtimeArrival?: string;
    realtimeArrivalActual?: boolean;
    realtimeDeparture?: string;
    realtimeDepartureActual?: boolean;
    expectedDeparture?: string;
    expectedArrival?: string;
    scheduledDeparture?: string;
    scheduledArrival?: string;
    platform?: string;
    platformConfirmed?: boolean;
    platformChanged?: boolean;
    displayAs: string;
}

export interface Train {
    locationDetail: LocationDetail;
    serviceUid: string;
    runstring: string;
    trainIdentity: string;
    runningIdentity?: string;
    atocCode: string;
    atocColor?: string;
    atocName: string;
    delay?: number;
    timeTo?: string;
    serviceType: string;
    isPassenger: boolean;
}


export interface Filter {
    destination?: Location | null;
    origin?: Location | null;
}

export interface StationResponse {
    location: Location;
    filter?: Filter | null;
    services: Train[] | null;
}

export interface ServiceLocation {
    realtimeActivated: boolean;
    tiploc: string | string[];
    crs: string;
    description: string;

    gbttBookedArrival?: string;
    gbttBookedDeparture?: string;

    wttBookedArrival?: string;
    wttBookedDeparture?: string;

    origin: OriginDestination[];
    destination: OriginDestination[];

    isCall: boolean;
    isPublicCall: boolean;

    realtimeArrival?: string;
    realtimeArrivalActual?: boolean;
    realtimeDeparture?: string;
    realtimeDepartureActual?: boolean;
    expectedArrival?: string;
    expectedDeparture?: string;
    scheduledArrival?: string;
    scheduledDeparture?: string;

    departed?: boolean;
    delay?: number;

    platform?: string;
    platformConfirmed?: boolean;
    platformChanged?: boolean;

    line?: string;
    lineConfirmed?: boolean;

    serviceLocation?: string;
    displayAs: string;
}

export interface TrainService {
    serviceUid: string;
    runDate: string;
    serviceType: string;
    isPassenger: boolean;
    trainIdentity: string;

    fromStop?: ServiceLocation;
    toStop?: ServiceLocation;
    duration?: number;
    fastest?: boolean;

    powerType?: string;
    trainClass?: string;

    timeTo?: string;

    atocCode: string;
    atocName: string;

    sequence?: number;
    progress?: number;

    nextStation?: ServiceLocation;

    atocColor?: string;
    delay?: number;

    predictions?: Prediction[];

    finished?: boolean;

    performanceMonitored?: boolean;

    origin: OriginDestination[];
    destination: OriginDestination[];
    locations: ServiceLocation[];

    realtimeActivated?: boolean;
    runningIdentity?: string;
}
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
    platform?: string;
    platformConfirmed?: boolean;
    platformChanged?: boolean;
    displayAs: string;
}

export interface Train {
    locationDetail: LocationDetail;
    serviceUid: string;
    runDate: string;
    trainIdentity: string;
    runningIdentity?: string;
    atocCode: string;
    atocName: string;
    serviceType: string;
    isPassenger: boolean;
    expectedDeparture?: Date;
    expectedArrival?: Date;
    scheduledDeparture?: Date;
    scheduledArrival?: Date;
}

export interface TrainResponse {
    location: Location;
    filter?: string | null;
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

    powerType?: string;
    trainClass?: string;

    atocCode: string;
    atocName: string;

    performanceMonitored?: boolean;

    origin: OriginDestination[];
    destination: OriginDestination[];
    locations: ServiceLocation[];

    realtimeActivated?: boolean;
    runningIdentity?: string;
}
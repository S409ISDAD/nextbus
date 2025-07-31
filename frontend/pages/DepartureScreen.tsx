import { useEffect, useRef, useState } from "react";
import { isTrackedBus, type Departure } from "../models/Bus";
import fetchDepartures from "../utils/getDepartures";

import { useParams } from "react-router";

import timeTo, { toTime } from "../utils/timeUtils";

const DepartureScreen: React.FC = () => {
    const { stop_id } = useParams();

    const firstFetch = useRef(true);

    const [buses, setBuses] = useState<Departure[]>([]);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();

            const newBuses = buses
                .map((bus) => {
                    return {
                        ...bus,
                        timeto: timeTo(bus),
                    };
                })
                .filter(
                    (bus) =>
                        new Date(new Date(bus.expected).getTime() + 60 * 1000) >
                        now
                );

            setBuses(newBuses);
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed, buses]);

    useEffect(() => {
        let interval: any;
        const getData = async (id: string) => {
            if (fetching) {
                return;
            }
            setFetching(true);
            try {
                const schedDeparturesPromise = fetchDepartures(id, "scheduled");
                const departuresPromise = fetchDepartures(id, "");

                if (firstFetch.current) {
                    const departures = await schedDeparturesPromise;

                    if (departures) {
                        setBuses(departures.updatedBuses);
                        setRefreshed(departures.timestamp);
                    }

                    const liveResult = await fetchDepartures(id, "live");
                    if (liveResult) {
                        setBuses(liveResult.updatedBuses);

                        setRefreshed(liveResult.timestamp);
                    }
                    firstFetch.current = false;
                } else {
                    const departures = await departuresPromise;

                    if (departures) {
                        setBuses(departures.updatedBuses);
                        setRefreshed(departures.timestamp);
                    }
                }
                // else {
                //     setMsg("Failed to fetch departures.");
                // }
            } catch {
                console.log("uh oh");
            } finally {
                setFetching(false);
            }
        };
        const init = async (stop_id: string) => {
            try {
                await getData(stop_id);
                interval = setInterval(() => getData(stop_id), 30000);
            } catch (error) {
                console.error("Init error:", error);
                setFetching(false);
            }
        };

        if (stop_id) {
            init(stop_id);
        }

        return () => clearInterval(interval);
    }, [stop_id]);

    return (
        <div className="flex flex-col h-full gap-3 p-3 bg-black">
            {buses.map((bus) => (
                <div className="flex flex-row justify-between text-xl font-bold align-center">
                    <span>
                        {isTrackedBus(bus) ? bus.service.line_name : bus.line}{" "}
                        to {bus.destination}
                    </span>

                    <span>
                        {new Date(bus.expected).getTime() -
                            new Date().getTime() >
                        45 * 60 * 1000
                            ? toTime(bus.expected)
                            : bus.timeto}
                    </span>
                </div>
            ))}
        </div>
    );
};

export default DepartureScreen;

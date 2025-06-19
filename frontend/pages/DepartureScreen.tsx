import { useEffect, useState } from "react";
import { isTrackedBus, type Departure } from "../models/Bus";
import fetchDepartures from "../utils/getDepartures";

import { useParams } from "react-router";

import timeTo from "../utils/timeTo";

const DepartureScreen: React.FC = () => {
    const { stop_id } = useParams();

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
                    (bus) => new Date(bus.expected.getTime() + 60 * 1000) > now
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
                const departuresPromise = fetchDepartures(id);

                const departures = await departuresPromise;
                if (departures) {
                    console.log(departures.updatedBuses);
                    setBuses(departures.updatedBuses);
                    setRefreshed(departures.timestamp);
                }
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
    }, [stop_id, fetching]);

    return (
        <div className="p-5">
            <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-3">
                    {buses.map((bus) => (
                        <div className="flex flex-row justify-between align-center">
                            <div className="flex flex-col justify-around">
                                <div className="flex flex-row flex-wrap items-center gap-1">
                                    <span className="text-2xl font-bold">
                                        {isTrackedBus(bus)
                                            ? bus.service.line_name
                                            : bus.line}{" "}
                                        to {bus.destination}
                                    </span>
                                </div>
                            </div>
                            <div className="flex flex-row flex-wrap items-center justify-end gap-2 md:gap-4">
                                <span className="text-xl font-bold ">
                                    {bus.timeto}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default DepartureScreen;

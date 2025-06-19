import { useEffect, useState } from "react";
import { isTrackedBus, type Departure } from "../models/Bus";
import type { Stop } from "../models/Stop";
import fetchDepartures from "../utils/getDepartures";
import getStopData from "../utils/getStopData";
import { useNavigate, useParams } from "react-router";
import { Skeleton } from "@radix-ui/themes";
import { Card } from "../components/ui/Card";
import timeTo, { lateness } from "../utils/timeTo";
import getClosestStop from "../utils/closestStop";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faSatelliteDish,
    faSlash,
    faUpRightFromSquare,
} from "@fortawesome/free-solid-svg-icons";
import clsx from "clsx";

const DepartureScreen: React.FC = () => {
    const { stop_id } = useParams();

    const navigate = useNavigate();

    const [buses, setBuses] = useState<Departure[]>([]);
    const [stop, setStop] = useState<Stop>();
    const [closestStop, setClosest] = useState<string>();
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");
    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            const diffSec = Math.floor(
                (now.getTime() - lastRefreshed.getTime()) / 1000
            );
            const min = Math.floor(diffSec / 60);
            const sec = diffSec % 60;

            setElapsed(min > 0 ? `${min}m ${sec}s` : `${sec}s`);

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
                    setMsg("");
                } else {
                    setMsg("Lost connection to server. Please Wait...");
                }
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
                setFetching(false);
            }
        };
        const init = async (stop_id: string) => {
            try {
                await getData(stop_id);
                interval = setInterval(() => getData(stop_id), 30000);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get stop data.");
                setLoading(false);
                setFetching(false);
            }
        };

        if (stop_id) {
            init(stop_id);
        }

        return () => clearInterval(interval);
    }, [stop_id]);

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

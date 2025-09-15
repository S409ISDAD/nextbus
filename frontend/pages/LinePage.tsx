import React, { useEffect, useState } from "react";
// import DepartureBoard from "../components/DepartureBoard";
// import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import DepartureBoard from "../components/DepartureBoard";
import { getClosestStopForService } from "../utils/closestStop";
import { useParams } from "react-router";
import { getCurrentPosition } from "../utils/locations";

import { getDBService } from "../utils/getService";
import type { LineResult } from "../models/Search";

const linePage: React.FC = () => {
    const { line_id } = useParams();

    const [line, setline] = useState<LineResult>();
    const [loading, setLoading] = useState(true);
    const [stopID, setStopID] = useState<string>("");

    const [msg, setMsg] = useState("");

    useEffect(() => {
        let interval: any;

        const getData = async (id: string) => {
            try {
                const line = await getDBService(id);

                if (line) {
                    console.log(line);
                    setline(line);
                    document.title = `Service ${line.line_name} | nextbus`;
                    const pos = await getCurrentPosition();
                    const closest_stop = await getClosestStopForService(
                        [pos.coords.latitude, pos.coords.longitude],
                        line.bt_service_id ? line.bt_service_id : ""
                    );
                    console.log("closest_stop", closest_stop);
                    setStopID(closest_stop);
                    setMsg("");
                    setLoading(false);
                }
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
            }
        };
        const init = async (line_id: string) => {
            try {
                await getData(line_id);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get line data.");
                setLoading(false);
            }
        };

        if (line_id) {
            init(line_id);
        }

        return () => {
            clearInterval(interval);
        };
    }, [line_id]);

    return (
        <div className="p-5 md:mx-20">
            <div className="flex flex-col items-center gap-4">
                <div className="flex flex-col items-center justify-center gap-6">
                    <div className="flex flex-col items-center justify-center gap-3">
                        <span className="text-4xl font-bold md:text-4xl text-start">
                            Service {line?.line_name}
                        </span>
                        <span className="text-xl font-semibold text-center text-neutral-300">
                            {line?.description}
                        </span>
                        {line?.vias && (
                            <span className="font-semibold text-center text-neutral-400">
                                Via {line?.vias}
                            </span>
                        )}
                        {line?.bt_service_id && (
                            <div className="flex flex-wrap items-center justify-center gap-4 gap-y-1">
                                <a
                                    className="underline text-sky-500"
                                    href={`https://bustimes.org/services/${line?.bt_service_id}`}
                                    target="_blank">
                                    View on bustimes.org
                                </a>
                            </div>
                        )}
                    </div>
                </div>
                {msg && <span className="text-red-500 ">{msg}</span>}
                {line?.outbound_description && (
                    <div className="flex flex-col items-center justify-center gap-1">
                        <span className="text-lg font-semibold">
                            Outbound: {line.outbound_description}
                        </span>
                        {line.inbound_description && (
                            <span className="text-lg font-semibold">
                                Inbound: {line.inbound_description}
                            </span>
                        )}
                    </div>
                )}
                {loading && (
                    <span className="text-neutral-300">Loading...</span>
                )}
                {stopID && (
                    <DepartureBoard
                        stop_id={stopID}
                        filter={line?.line_name}></DepartureBoard>
                )}
            </div>
        </div>
    );
};

export default linePage;

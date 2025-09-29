import React, { useEffect, useState } from "react";
// import DepartureBoard from "../components/DepartureBoard";
// import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import DepartureBoard from "../../components/DepartureBoard";
import { getClosestStopForService } from "../../utils/closestStop";
import { useParams } from "react-router";
import { getCurrentPosition } from "../../utils/locations";

import { getDBService } from "../../utils/getService";
import type { ServiceResult } from "../../models/Search";

const ServicePage: React.FC = () => {
    const { service_id } = useParams();

    const [service, setservice] = useState<ServiceResult>();
    const [loading, setLoading] = useState(true);
    const [stopID, setStopID] = useState<string>("");

    const [msg, setMsg] = useState("");

    useEffect(() => {
        let interval: any;

        const getData = async (id: string) => {
            try {
                const service = await getDBService(id);

                if (service) {
                    console.log(service);
                    setservice(service);
                    document.title = `Service ${service.line_name} | nextbus`;
                    const pos = await getCurrentPosition();
                    const closest_stop = await getClosestStopForService(
                        [pos.coords.latitude, pos.coords.longitude],
                        service.bt_service_id ? service.bt_service_id : ""
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
        const init = async (service_id: string) => {
            try {
                await getData(service_id);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get service data.");
                setLoading(false);
            }
        };

        if (service_id) {
            init(service_id);
        }

        return () => {
            clearInterval(interval);
        };
    }, [service_id]);

    return (
        <div className="p-5 md:mx-20">
            <div className="flex flex-col items-center gap-4">
                <div className="flex flex-col items-center justify-center gap-6">
                    <div className="flex flex-col items-center justify-center gap-3">
                        <span className="text-4xl font-bold md:text-4xl text-start">
                            {service?.line_name} · {service?.description}
                        </span>
                        <div className="flex flex-col items-center justify-center gap-1">
                            {service?.vias && (
                                <span className="text-xl font-semibold text-center text-neutral-400">
                                    Via {service?.vias}
                                </span>
                            )}
                            <span className="text-sm font-semibold text-center text-neutral-400">
                                Operated by{" "}
                                {service?.operator ? service?.operator : "N/A"}
                            </span>
                            {service?.bt_service_id && (
                                <div className="flex flex-wrap items-center justify-center gap-4 gap-y-1">
                                    <a
                                        className="underservice text-sky-500"
                                        href={`https://bustimes.org/services/${service?.bt_service_id}`}
                                        target="_blank">
                                        View on bustimes.org
                                    </a>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
                {msg && <span className="text-red-500 ">{msg}</span>}
                <div className="flex flex-col items-start w-full gap-3">
                    {service?.outbound_description && (
                        <div className="flex flex-col">
                            <span className="text-lg font-semibold">
                                {service.outbound_description}
                            </span>
                            <span className="text text-neutral-400">
                                timetable soon
                            </span>
                        </div>
                    )}
                    {service?.inbound_description && (
                        <div className="flex flex-col">
                            <span className="text-lg font-semibold">
                                {service.inbound_description}
                            </span>
                            <span className="text text-neutral-400">
                                timetable soon
                            </span>
                        </div>
                    )}
                </div>
                {loading && (
                    <span className="text-neutral-300">Loading...</span>
                )}
                {stopID && (
                    <DepartureBoard
                        stop_id={stopID}
                        filter={service?.line_name}></DepartureBoard>
                )}
            </div>
        </div>
    );
};

export default ServicePage;

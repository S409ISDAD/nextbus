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
import Timetable from "../../components/Timetable";

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
                    if (service.bt_service_id) {
                        const closest_stop = await getClosestStopForService(
                            [pos.coords.latitude, pos.coords.longitude],
                            service.bt_service_id ? service.bt_service_id : ""
                        );
                        console.log("closest_stop", closest_stop);
                        setStopID(closest_stop);
                    }
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
        <div className="p-2 py-5 sm:p-5 md:mx-20">
            <div className="flex flex-col items-center gap-4">
                <div className="flex flex-col items-center justify-center gap-6 p-3 sm:p-0">
                    <div className="flex flex-col items-center justify-center gap-3">
                        <span className="text-4xl font-bold text-center md:text-4xl">
                            {service?.line_name} · {service?.description}
                        </span>
                        <div className="flex flex-col items-center justify-center gap-1">
                            {service?.vias && (
                                <span className="text-xl font-semibold text-center text-text-light">
                                    Via {service?.vias}
                                </span>
                            )}
                            <span className="text-sm font-semibold text-center text-text-light">
                                Operated by{" "}
                                {service?.operators
                                    .map((op) => op.name)
                                    .join(", ")}
                            </span>
                            {service?.bt_service_id && (
                                <div className="flex flex-wrap items-center justify-center gap-4 gap-y-1">
                                    <a
                                        className="underservice text-link"
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
                        <div className="flex flex-col max-w-full">
                            <span className="mb-2 text-lg font-semibold">
                                {service.outbound_description}
                            </span>
                            <Timetable
                                service_id={service.service_id}
                                inbound={false}
                            />
                        </div>
                    )}
                    {service?.inbound_description && (
                        <div className="flex flex-col max-w-full">
                            <span className="mb-2 text-lg font-semibold">
                                {service.inbound_description}
                            </span>
                            <Timetable
                                service_id={service.service_id}
                                inbound={true}
                            />
                        </div>
                    )}
                </div>
                {service?.last_modified && (
                    <span className="w-full text-sm text-text-light text-start">
                        timetable data from{" "}
                        {new Date(service?.last_modified).toLocaleString(
                            "en-GB",
                            {
                                day: "numeric",
                                month: "long",
                                year: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                                timeZoneName: "short",
                            }
                        )}
                    </span>
                )}
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

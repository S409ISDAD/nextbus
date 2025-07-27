import React, { use, useEffect, useState } from "react";
// import DepartureBoard from "../components/DepartureBoard";
// import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import DepartureBoard from "../components/DepartureBoard";
import { getClosestStopForService } from "../utils/closestStop";
import { useParams } from "react-router";
import { getCurrentPosition } from "../utils/locations";

import getService from "../utils/getService";
import type { ServiceInfo } from "../models/ServiceInfo";

const ServicePage: React.FC = () => {
    const { service_id } = useParams();

    const [service, setService] = useState<ServiceInfo>();
    const [loading, setLoading] = useState(true);
    const [stopID, setStopID] = useState<string>("");

    const [msg, setMsg] = useState("");

    useEffect(() => {
        let interval: any;

        const getData = async (id: string) => {
            try {
                const service = await getService(id);

                if (service) {
                    setService(service);
                    document.title = `Service ${service.line_name} | nextbus`;
                    const pos = await getCurrentPosition();
                    const closest_stop = await getClosestStopForService(
                        [pos.coords.latitude, pos.coords.longitude],
                        service_id ? service_id : ""
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
            <div className="flex flex-col gap-4">
                <div className="flex flex-col items-center justify-center gap-6">
                    <div className="flex flex-col items-center justify-center gap-3">
                        <span className="text-4xl font-bold md:text-4xl text-start">
                            Service {service?.line_name}
                        </span>
                        <span className="text-xl font-semibold text-neutral-300">
                            Via: {service?.detail}
                        </span>
                        <div className="flex flex-wrap items-center justify-center gap-4 gap-y-1">
                            <a
                                className="underline text-sky-500"
                                href={`https://bustimes.org/services/${service_id}`}
                                target="_blank">
                                View on bustimes.org
                            </a>
                        </div>
                    </div>
                </div>
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

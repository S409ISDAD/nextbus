import React, { useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import type { Locality } from "../../models/Places";
import { getLocality } from "../../utils/getPlaces";

const LocalityPage: React.FC = () => {
    const navigate = useNavigate();
    const [locality, setLocality] = React.useState<Locality>();
    const [loading, setLoading] = React.useState(false);

    const { locality_id } = useParams();

    useEffect(() => {
        const getData = async () => {
            if (!locality_id) {
                return;
            }
            try {
                setLoading(true);
                const locality = await getLocality(locality_id);
                setLoading(false);
                if (locality) {
                    document.title = `${locality.name} | nextbus`;
                    setLocality(locality);
                }
            } catch (error) {
                console.log("uh oh", error);
                navigate("/404", { replace: true });
            }
        };

        getData();
    }, [locality_id]);

    return (
        <div className="flex flex-col items-center justify-center w-full p-8 pb-0">
            {loading && (
                <span className="mb-5 text-xl font-medium text-center text-gray-400">
                    Loading...
                </span>
            )}
            {!loading && locality && (
                <>
                    <span className="mb-10 text-4xl font-bold">
                        {locality.name}
                    </span>
                    <span className="text-2xl font-semibold">Services</span>
                    <div className="flex flex-col w-full gap-4">
                        <div className="flex flex-col items-center w-full mt-4">
                            {!locality ? (
                                <span className="w-full mb-5 text-sm text-center text-gray-400">
                                    No Locality found.
                                </span>
                            ) : (
                                <div className="w-full max-w-[80vw] mb-8 columns-2">
                                    {locality.services.map((service, idx) => (
                                        <div
                                            key={service.id}
                                            className="mb-2 break-inside-avoid">
                                            <div className="flex items-center gap-2 mb-0.5">
                                                <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                                <span className="text-[10px] text-neutral-600">
                                                    nextbus
                                                </span>
                                                <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                            </div>
                                            <div
                                                key={service.id}
                                                className="flex flex-col cursor-pointer"
                                                onClick={() => {
                                                    navigate(
                                                        `/buses/services/${service.id}`
                                                    );
                                                }}>
                                                <div className="flex flex-row items-stretch mb-1">
                                                    <div className="flex items-center px-3 py-1 bg-primary-700 rounded-l-2xl">
                                                        <span className="flex items-center justify-center text-xl font-bold text-center ">
                                                            {service.line_name}
                                                        </span>
                                                    </div>
                                                    <div className="flex flex-col justify-center px-3 bg-bg-light/50 rounded-r-2xl ">
                                                        <span className="font-semibold text ">
                                                            {
                                                                service.description
                                                            }
                                                        </span>
                                                    </div>
                                                </div>
                                                <span className="text-sm text-gray-400">
                                                    {service?.operators &&
                                                        service?.operators
                                                            .map(
                                                                (op) => op.name
                                                            )
                                                            .join(", ")}
                                                </span>
                                                {service.vias && (
                                                    <span className="text-sm text-gray-400">
                                                        via {service.vias}
                                                    </span>
                                                )}
                                            </div>
                                            {idx ===
                                                locality.services.length -
                                                    1 && (
                                                <div className="flex items-center gap-2 mb-0.5">
                                                    <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                                    <span className="text-[10px] text-neutral-600">
                                                        nextbus
                                                    </span>
                                                    <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                    <span className="text-2xl font-semibold">Stops</span>
                    <div className="flex flex-col w-full gap-4">
                        <div className="flex flex-col items-center w-full mt-4">
                            {!locality ? (
                                <span className="w-full mb-5 text-sm text-center text-gray-400">
                                    No Locality found.
                                </span>
                            ) : (
                                <div className="gap-4 mb-8 columns-2 sm:columns-3 md:columns-4">
                                    {locality.stops.map((stop) => (
                                        <div
                                            key={stop.atco_code}
                                            className="mb-2 cursor-pointer break-inside-avoid"
                                            onClick={() => {
                                                navigate(
                                                    `/buses/stops/${stop.atco_code}`
                                                );
                                            }}>
                                            <span className="underline text-link">
                                                {stop.common_name}{" "}
                                                {stop.indicator &&
                                                    `(${stop.indicator})`}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default LocalityPage;

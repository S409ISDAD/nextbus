import React, { useEffect, useState } from "react";
import DepartureBoard from "../../components/DepartureBoard";
import useLocalStorageState from "use-local-storage-state";
import haversine from "haversine-distance";
import { getCurrentPosition } from "../../utils/locations";
// import {
//     LocationPrompt,
//     useIsLocationGranted,
// } from "../components/LocationPrompt";
import getNearby from "../../utils/getNearby";
import { Card } from "../../components/ui/Card";
import { getClosestStops } from "../../utils/closestStop";
import type { Service } from "../../models/ServiceInfo";
import { useNavigate } from "react-router";
import UsageManager from "../../usage/UsageManager";
import type { PredictedStop } from "../../usage/usageModels";
import { USAGE_TRACKING, useLocalSetting } from "../../src/settings";
// import { faCaretRight } from "@fortawesome/free-solid-svg-icons";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

const BusPage: React.FC = () => {
    useEffect(() => {
        document.title = "bus dashboard | nextbus";
    }, []);

    const [tab, setTab] = useState<"nearby" | "fav">("fav");
    const [closestStops, setClosestStops] = useState<string[]>([]);
    const [nearbyServices, setNearbyServices] = useState<Service[]>([]);
    const [status, setStatus] = useState<string>("Getting location...");
    const [usageToggle] = useLocalSetting("usageToggle", true);

    const [favStops, setFavStops] = useLocalStorageState<
        Record<string, [number, number]>
    >("favStops", {
        defaultValue: {},
    });
    const [userCoords, setUserCoords] = useState<[number, number] | null>(null);
    const usageManager = UsageManager.getInstance();
    const [predictedStops, setPredictedStops] = useState<PredictedStop[]>([]);

    const navigate = useNavigate();
    // const isGranted = useIsLocationGranted();

    useEffect(() => {
        const getUserCoords = async () => {
            // if (!isGranted) return;
            let userCoords: GeolocationPosition | null = null;
            try {
                userCoords = await getCurrentPosition();
                setUserCoords([
                    userCoords.coords.latitude,
                    userCoords.coords.longitude,
                ]);
                setStatus("Getting closest stop...");

                const closestStops = await getClosestStops(
                    [userCoords.coords.latitude, userCoords.coords.longitude],
                    "",
                    1
                );
                setStatus("");
                const stopIDs = closestStops
                    .filter((stop) => stop.active_now)
                    .map((stop) => stop.stop_id);
                setClosestStops(stopIDs);

                const services = await getNearby([
                    userCoords.coords.latitude,
                    userCoords.coords.longitude,
                ]);
                if (services) {
                    setNearbyServices(services);
                }
            } catch (e) {
                setStatus(
                    "Unable to get location. Make sure location services are enabled."
                );
            }

            const stops = userCoords
                ? (await usageManager).predictStopAndRoutes(
                      userCoords.coords.latitude,
                      userCoords.coords.longitude
                  )
                : (await usageManager).predictStopAndRoutes();

            setPredictedStops(await stops);
        };
        getUserCoords();
    }, []);

    return (
        <div className="flex flex-col items-center justify-center gap-3 p-4">
            <div className="flex flex-row justify-center gap-4 mb-4">
                <button
                    className={`px-4 py-2 text-lg font-semibold rounded-xl transition-all duration-150 cursor-pointer ${
                        tab === "fav"
                            ? " bg-neutral-800 text-primary-400 scale-105"
                            : " bg-neutral-900 text-neutral-400 hover:text-primary-300"
                    }`}
                    onClick={() => setTab("fav")}
                    aria-selected={tab === "fav"}>
                    Favourites
                </button>
                <button
                    className={`px-4 py-2 text-lg font-semibold rounded-xl transition-all duration-150 cursor-pointer ${
                        tab === "nearby"
                            ? " bg-neutral-800 text-primary-400 scale-105"
                            : " bg-neutral-900 text-neutral-400 hover:text-primary-300"
                    }`}
                    onClick={() => setTab("nearby")}
                    aria-selected={tab === "nearby"}>
                    Nearby
                </button>
            </div>
            <div
                style={{ display: tab === "nearby" ? "flex" : "none" }}
                className="flex flex-col items-center justify-center max-w-full gap-10 md:flex-row">
                <div className="flex flex-col items-center justify-center gap-2">
                    <span className="text-2xl font-bold">Nearby Services</span>
                    <div className="flex flex-col flex-wrap items-center max-w-full gap-2 ">
                        {nearbyServices.length === 0 && (
                            <span className="text-sm text-neutral-400">
                                {status != "" ? (
                                    status
                                ) : (
                                    <>
                                        No services found nearby. <br></br>Make
                                        sure location services are enabled.
                                    </>
                                )}
                            </span>
                        )}
                        {nearbyServices.map((service) => (
                            <div
                                className="flex flex-row items-stretch mb-1 cursor-pointer"
                                key={service.id}
                                onClick={() => {
                                    navigate(`/buses/services/${service.id}`);
                                }}>
                                <div className="flex items-center px-3 py-1 bg-primary-700 rounded-l-2xl">
                                    <span className="flex items-center justify-center text-lg font-bold text-center">
                                        {service.line_name}
                                    </span>
                                </div>
                                <div className="flex flex-col justify-center px-3 bg-neutral-800/50 rounded-r-2xl">
                                    <span className="font-semibold text">
                                        {service.description}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="flex flex-col items-center justify-center gap-2">
                    <span className="text-2xl font-bold">Closest Stop</span>
                    <div className="flex flex-row flex-wrap items-center justify-center gap-3">
                        {closestStops.length > 0 ? (
                            closestStops.map((stopId) => (
                                <DepartureBoard
                                    key={stopId}
                                    stop_id={stopId}></DepartureBoard>
                            ))
                        ) : (
                            <span className="p-3 text-center text-neutral-400">
                                {status != "" ? (
                                    status
                                ) : (
                                    <>
                                        No stops found nearby. <br></br>Make
                                        sure location services are enabled.
                                    </>
                                )}
                            </span>
                        )}
                    </div>
                </div>
            </div>
            <div
                style={{ display: tab === "fav" ? "flex" : "none" }}
                className="flex flex-col items-center justify-center gap-10">
                {USAGE_TRACKING && (
                    <div className="flex flex-col items-center justify-center gap-3">
                        <span className="text-2xl font-bold">Smart Stops</span>
                        {usageToggle ? (
                            <>
                                <span className="text-sm text-center text-neutral-400 max-w-110">
                                    predicts the stop and bus route that you
                                    might take based on your previous activity,
                                    time of day, weekday, and location. It gets
                                    better the more you use nextbus.{" "}
                                    <a
                                        href="/buses/predictions"
                                        className="text-sm underline text-link-400">
                                        more info
                                    </a>
                                </span>
                                <div className="flex flex-row flex-wrap items-center justify-center gap-3">
                                    {Object.keys(predictedStops).length > 0 ? (
                                        predictedStops.map((predictedStop) => (
                                            <Card
                                                key={predictedStop.stopId}
                                                className="flex flex-col items-center justify-center">
                                                <div
                                                    className="mb-4 text-xl font-bold cursor-pointer"
                                                    onClick={() =>
                                                        navigate(
                                                            `/buses/stops/${predictedStop.stopId}`
                                                        )
                                                    }>
                                                    {predictedStop.stopName}
                                                </div>
                                                <div className="flex flex-row flex-wrap gap-2">
                                                    {predictedStop.topRoutes.map(
                                                        (route) => (
                                                            <div
                                                                key={
                                                                    route.lineName
                                                                }
                                                                className="flex flex-row items-stretch justify-center cursor-pointer"
                                                                onClick={() =>
                                                                    navigate(
                                                                        `/buses/stops/${predictedStop.stopId}?filter=${route.lineName}`
                                                                    )
                                                                }>
                                                                <div className="flex items-center px-3 py-1 bg-primary-700 rounded-l-2xl">
                                                                    <span className="flex items-center justify-center text-lg font-bold text-center">
                                                                        {
                                                                            route.lineName
                                                                        }
                                                                    </span>
                                                                </div>
                                                                <div className="flex flex-col justify-center px-3 bg-neutral-800/50 rounded-r-2xl">
                                                                    <span className="font-semibold text">
                                                                        {route.destination.includes(
                                                                            "-"
                                                                        )
                                                                            ? ""
                                                                            : "to "}
                                                                        {
                                                                            route.destination
                                                                        }
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        )
                                                    )}
                                                </div>
                                            </Card>
                                        ))
                                    ) : (
                                        <Card>
                                            <span className="text-center text-neutral-300">
                                                No predicted stops. <br></br>{" "}
                                                Try using nextbus for a few more
                                                days in this area to improve
                                                predictions.
                                            </span>
                                        </Card>
                                    )}
                                </div>
                                {/* <span className="text-sm text-neutral-400">
                        wrong?{" "}
                        <a
                            href="/buses/predictions"
                            className="text-sm underline text-link-400">
                            edit your predictions{" "}
                            <FontAwesomeIcon icon={faCaretRight} />
                        </a>
                    </span> */}
                            </>
                        ) : (
                            <span className="text-sm text-center text-neutral-400 max-w-110">
                                usage tracking is off.{" "}
                                <a
                                    href="/buses/predictions"
                                    className="text-sm underline text-link-400">
                                    turn it on here
                                </a>
                            </span>
                        )}
                    </div>
                )}

                <div className="flex flex-col items-center justify-center gap-3">
                    <span className="text-2xl font-bold">Favorite Stops</span>
                    <div className="flex flex-row flex-wrap items-center justify-center gap-3">
                        {Object.keys(favStops).length > 0 ? (
                            Object.entries(favStops)
                                .sort((a, b) => {
                                    if (!userCoords) return 0;
                                    return (
                                        haversine(userCoords, a[1]) -
                                        haversine(userCoords, b[1])
                                    );
                                })
                                .map(([stopId, _]) => (
                                    <DepartureBoard
                                        key={stopId}
                                        stop_id={stopId}></DepartureBoard>
                                ))
                        ) : (
                            <span className="text-center text-neutral-400">
                                No favorite stops added yet. <br></br>To add a
                                stop, click the star icon on a stop page
                            </span>
                        )}
                    </div>
                    <button
                        className="p-1.5 px-4 text-sm font-semibold text-white transition-all bg-primary cursor-pointer rounded-xl hover:bg-primary-700"
                        onClick={() => setFavStops({})}>
                        Clear Favorites
                    </button>
                </div>
            </div>
        </div>
    );
};

export default BusPage;

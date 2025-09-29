import React, { useEffect, useState } from "react";
import DepartureBoard from "../../components/DepartureBoard";
import useLocalStorageState from "use-local-storage-state";
import haversine from "haversine-distance";
import { getCurrentPosition } from "../../utils/locations";
// import {
//     LocationPrompt,
//     useIsLocationGranted,
// } from "../components/LocationPrompt";
import { Card } from "../../components/ui/Card";
import { getClosestStops } from "../../utils/closestStop";

const BusPage: React.FC = () => {
    useEffect(() => {
        document.title = "bus dashboard | nextbus";
    }, []);

    const [tab, setTab] = useState<"nearby" | "fav">("nearby");
    const [closestStops, setClosestStops] = useState<string[]>([]);
    const [status, setStatus] = useState<string>("Getting location...");

    const [favStops, setFavStops] = useLocalStorageState<
        Record<string, [number, number]>
    >("favStops", {
        defaultValue: {},
    });
    const [userCoords, setUserCoords] = useState<[number, number] | null>(null);
    // const isGranted = useIsLocationGranted();

    useEffect(() => {
        const getUserCoords = async () => {
            // if (!isGranted) return;
            const userCoords = await getCurrentPosition();
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
        };
        getUserCoords();
    }, []);

    return (
        <div className="flex flex-col items-center justify-center gap-3 p-4">
            <div className="flex flex-row justify-center gap-4 mb-4">
                <button
                    className={`px-4 py-2 text-lg font-semibold rounded-xl transition-all duration-150 cursor-pointer ${
                        tab === "nearby"
                            ? " bg-neutral-800 text-blue-400 scale-105"
                            : " bg-neutral-900 text-neutral-400 hover:text-blue-300"
                    }`}
                    onClick={() => setTab("nearby")}
                    aria-selected={tab === "nearby"}>
                    Nearby
                </button>
                <button
                    className={`px-4 py-2 text-lg font-semibold rounded-xl transition-all duration-150 cursor-pointer ${
                        tab === "fav"
                            ? " bg-neutral-800 text-blue-400 scale-105"
                            : " bg-neutral-900 text-neutral-400 hover:text-blue-300"
                    }`}
                    onClick={() => setTab("fav")}
                    aria-selected={tab === "fav"}>
                    Favourites
                </button>
            </div>
            <div style={{ display: tab === "nearby" ? "flex" : "none" }}>
                <Card className="flex flex-col items-center justify-center gap-2 p-2 rounded-[32px] bg-neutral-900">
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
                </Card>
            </div>
            <div style={{ display: tab === "fav" ? "flex" : "none" }}>
                <Card className="flex flex-col items-center justify-center gap-2 p-2 rounded-[32px] bg-neutral-900">
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
                        className="p-1.5 px-4 text-sm font-semibold text-white transition-all bg-blue-600 cursor-pointer rounded-xl hover:bg-blue-700"
                        onClick={() => setFavStops({})}>
                        Clear Favorites
                    </button>
                </Card>
            </div>
        </div>
    );
};

export default BusPage;

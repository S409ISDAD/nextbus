import React, { useEffect, useState } from "react";
import DepartureBoard from "../components/DepartureBoard";
import useLocalStorageState from "use-local-storage-state";
import haversine from "haversine-distance";
import { getCurrentPosition } from "../utils/locations";
// import {
//     LocationPrompt,
//     useIsLocationGranted,
// } from "../components/LocationPrompt";
import { Card } from "../components/ui/Card";

const BusPage: React.FC = () => {
    useEffect(() => {
        document.title = "bus dashboard | nextbus";
    }, []);

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
        };
        getUserCoords();
    }, []);

    return (
        <div className="flex flex-row flex-wrap items-center justify-center gap-3 p-4">
            <Card className="flex flex-col items-center justify-center gap-2 p-2 rounded-[32px] bg-neutral-900">
                <span className="text-2xl font-bold">Closest Stop</span>
                {/* <LocationPrompt className="p-3 w-80">
                    <DepartureBoard stop_id="" closest={true}></DepartureBoard>
                </LocationPrompt> */}
                <DepartureBoard stop_id="" closest={true}></DepartureBoard>
            </Card>
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
                            No favorite stops added yet. <br></br>To add a stop,
                            click the star icon on a stop page
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
    );
};

export default BusPage;

import React, { useEffect, useState } from "react";
import DepartureBoard from "../components/DepartureBoard";
import useLocalStorageState from "use-local-storage-state";
import haversine from "haversine-distance";
import { getCurrentPosition } from "../utils/locations";

const BusPage: React.FC = () => {
    useEffect(() => {
        document.title = "Bus Page";
    }, []);

    const [favStops, setFavStops] = useLocalStorageState<
        Record<string, [number, number]>
    >("favStops", {
        defaultValue: {},
    });
    const [userCoords, setUserCoords] = useState<[number, number] | null>(null);

    useEffect(() => {
        const getUserCoords = async () => {
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
            <div className="flex flex-col items-center justify-center gap-2 p-2 rounded-[32px] bg-neutral-900">
                <span className="text-2xl font-bold">Closest Stop</span>
                <DepartureBoard stop_id="" closest={true}></DepartureBoard>
            </div>
            <div className="flex flex-col items-center justify-center gap-2 p-2 rounded-[32px] bg-neutral-900">
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
            </div>
        </div>
    );
};

export default BusPage;

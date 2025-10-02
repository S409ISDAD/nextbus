import React, { useEffect, useState } from "react";
// import DepartureBoard from "../components/DepartureBoard";
// import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Card } from "../components/ui/Card";
import { getCurrentPosition } from "../utils/locations";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faBus,
    faCaretRight,
    faMap,
    // faRotateRight,
    faTrainSubway,
    faWarning,
} from "@fortawesome/free-solid-svg-icons";
import { getClosestStops } from "../utils/closestStop";
import { useNavigate } from "react-router";
import SearchBar from "../components/SearchBar";
// import {
//     LocationPrompt,
//     useIsLocationGranted,
// } from "../components/LocationPrompt";
import { useGeolocated } from "react-geolocated";
import type { DBStats } from "../models/Stats.ts";
import { getDBStats } from "../utils/getStats.ts";
// import type { Locality } from "../models/Locality.ts";
// import { getDestinations } from "../utils/JourneyPlanning.ts";

const Home: React.FC = () => {
    // const navigate = useNavigate();

    const [closestStop, setClosestStop] = React.useState<string | null>(null);
    const [showStop, setShowStop] = React.useState(false);
    const [stats, setStats] = useState<DBStats>();
    // const [destinations, setDestinations] = useState<Locality[]>([]);
    // const [loadingDestinations, setLoadingDestinations] = useState(false);
    const {
        coords,
        // isGeolocationAvailable,
        // isGeolocationEnabled,
        // getPosition,
    } = useGeolocated({
        positionOptions: {
            enableHighAccuracy: false,
        },
        suppressLocationOnMount: true,
        userDecisionTimeout: 5000,
    });

    const [showCaution, setShowCaution] = useState(false);

    const navigate = useNavigate();

    useEffect(() => {
        document.title = "nextbus";
    }, []);

    // const fetchLocalities = async () => {
    //     try {
    //         // console.log(isGeolocationAvailable, isGeolocationEnabled);
    //         // if (!isGeolocationAvailable || !isGeolocationEnabled) return;
    //         setLoadingDestinations(true);

    //         const pos = await getCurrentPosition();

    //         const destinations = await getDestinations(
    //             [pos.coords.latitude, pos.coords.longitude],
    //             undefined
    //         );
    //         if (destinations) {
    //             console.log("destinations", destinations);
    //             setDestinations(destinations);
    //         }
    //     } catch (error) {
    //         console.log("uh oh", error);
    //     } finally {
    //         setLoadingDestinations(false);
    //     }
    // };

    useEffect(() => {
        const getClosest = async () => {
            try {
                // console.log(isGeolocationAvailable, isGeolocationEnabled);
                // if (!isGeolocationAvailable || !isGeolocationEnabled) return;

                const pos = await getCurrentPosition();

                const closestStops = await getClosestStops([
                    pos.coords.latitude,
                    pos.coords.longitude,
                ]);
                // const closestStop = await getClosestStop(fakeCoords);
                if (closestStops) {
                    const closestStop = closestStops[0];
                    console.log(
                        "closest stop",
                        closestStop,
                        "distance",
                        closestStop.dist
                    );
                    if (closestStop.dist < 10 && closestStop.stop_id) {
                        // 10 meters
                        console.log("stop is close enough, showing popup");
                        setClosestStop(closestStop.stop_id);
                        setShowStop(true);
                    }
                }
            } catch (error) {
                console.log("uh oh", error);
            }
        };
        const fetchStats = async () => {
            try {
                const stats = await getDBStats();
                if (stats) {
                    setStats(stats.dbStats);
                }
            } catch {
                console.log("uh oh");
            }
        };

        getClosest();
        // fetchLocalities();
        fetchStats();
    }, [coords]);

    return (
        <div>
            <div className="flex flex-col items-center justify-center gap-6">
                <div className="flex flex-col items-center justify-center w-full gap-5 pt-0 py-7">
                    <div className="flex flex-col items-center justify-center p-2">
                        <div className="flex flex-col items-center w-full">
                            <button
                                className="flex flex-row items-center justify-center gap-1 p-2 px-4 transition cursor-pointer border-1 rounded-2xl bg-neutral-800 border-amber-500 hover:border-amber-400"
                                onClick={() => setShowCaution((prev) => !prev)}>
                                <FontAwesomeIcon icon={faWarning} />
                                <span className="ml-2 text-sm">
                                    {showCaution
                                        ? "Hide notice"
                                        : "Show notice"}
                                </span>
                            </button>
                            {showCaution && (
                                <div className="w-full max-w-xl px-4 py-2 mt-2 rounded-2xl bg-amber-500">
                                    <span className="text-center text text-neutral-950">
                                        This is a work in progress. There may be
                                        some bugs and issues, and the
                                        information given is not guaranteed to
                                        be true.{" "}
                                        <a
                                            href="https://discord.gg/dyEmZSkwge"
                                            className="text-red-800 underline h-fit"
                                            target="_blank"
                                            rel="noopener noreferrer">
                                            Join the Discord
                                        </a>{" "}
                                        if you would like to suggest or report
                                        anything.
                                    </span>
                                </div>
                            )}
                        </div>
                        <div className="flex flex-row items-center gap-1 spooky-font">
                            {/* TODO: remember to go down a size when changing back to normal font */}
                            <span className="text-6xl font-black text-center pt-7">
                                nextbus
                            </span>
                            <span className="text-2xl font-bold h-fit text-link">
                                beta
                            </span>
                        </div>
                    </div>

                    {showStop && closestStop && (
                        <div className="flex flex-col items-center gap-2 p-3 bg-neutral-800 rounded-[24px]">
                            <span className="px-5 font-semibold text-center text-neutral-300 text">
                                It looks like you're at a bus stop!
                                <br /> Would you like to see the departures?
                            </span>
                            <div className="flex flex-row w-full gap-2">
                                <button
                                    className="w-full p-2 mt-2 font-semibold text-white transition-all cursor-pointer bg-neutral-600 rounded-xl hover:bg-neutral-700"
                                    onClick={() => {
                                        setShowStop(false);
                                    }}>
                                    No, thanks.
                                </button>
                                <button
                                    className="w-full p-2 mt-2 font-semibold text-white transition-all cursor-pointer bg-primary text-nowrap rounded-xl hover:bg-primary-700"
                                    onClick={() => {
                                        setShowStop(false);
                                        navigate("/buses/stops/${closestStop}");
                                    }}>
                                    Yes, show me!{" "}
                                </button>
                            </div>
                        </div>
                    )}
                    <div className="flex flex-wrap items-center justify-center w-full gap-4">
                        <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                            <span className="text-xl font-bold text-link-400">
                                {stats?.lines?.toLocaleString() ?? "--"}
                            </span>
                            <span className="mt-1 text-sm text-neutral-400">
                                Services
                            </span>
                        </div>
                        <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                            <span className="text-xl font-bold text-purple-400">
                                {stats?.stops?.toLocaleString() ?? "--"}
                            </span>
                            <span className="mt-1 text-sm text-neutral-400">
                                Stops
                            </span>
                        </div>
                        <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                            <span className="text-xl font-bold text-emerald-400">
                                {stats?.operators?.toLocaleString() ?? "--"}
                            </span>
                            <span className="mt-1 text-sm text-neutral-400">
                                Operators
                            </span>
                        </div>
                    </div>
                    <a
                        href="/stats"
                        className="text-sm underline text-link-400">
                        See more stats <FontAwesomeIcon icon={faCaretRight} />
                    </a>

                    <SearchBar />

                    <div className="flex flex-row flex-wrap items-start justify-center w-full gap-5 p-5">
                        <Card className="max-w-[90vw] flex flex-col items-center gap-2">
                            <div className="flex flex-col items-center justify-center">
                                <span className="text-xl font-bold text-center">
                                    Quick Links
                                </span>
                            </div>
                            <div className="flex flex-row flex-wrap items-center justify-center gap-2">
                                <button
                                    className="button max-w-fit"
                                    onClick={() => {
                                        navigate("/buses");
                                    }}>
                                    Buses <FontAwesomeIcon icon={faBus} />
                                </button>
                                <button
                                    className="button max-w-fit"
                                    onClick={() => {
                                        navigate("/map");
                                    }}>
                                    Map <FontAwesomeIcon icon={faMap} />
                                </button>
                                <button
                                    className="button max-w-fit"
                                    onClick={() => {
                                        navigate("/trains");
                                    }}>
                                    Trains{" "}
                                    <FontAwesomeIcon icon={faTrainSubway} />
                                </button>
                            </div>
                        </Card>

                        {/* <Card className="max-w-[90vw] flex flex-col items-center gap-2">
                            <div className="flex flex-row items-center justify-center gap-3">
                                <div className="flex flex-col items-center justify-center gap-1">
                                    <div className="flex flex-row items-center justify-center gap-1">
                                        <span className="text-xl font-bold text-center text-nowrap">
                                            Where to?
                                        </span>
                                        <button
                                            className="w-8 h-8 p-1 rounded-2xl bg-primary"
                                            onClick={async () => {
                                                await fetchLocalities();
                                            }}>
                                            <FontAwesomeIcon
                                                icon={faRotateRight}
                                                className="text-xs"
                                            />
                                        </button>
                                    </div>
                                    <span className="text-sm font-semibold text-center text-neutral-500">
                                        finds possible destinations based on
                                        buses you could take right now (work in
                                        progress)
                                    </span>
                                </div>
                            </div>
                            <div className="w-full max-w-[400px]">
                                <div className="flex flex-row flex-wrap items-center justify-center gap-2 whitespace-nowrap">
                                    {loadingDestinations && (
                                        <span className="text-sm text-neutral-400">
                                            loading...
                                        </span>
                                    )}
                                    {destinations.length === 0 &&
                                        !loadingDestinations && (
                                            <span className="text-sm text-neutral-400">
                                                No possible destinations found.
                                            </span>
                                        )}
                                    {destinations.map((dest) => (
                                        <a
                                            key={dest.id}
                                            className="flex items-center justify-center px-3 py-1 text-lg font-bold text-center cursor-pointer rounded-xl bg-neutral-800/50"
                                            href={`/buses/journeysearch/${dest.id}`}>
                                            {dest.name}
                                        </a>
                                    ))}
                                </div>
                            </div>
                        </Card> */}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;

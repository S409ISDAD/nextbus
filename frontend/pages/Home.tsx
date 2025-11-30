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
import { Switch } from "@headlessui/react";
// import {
//     LocationPrompt,
//     useIsLocationGranted,
// } from "../components/LocationPrompt";
import { useGeolocated } from "react-geolocated";
import type { Stats } from "../models/Stats.ts";
import getStats from "../utils/getStats.ts";
import { faDiscord } from "@fortawesome/free-brands-svg-icons";
import { useLocalSetting } from "../src/settings.ts";
// import type { Locality } from "../models/Locality.ts";
// import { getDestinations } from "../utils/JourneyPlanning.ts";

const Home: React.FC = () => {
    // const navigate = useNavigate();

    const [closestStop, setClosestStop] = React.useState<string | null>(null);
    const [showStop, setShowStop] = React.useState(false);
    const [stats, setStats] = useState<Stats>();
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
    const [vegMode, setVegMode] = useLocalSetting("veg", false);

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
                const stats = await getStats();
                if (stats) {
                    setStats(stats);
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
            <div className="flex flex-col items-center justify-center">
                <div className="flex flex-col items-center justify-center w-full gap-6 pt-0 py-7">
                    <div className="flex flex-col items-center justify-center p-2 pb-0">
                        <div className="flex flex-col items-center w-full">
                            <button
                                className="flex flex-row items-center justify-center gap-1 p-2 px-4 transition border cursor-pointer rounded-2xl bg-neutral-800 border-amber-500 hover:border-amber-400"
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
                        <div className="flex flex-col items-center gap-3">
                            <div className="flex flex-row items-center gap-1">
                                <h1 className="text-5xl font-black text-center sm:text-6xl pt-7">
                                    nextbus
                                </h1>
                                <h3 className="text-xl font-bold h-fit text-link">
                                    beta
                                </h3>
                            </div>
                            <h2 className="text-2xl font-bold text-center sm:text-4xl">
                                track your bus and{" "}
                                <span className="underline text-link">
                                    skip the guesswork
                                </span>
                            </h2>
                            {showStop && closestStop ? (
                                <div className="flex flex-col items-center gap-2 p-3 bg-neutral-800 rounded-3xl">
                                    <p className="px-5 font-semibold text-center text-neutral-300 text">
                                        It looks like you're at a bus stop!
                                        <br /> Would you like to see the
                                        departures?
                                    </p>
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
                                                navigate(
                                                    `/buses/stops/${closestStop}`
                                                );
                                            }}>
                                            Yes, show me!{" "}
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <p className="max-w-lg m-2 text-center text-neutral-400">
                                    real-time bus tracking across the UK, with
                                    smart predictions to make taking the bus
                                    easier, faster, and more reliable.
                                </p>
                            )}
                        </div>
                    </div>

                    <SearchBar />
                    <div className="flex flex-row w-[90vw] lg:w-[40%] md:w-[50%] items-center justify-center gap-2">
                        <button
                            className="button text-nowrap"
                            onClick={() => {
                                navigate("/buses");
                            }}>
                            Buses <FontAwesomeIcon icon={faBus} />
                        </button>
                        <button
                            className="button text-nowrap"
                            onClick={() => {
                                navigate("/map");
                            }}>
                            Map <FontAwesomeIcon icon={faMap} />
                        </button>
                        <button
                            className="button text-nowrap"
                            onClick={() => {
                                navigate("/trains");
                            }}>
                            Trains <FontAwesomeIcon icon={faTrainSubway} />
                        </button>
                    </div>

                    <a
                        href="/tutorials/install"
                        className="underline text-link-400">
                        Want nextbus as an app?{" "}
                        <FontAwesomeIcon icon={faCaretRight} />
                    </a>
                    {/* <div className="flex flex-row flex-wrap items-start justify-center w-full gap-5">
                        <Card className="max-w-[90vw] flex flex-col items-center gap-2">
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
                        </Card>
                    </div> */}
                    <div className="flex flex-col items-center justify-center gap-2">
                        <div className="flex flex-wrap items-center justify-center w-full gap-4">
                            <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                                <h2 className="text-xl font-bold text-link-400">
                                    {stats?.total_buses?.toLocaleString() ??
                                        "--"}
                                </h2>
                                <p className="mt-1 text-sm text-neutral-400">
                                    Buses Tracked
                                </p>
                            </div>
                            <div className="flex flex-col items-center p-2 px-6 shadow bg-neutral-800/50 rounded-xl">
                                <h2 className="text-xl font-bold text-purple-400">
                                    {stats?.total_stops?.toLocaleString() ??
                                        "--"}
                                </h2>
                                <p className="mt-1 text-sm text-neutral-400">
                                    Stops Viewed
                                </p>
                            </div>
                        </div>
                        <a
                            href="/stats"
                            className="text-sm underline text-link-400">
                            See more stats{" "}
                            <FontAwesomeIcon icon={faCaretRight} />
                        </a>
                    </div>

                    <Card className="max-w-[90vw] flex flex-col items-center gap-2">
                        <div className="flex flex-col items-center justify-center">
                            <h2 className="text-xl font-bold text-center">
                                Get Involved
                            </h2>
                        </div>

                        <p className="mb-2 text-sm text-center text-neutral-400">
                            Join our Discord to give feedback, report issues,
                            and suggest features!
                        </p>

                        <button
                            className="button max-w-fit"
                            onClick={() => {
                                window.open(
                                    "https://discord.gg/dyEmZSkwge",
                                    "_blank"
                                );
                            }}>
                            Join the Discord!{" "}
                            <FontAwesomeIcon icon={faDiscord} />
                        </button>
                    </Card>
                    <Card className="max-w-[90vw] flex flex-col items-center gap-2">
                        <div className="flex flex-col items-center justify-center">
                            <h2 className="text-xl font-bold text-center">
                                Settings
                            </h2>
                        </div>
                        <div className="flex flex-row items-center justify-center gap-2">
                            <p className="text-center text-neutral-400">
                                enthusiast mode
                            </p>

                            <Switch
                                checked={vegMode}
                                onChange={setVegMode}
                                className="relative flex p-1 ease-in-out rounded-full cursor-pointer group h-7 w-14 bg-white/10 focus:not-data-focus:outline-none data-checked:bg-primary data-focus:outline data-focus:outline-white">
                                <span
                                    aria-hidden="true"
                                    className="inline-block transition duration-200 ease-in-out translate-x-0 bg-white rounded-full shadow-lg pointer-events-none size-5 ring-0 group-data-checked:translate-x-7"
                                />
                            </Switch>
                        </div>
                        <p className="text-xs text-center text-neutral-400">
                            (for bus enthusiasts, shows bus details like reg,
                            fleet number, and vehicle type)
                        </p>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default Home;

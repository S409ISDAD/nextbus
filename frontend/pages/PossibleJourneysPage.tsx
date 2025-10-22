import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { Skeleton } from "@radix-ui/themes";
import { Card } from "../components/ui/Card";
import { lateness, timedeltaDisplay, toTime } from "../utils/timeUtils";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faArrowLeft,
    faBus,
    faHourglassStart,
    faPersonWalkingArrowRight,
    faStopwatch,
} from "@fortawesome/free-solid-svg-icons";
import type { Locality } from "../models/Locality.ts";
import type { PossibleJourney } from "../models/PossibleJourneys.ts";
import { getLocality, getPossibleJourneys } from "../utils/JourneyPlanning.ts";
import { getCurrentPosition } from "../utils/locations.ts";

function JourneyCard({
    journey,
    onClick,
    idx,
}: {
    journey: PossibleJourney;
    onClick: () => void;
    idx: number;
}) {
    return (
        <div
            key={journey.journey_id}
            onClick={onClick}
            className="cursor-pointer">
            <div className="flex items-center justify-between font-semibold">
                {/* LEFT BLOCK */}
                <div className="flex flex-col gap-3">
                    <div className="flex flex-col items-start gap-4">
                        <div className="flex flex-col items-start gap-2 justify-between w-full">
                            <div className="flex mb-1">
                                <div className="flex items-center px-3 py-1 bg-primary-700 rounded-l-2xl">
                                    <span className="flex items-center justify-center text-xl font-bold text-center">
                                        {journey.line_name}
                                    </span>
                                </div>
                                <div className="flex flex-col justify-center px-3 bg-bg-light/50 rounded-r-2xl">
                                    <span className="font-semibold text">
                                        {journey.headsign}
                                    </span>
                                    {journey.live_bus && (
                                        <span className="mb-0.5 text-xs text-text-light">
                                            {journey.live_bus.bus_type}
                                        </span>
                                    )}
                                </div>
                                {idx === 0 && (
                                    <span className="px-2 py-1 align-self-center h-fit ml-2 text-xs font-bold text-primary-400 rounded-full bg-primary/20">
                                        arrives first
                                    </span>
                                )}
                            </div>
                            {journey.live_bus && (
                                <div className="flex items-center gap-3">
                                    <div className="flex justify-center px-2 py-1 rounded-lg bg-amber-400">
                                        <span className="text-xs font-bold align-middle text-bg-main text-nowrap">
                                            {journey.live_bus.reg}
                                        </span>
                                    </div>
                                    <span
                                        className={`text-${
                                            journey.live_bus.delay >= 60
                                                ? "red"
                                                : "green"
                                        }-400`}>
                                        {lateness(journey.live_bus.delay)}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Journey Details Timeline */}
                        <div className="relative flex flex-col gap-4">
                            {/* Origin Stop */}

                            <div className="flex items-center gap-3">
                                <div className="text-sm font-bold">
                                    {journey.origin_stop_name}
                                </div>
                                {journey.departure &&
                                    (() => {
                                        const aimed = new Date(
                                            journey.departure
                                        ).getTime();
                                        const expt = new Date(
                                            journey.live_bus?.expected ||
                                                journey.departure
                                        ).getTime();
                                        const diff = Math.abs(expt - aimed);
                                        const isLate =
                                            expt > aimed && diff > 60000;
                                        return (
                                            <div className="flex gap-2">
                                                {isLate && (
                                                    <span className="line-through text-neutral-500">
                                                        {toTime(
                                                            journey.departure
                                                        )}
                                                    </span>
                                                )}
                                                <span
                                                    className={"text-link-400"}>
                                                    {toTime(
                                                        journey.live_bus
                                                            ?.expected ||
                                                            journey.departure
                                                    )}
                                                </span>
                                            </div>
                                        );
                                    })()}
                            </div>

                            {/* Journey Steps */}
                            <div className="flex flex-col gap-2 text-sm text-text-light">
                                {journey.wait_seconds && (
                                    <div className="flex items-center gap-2">
                                        <FontAwesomeIcon
                                            icon={faHourglassStart}
                                            className="text-neutral-100"
                                        />
                                        Go in{" "}
                                        {timedeltaDisplay(journey.wait_seconds)}
                                    </div>
                                )}
                                {journey.walk_seconds && (
                                    <div className="flex items-center gap-2">
                                        <FontAwesomeIcon
                                            icon={faPersonWalkingArrowRight}
                                            className="text-neutral-100"
                                        />
                                        Walk{" "}
                                        {timedeltaDisplay(journey.walk_seconds)}
                                    </div>
                                )}
                                <div className="flex items-start gap-2 flex-col">
                                    <div className="flex items-center gap-2">
                                        <FontAwesomeIcon
                                            icon={faBus}
                                            className="text-neutral-100"
                                        />
                                        Board the {journey.line_name}
                                    </div>
                                </div>
                                {journey.in_vehicle_seconds && (
                                    <div className="flex items-center gap-2">
                                        <FontAwesomeIcon
                                            icon={faStopwatch}
                                            className="text-neutral-100"
                                        />
                                        Ride for{" "}
                                        {timedeltaDisplay(
                                            journey.in_vehicle_seconds
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Destination Stop */}

                            <div className="flex items-center gap-3">
                                <div className="text-sm font-bold">
                                    {journey.dest_stop_name}
                                </div>
                                {journey.arrival &&
                                    (() => {
                                        const aimed = new Date(
                                            journey.arrival
                                        ).getTime();
                                        const expt = new Date(
                                            journey.live_bus
                                                ? journey.live_bus.delay +
                                                  journey.arrival
                                                : journey.arrival
                                        ).getTime();
                                        const diff = Math.abs(expt - aimed);
                                        const isLate =
                                            expt > aimed && diff > 60000;
                                        return (
                                            <div className="flex gap-2">
                                                {isLate && (
                                                    <span className="line-through text-neutral-500">
                                                        {toTime(
                                                            journey.arrival
                                                        )}
                                                    </span>
                                                )}
                                                <span
                                                    className={"text-link-400"}>
                                                    {toTime(
                                                        journey.live_bus
                                                            ? new Date(
                                                                  journey
                                                                      .live_bus
                                                                      .delay +
                                                                      new Date(
                                                                          journey.arrival
                                                                      ).getTime()
                                                              ).toString()
                                                            : journey.arrival
                                                    )}
                                                </span>
                                            </div>
                                        );
                                    })()}
                            </div>
                        </div>
                    </div>
                </div>

                {/* RIGHT BLOCK */}
                {/*<div className="flex flex-wrap items-center justify-center gap-2 text-sm md:gap-4 sm:text-base">*/}
                {/*    <div className="px-1.5 py-0.5 bg-primary rounded-lg">*/}
                {/*        <span className="text-xs font-bold text-bg-main whitespace-nowrap">*/}
                {/*            Platform {train.fromStop?.platform ?? "-"}*/}
                {/*        </span>*/}
                {/*    </div>*/}

                {/*    <div className="flex items-end justify-center gap-1 px-2 py-[0.2rem] w-16 sm:w-18 rounded-xl bg-bg-light/50">*/}
                {/*        <span className="text-base font-bold sm:text-lg">*/}
                {/*            {train.timeTo?.split(" ")[0] ?? "--"}*/}
                {/*        </span>*/}
                {/*        <span className="text-xs sm:text-sm font-bold mb-[0.15rem]">*/}
                {/*            {train.timeTo?.split(" ")[1]}*/}
                {/*        </span>*/}
                {/*    </div>*/}
                {/*</div>*/}
            </div>
        </div>
    );
}

const PossibleJourneysPage: React.FC = () => {
    const { locality, datetime } = useParams();

    const navigate = useNavigate();

    const [possibleJourneys, setPossibleJourneys] = useState<PossibleJourney[]>(
        []
    );
    const [destination, setDestination] = useState<Locality>();
    const [loading, setLoading] = useState(true);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            const diffSec = Math.floor(
                (now.getTime() - lastRefreshed.getTime()) / 1000
            );
            const min = Math.floor(diffSec / 60);
            const sec = diffSec % 60;

            setElapsed(min > 0 ? `${min}m ${sec}s` : `${sec}s`);

            // setPossibleJourneys((prevTrains) =>
            //     prevTrains
            //         .map((train) => {
            //             return {
            //                 ...train,
            //                 timeTo: generateTimeTo(
            //                     (() => {
            //                         const expected =
            //                             train.fromStop?.expectedDeparture ||
            //                             train.fromStop?.expectedArrival;
            //
            //                         if (!expected) return 0;
            //                         const expectedDate =
            //                             typeof expected === "string"
            //                                 ? new Date(expected)
            //                                 : expected;
            //                         return (
            //                             (expectedDate.getTime() -
            //                                 now.getTime()) /
            //                             1000
            //                         );
            //                     })()
            //                 ),
            //             };
            //         })
            //         .filter((train) => {
            //             const expected =
            //                 train.fromStop?.expectedDeparture ||
            //                 train.fromStop?.expectedArrival;
            //             if (!expected) return false;
            //             return (
            //                 new Date(new Date(expected).getTime() + 60 * 1000) >
            //                 now
            //             );
            //         })
            // );
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed]);

    useEffect(() => {
        const getData = async () => {
            if (!locality) {
                setMsg("Please enter a valid place code");
                return;
            }
            try {
                const destination = await getLocality(locality);
                if (destination) {
                    setDestination(destination);
                }
                const pos = await getCurrentPosition();
                // const fakePos = [51.0812758, -1.1592113]
                // const fakePos = [51.062069, -1.294477]
                const possible = await getPossibleJourneys(
                    [pos.coords.latitude, pos.coords.longitude],
                    locality,
                    undefined
                );
                // const possible = await getPossibleJourneys(
                //     fakePos, locality
                // );

                if (possible) {
                    if (possible.length === 0) {
                        setMsg("No journeys found.");
                        setPossibleJourneys([]);
                        setLoading(false);
                        return;
                    }
                    setPossibleJourneys(possible);
                    document.title = `buses to ${
                        destination.name ?? "Unknown"
                    } | nextbus`;
                    setRefreshed(new Date());
                    setMsg("");
                    setLoading(false);
                }
            } catch (err) {
                console.error(err);
                setMsg("Failed to fetch data.");
            }
        };

        getData();
        const interval = setInterval(() => {
            getData();
        }, 60000);
        return () => clearInterval(interval);
    }, [locality, datetime]);

    return (
        <div className="gap-3 p-5 md:mx-20">
            <div
                className="flex items-center gap-2 p-1.5 px-2.5 my-2 text-sm font-semibold text-text-dark transition-all cursor-pointer bg-bg-light w-fit rounded-xl hover:bg-primary-700"
                onClick={() => {
                    navigate(-1);
                }}>
                <FontAwesomeIcon icon={faArrowLeft} />
                Back
            </div>
            <div className="flex flex-col items-center w-full gap-4">
                <div className="flex flex-col items-center justify-center gap-3">
                    <div className="flex flex-wrap items-center justify-center text-3xl font-bold text-center">
                        Fastest buses to
                        <span className="mx-1 text-3xl font-bold">
                            {destination?.name ?? "?"}
                        </span>
                    </div>
                </div>

                <div className="flex justify-center gap-2">
                    <span className="text-xs text-text-light">
                        {loading ? "Loading..." : `Updated ${elapsed} ago`}
                    </span>
                    <span className="text-xs text-text-light">·</span>
                    <span className="text-xs text-text-light">
                        Updates every minute
                    </span>
                </div>

                <div className="flex flex-col w-full gap-1">
                    {msg ? (
                        <div className="flex justify-center gap-1 p-3">
                            <span className="text-red">{msg}</span>
                        </div>
                    ) : (
                        <></>
                    )}
                    {loading ? (
                        <>
                            {[1, 2, 3, 4, 5].map((i) => (
                                <Card key={i}>
                                    <div className="flex flex-row justify-between align-center">
                                        <div className="flex flex-col gap-1">
                                            <Skeleton>
                                                <span className="text-xl">
                                                    123 to Location
                                                </span>
                                            </Skeleton>
                                            <Skeleton>
                                                <span>10:10:10</span>
                                            </Skeleton>
                                        </div>
                                        <div className="flex flex-row gap-3">
                                            <Skeleton>
                                                <div className="p-3">
                                                    <span>AB12ACB</span>
                                                </div>
                                            </Skeleton>
                                            <Skeleton>
                                                <div className="p-3">
                                                    <span>5 min</span>
                                                </div>
                                            </Skeleton>
                                        </div>
                                    </div>
                                </Card>
                            ))}
                        </>
                    ) : (
                        <>
                            {possibleJourneys.map((journey, idx) => (
                                <>
                                    <div className="flex items-center gap-2 mb-0.5">
                                        <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                        <span className="text-[10px] text-neutral-600">
                                            nextbus
                                        </span>
                                        <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                    </div>

                                    <JourneyCard
                                        journey={journey}
                                        onClick={() => {
                                            // navigate(
                                            //     `/trains/${train.serviceUid}?from=${fromStationCode}&to=${toStationCode}`
                                            // )
                                        }}
                                        idx={idx}
                                    />
                                    {idx === possibleJourneys.length - 1 && (
                                        <div className="flex items-center gap-2 mb-0.5">
                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                            <span className="text-[10px] text-neutral-600">
                                                nextbus
                                            </span>
                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                        </div>
                                    )}
                                </>
                            ))}
                            {possibleJourneys.length === 0 && (
                                <div className="flex justify-center">
                                    <span className="text-text-light">
                                        No more trains!
                                    </span>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PossibleJourneysPage;

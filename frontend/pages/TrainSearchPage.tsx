import { useEffect, useState } from "react";
import { fetchRoute } from "../utils/getStationDepartures";
import { useNavigate, useParams } from "react-router";
import { Skeleton } from "@radix-ui/themes";
import { Card } from "../components/ui/Card";
import type { ServiceLocation, TrainService } from "../models/Trains";
import { generateTimeTo, lateness, toTime } from "../utils/timeUtils";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowLeft, faArrowRight } from "@fortawesome/free-solid-svg-icons";

function TrainCard({
    train,
    onClick,
    idx,
}: {
    train: TrainService;
    onClick: () => void;
    idx: number;
}) {
    return (
        <div
            key={train.serviceUid}
            onClick={onClick}
            className="cursor-pointer">
            <div className="flex items-center justify-between font-semibold">
                {/* LEFT BLOCK */}
                <div className="flex flex-col gap-3">
                    <div className="flex flex-wrap items-center gap-6 gap-y-1">
                        {/* FROM -> TO */}
                        <div className="flex items-center gap-3">
                            {/* FROM */}
                            <div className="text-center">
                                {train.fromStop?.expectedDeparture &&
                                train.fromStop?.scheduledDeparture ? (
                                    <div className="flex gap-1">
                                        {new Date(
                                            train.fromStop.expectedDeparture
                                        ).getTime() >
                                            new Date(
                                                train.fromStop.scheduledDeparture
                                            ).getTime() && (
                                            <span className="line-through text-neutral-500">
                                                {toTime(
                                                    train.fromStop
                                                        .scheduledDeparture
                                                )}
                                            </span>
                                        )}
                                        <span
                                            className={
                                                new Date(
                                                    train.fromStop.expectedDeparture
                                                ).getTime() >
                                                new Date(
                                                    train.fromStop.scheduledDeparture
                                                ).getTime()
                                                    ? "text-red-400"
                                                    : "text-green-400"
                                            }>
                                            {toTime(
                                                train.fromStop.expectedDeparture
                                            )}
                                        </span>
                                    </div>
                                ) : (
                                    "-"
                                )}
                                <div className="text-sm font-bold text-start">
                                    {train.fromStop?.description}
                                </div>
                            </div>

                            <FontAwesomeIcon
                                icon={faArrowRight}
                                className="text-neutral-500"
                            />

                            {/* TO */}
                            <div className="text-center">
                                {train.toStop?.expectedArrival &&
                                train.toStop?.scheduledArrival ? (
                                    <div className="flex gap-1">
                                        {new Date(
                                            train.toStop.expectedArrival
                                        ).getTime() >
                                            new Date(
                                                train.toStop.scheduledArrival
                                            ).getTime() && (
                                            <span className="line-through text-neutral-500">
                                                {toTime(
                                                    train.toStop
                                                        .scheduledArrival
                                                )}
                                            </span>
                                        )}
                                        <span
                                            className={
                                                new Date(
                                                    train.toStop.expectedArrival
                                                ).getTime() >
                                                new Date(
                                                    train.toStop.scheduledArrival
                                                ).getTime()
                                                    ? "text-red-400"
                                                    : "text-green-400"
                                            }>
                                            {toTime(
                                                train.toStop.expectedArrival
                                            )}
                                        </span>
                                    </div>
                                ) : (
                                    "-"
                                )}
                                <div className="text-sm font-bold text-start">
                                    {train.toStop?.description}
                                </div>
                            </div>
                        </div>

                        {/* DELAY & BADGES */}
                        <div className="flex flex-wrap items-center gap-3">
                            <span
                                className={`text-${
                                    (train.fromStop?.delay ?? 0) >= 60
                                        ? "red"
                                        : "green"
                                }-400`}>
                                {lateness(train.fromStop?.delay ?? 0)}
                            </span>
                            {train.duration && (
                                <span className="font-semibold text-neutral-400">
                                    {`${Math.floor(
                                        train.duration / 3600
                                    )}h ${Math.floor(
                                        (train.duration % 3600) / 60
                                    )}m`}
                                </span>
                            )}

                            {idx === 0 && (
                                <span className="px-2 py-1 text-xs font-bold text-blue-400 rounded-full bg-blue-500/20">
                                    arrives first
                                </span>
                            )}
                            {train.fastest && (
                                <span className="px-2 py-1 text-xs font-bold text-blue-400 rounded-full bg-blue-500/20">
                                    fastest
                                </span>
                            )}
                        </div>
                    </div>

                    {/* DESTINATION & OPERATOR */}
                    <div className="flex flex-row items-center gap-3 text-sm">
                        <div className="flex mb-1">
                            <div className="flex items-center gap-1 px-3 py-1 font-semibold bg-neutral-800/50 rounded-l-2xl">
                                <span>to</span>
                                {train.destination.map((d, i) => (
                                    <span key={d.description}>
                                        {d.description}
                                        {i < train.destination.length - 2
                                            ? ", "
                                            : ""}
                                        {i === train.destination.length - 2
                                            ? " and "
                                            : ""}
                                    </span>
                                ))}
                            </div>
                            <div
                                className="px-3 py-1 font-semibold rounded-r-2xl"
                                style={{ backgroundColor: train.atocColor }}>
                                {train.atocCode}
                            </div>
                        </div>
                    </div>
                </div>

                {/* RIGHT BLOCK */}
                <div className="flex flex-wrap items-center justify-center gap-2 text-sm md:gap-4 sm:text-base">
                    <div className="px-1.5 py-0.5 bg-blue-500 rounded-lg">
                        <span className="text-xs font-bold text-neutral-950 whitespace-nowrap">
                            Platform {train.fromStop?.platform ?? "-"}
                        </span>
                    </div>

                    <div className="flex items-end justify-center gap-1 px-2 py-[0.2rem] w-16 sm:w-18 rounded-xl bg-neutral-800/50">
                        <span className="text-base font-bold sm:text-lg">
                            {train.timeTo?.split(" ")[0] ?? "--"}
                        </span>
                        <span className="text-xs sm:text-sm font-bold mb-[0.15rem]">
                            {train.timeTo?.split(" ")[1]}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

const TrainSearchPage: React.FC = () => {
    const { fromStationCode, toStationCode } = useParams();

    const navigate = useNavigate();

    const [trains, setTrains] = useState<TrainService[]>([]);
    const [stationTo, setStationTo] = useState<ServiceLocation>();
    const [stationFrom, setStationFrom] = useState<ServiceLocation>();
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

            setTrains((prevTrains) =>
                prevTrains
                    .map((train) => {
                        return {
                            ...train,
                            timeTo: generateTimeTo(
                                (() => {
                                    const expected =
                                        train.fromStop?.expectedDeparture ||
                                        train.fromStop?.expectedArrival;

                                    if (!expected) return 0;
                                    const expectedDate =
                                        typeof expected === "string"
                                            ? new Date(expected)
                                            : expected;
                                    return (
                                        (expectedDate.getTime() -
                                            now.getTime()) /
                                        1000
                                    );
                                })()
                            ),
                        };
                    })
                    .filter((train) => {
                        const expected =
                            train.fromStop?.expectedDeparture ||
                            train.fromStop?.expectedArrival;
                        if (!expected) return false;
                        return (
                            new Date(new Date(expected).getTime() + 60 * 1000) >
                            now
                        );
                    })
            );
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed]);

    useEffect(() => {
        const getData = async () => {
            if (!fromStationCode || !toStationCode) {
                setMsg("Please enter both stations.");
                return;
            }
            try {
                const trainData = await fetchRoute(
                    fromStationCode,
                    toStationCode
                );

                if (trainData) {
                    if (trainData.length === 0) {
                        setMsg("No trains found for this route.");
                        setTrains([]);
                        setLoading(false);
                        return;
                    }
                    setTrains(trainData);
                    setStationFrom(trainData[0].fromStop ?? undefined);
                    setStationTo(trainData[0].toStop ?? undefined);
                    document.title = `${
                        trainData[0].fromStop?.description ?? "Unknown"
                    } to ${
                        trainData[0].toStop?.description ?? "Unknown"
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
    }, [fromStationCode, toStationCode]);

    return (
        <div className="gap-3 p-5 md:mx-20">
            <div
                className="flex items-center gap-2 p-1.5 px-2.5 my-2 text-sm font-semibold text-white transition-all cursor-pointer bg-neutral-800 w-fit rounded-xl hover:bg-blue-600"
                onClick={() => {
                    navigate(-1);
                }}>
                <FontAwesomeIcon icon={faArrowLeft} />
                Back
            </div>
            <div className="flex flex-col items-center w-full gap-4">
                <div className="flex flex-col items-center justify-center gap-3">
                    <div className="flex flex-wrap items-center justify-center text-2xl font-semibold text-center">
                        Trains from
                        <span className="mx-1 text-3xl font-bold">
                            {stationFrom?.description ?? "?"}
                        </span>
                        to
                        <span className="mx-1 text-3xl font-bold">
                            {stationTo?.description ?? "?"}
                        </span>
                    </div>
                    {/* <div className="flex flex-wrap items-center justify-center gap-4 gap-y-1">

                        <a
                            className="underline text-sky-500"
                            href={`https://bustimes.org/stops/${stop?.stop_id}`}
                            target="_blank">
                            View on bustimes.org
                        </a>

                    </div> */}
                </div>
                {/* <div className="flex flex-row justify-center gap-1 overflow-x-auto">
                    {stop?.services
                        .sort((a, b) =>
                            new Intl.Collator(undefined, {
                                numeric: true,
                                sensitivity: "base",
                            }).compare(a.line_name, b.line_name)
                        )
                        .map((service) => (
                            <span
                                key={service.id}
                                className="flex items-center justify-center px-3 py-1 text-lg font-bold text-center rounded-xl bg-neutral-800/50">
                                {service.line_name}
                            </span>
                        ))}
                </div> */}

                <div className="flex justify-center gap-2">
                    <span className="text-xs text-neutral-400">
                        {loading ? "Loading..." : `Updated ${elapsed} ago`}
                    </span>
                    <span className="text-xs text-neutral-400">·</span>
                    <span className="text-xs text-neutral-400">
                        Updates every 30s
                    </span>
                </div>

                <div className="flex flex-col w-full gap-1">
                    {msg ? (
                        <div className="flex justify-center gap-1 p-3">
                            <span className="text-red-400">{msg}</span>
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
                            {trains.map((train, idx) => (
                                <>
                                    <div className="flex items-center gap-2 mb-0.5">
                                        <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                        <span className="text-[10px] text-neutral-600">
                                            nextbus
                                        </span>
                                        <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                    </div>

                                    <TrainCard
                                        train={train}
                                        onClick={() =>
                                            navigate(
                                                `/trains/${train.serviceUid}?from=${fromStationCode}&to=${toStationCode}`
                                            )
                                        }
                                        idx={idx}
                                    />
                                    {idx === trains.length - 1 && (
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
                            {trains.length === 0 && (
                                <div className="flex justify-center">
                                    <span className="text-neutral-400">
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

export default TrainSearchPage;

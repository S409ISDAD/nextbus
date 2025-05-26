import { useEffect, useRef, useState } from "react";
import type { Bus } from "../models/Bus";
import type { Journey } from "../models/Journey";
import fetchJourney from "../utils/getJourney";
import getBus, { type BusResponse } from "../utils/getBus";
import { useNavigate, useParams } from "react-router";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBus, faLocationDot } from "@fortawesome/free-solid-svg-icons";
import {
    Flex,
    Text,
    Box,
    Container,
    Card,
    Badge,
    Separator,
    Skeleton,
    IconButton,
} from "@radix-ui/themes";

const JourneyPage: React.FC = () => {
    const { bus_id, journey_id } = useParams();

    const navigate = useNavigate();

    const [bus, setBus] = useState<BusResponse>();
    const [journey, setJourney] = useState<Journey>();
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
        }, 1000);
        return () => clearInterval(interval);
    }, [lastRefreshed]);

    const busRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (journey && busRef.current) {
            requestAnimationFrame(() => {
                busRef.current?.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                });
            });
        }
    }, [journey]);

    useEffect(() => {
        let interval: any;
        const getData = async (bus_id: string, journey_id: string) => {
            try {
                const journey = await fetchJourney(bus_id, journey_id);
                const bus = await getBus(bus_id);

                if (journey) {
                    setJourney(journey);
                } else {
                    setMsg("Failed to fetch journey. Try reloading the page");
                }

                if (bus) {
                    setBus(bus);
                } else {
                    setMsg("Failed to fetch bus. Try reloading the page");
                }
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
            }
        };
        const init = async (bus_id: string, journey_id: string) => {
            try {
                await getData(bus_id, journey_id);
                interval = setInterval(
                    () => getData(bus_id, journey_id),
                    30000
                );
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get journey data.");
                setLoading(false);
            }
        };

        if (bus_id && journey_id) {
            init(bus_id, journey_id);
        }

        return () => clearInterval(interval);
    }, [bus_id, journey_id]);

    return (
        <Container p="5">
            <Flex direction="column" gap="3">
                {journey?.stops.map((stop, idx) => (
                    <>
                        <Flex key={stop.stop_id} gap="2" align="center">
                            {bus?.progress.sequence == idx &&
                            bus.progress.progress < 0.1 ? (
                                <div ref={busRef}>
                                    {" "}
                                    <IconButton
                                        color="red"
                                        onClick={() =>
                                            navigate(
                                                `/departures/${stop.stop_id}`
                                            )
                                        }
                                        style={{
                                            cursor: "pointer",
                                        }}>
                                        <FontAwesomeIcon icon={faBus} />
                                    </IconButton>
                                </div>
                            ) : (
                                <IconButton
                                    onClick={() =>
                                        navigate(`/departures/${stop.stop_id}`)
                                    }
                                    style={{
                                        cursor: "pointer",
                                    }}>
                                    <FontAwesomeIcon icon={faLocationDot} />
                                </IconButton>
                            )}
                            <Separator></Separator>
                            <Flex direction="column">
                                <Text>{stop.name}</Text>
                                <Flex direction="row" gap="3">
                                    {stop.actual_departure_time ? (
                                        <Text color="red">
                                            <s>
                                                {stop.aimed_departure_time.toLocaleTimeString(
                                                    [],
                                                    {
                                                        hour: "2-digit",
                                                        minute: "2-digit",
                                                    }
                                                )}
                                            </s>
                                        </Text>
                                    ) : (
                                        <Text color="green">
                                            {stop.aimed_departure_time.toLocaleTimeString(
                                                [],
                                                {
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                }
                                            )}
                                        </Text>
                                    )}
                                    <Text color="green">
                                        {stop.actual_departure_time?.toLocaleTimeString()}
                                    </Text>
                                </Flex>
                            </Flex>
                        </Flex>
                        {bus?.progress.sequence == idx &&
                        bus.progress.progress > 0.1 ? (
                            <div ref={busRef}>
                                <Flex direction="row" gap="3" align="center">
                                    <IconButton color="red">
                                        <FontAwesomeIcon icon={faBus} />
                                    </IconButton>
                                    <Text weight="bold">
                                        The bus is currently here
                                    </Text>
                                </Flex>
                            </div>
                        ) : (
                            <></>
                        )}
                    </>
                ))}
            </Flex>
        </Container>
    );
};

export default JourneyPage;

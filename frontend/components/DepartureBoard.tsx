import { useEffect, useState } from "react";
import type { Bus } from "../models/Bus";
import fetchDepartures from "../utils/getDepartures";
import { useNavigate } from "react-router";
import {
    Flex,
    Text,
    Box,
    Container,
    Card,
    Badge,
    Separator,
    Skeleton,
} from "@radix-ui/themes";
import getClosestStop, { getCurrentPosition } from "../utils/closestStop";

interface Props {
    stop_id: string;
    closest?: boolean;
}

function DepartureBoard({ stop_id, closest }: Props) {
    const [buses, setBuses] = useState<Bus[]>([]);
    const [stop, setStop] = useState<String>("");
    const [stopID, setStopID] = useState<String>("");
    const [loading, setLoading] = useState(true);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
    const [msg, setMsg] = useState<string>("");

    const navigate = useNavigate();

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

    useEffect(() => {
        let interval: any;
        const getData = async (id: string) => {
            try {
                const departures = await fetchDepartures(id);

                if (departures) {
                    setBuses(departures.updatedBuses);
                    setStop(departures.stop_name);
                    setRefreshed(departures.timestamp);
                    setMsg("");
                } else {
                    setMsg("Failed to fetch departures.");
                }
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
            }
        };
        const init = async () => {
            try {
                if (closest) {
                    const pos = await getCurrentPosition();
                    const closest_stop_id = await getClosestStop(pos);
                    if (closest_stop_id) {
                        await getData(closest_stop_id);
                        setStopID(closest_stop_id);
                        const interval = setInterval(
                            () => getData(closest_stop_id),
                            30000
                        );
                        return () => clearInterval(interval);
                    } else {
                        setMsg("No stop found nearby");
                        setLoading(false);
                    }
                } else {
                    await getData(stop_id);
                    setStopID(stop_id);
                    interval = setInterval(() => getData(stop_id), 30000);
                }
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get location or stop data.");
                setLoading(false);
            }
        };

        init();

        return () => clearInterval(interval);
    }, [stop_id, closest]);

    if (loading) {
        return (
            <Container height="300px" minHeight="300px">
                {/* <Card style={{ height: "100%" }}>
                    <Flex
                        align="center"
                        justify="center"
                        gap="3"
                        style={{ height: "100%" }}>
                        <Text>Loading...</Text>
                        <Spinner size="3"></Spinner>
                    </Flex>
                </Card> */}
                <Card style={{ height: "100%" }}>
                    <Flex direction="column" gap="2" style={{ height: "100%" }}>
                        <Flex justify="center">
                            <Skeleton>
                                <Text
                                    size="5"
                                    weight="bold"
                                    align="center"
                                    truncate>
                                    Stop Name
                                </Text>
                            </Skeleton>
                        </Flex>

                        <Box style={{ flexGrow: 1, overflowY: "auto" }} px="2">
                            <Flex direction="column">
                                {[1, 2, 3].map((item) => (
                                    <Container key={item}>
                                        <Flex
                                            direction="row"
                                            align="center"
                                            justify="between">
                                            <Flex gap="2" direction="column">
                                                <Flex
                                                    direction="row"
                                                    gap="1"
                                                    align="center">
                                                    <Skeleton>
                                                        <Text>
                                                            12 to Location
                                                        </Text>
                                                    </Skeleton>
                                                </Flex>
                                                <Flex direction="row" gap="3">
                                                    <Skeleton>
                                                        <Text color="green">
                                                            10:10:10
                                                        </Text>
                                                    </Skeleton>
                                                </Flex>
                                            </Flex>
                                            <Flex
                                                direction="row"
                                                gap="2"
                                                align="center">
                                                <Skeleton>
                                                    <Badge
                                                        color="amber"
                                                        variant="solid">
                                                        <Text weight="bold">
                                                            0000000
                                                        </Text>
                                                    </Badge>
                                                </Skeleton>
                                                <Skeleton>
                                                    <Badge
                                                        color="iris"
                                                        size="3">
                                                        5 min
                                                    </Badge>
                                                </Skeleton>
                                            </Flex>
                                        </Flex>
                                        <Separator my="2" size="4" />
                                    </Container>
                                ))}
                            </Flex>
                        </Box>
                        <Box>
                            <Skeleton>Updated 1s ago</Skeleton>
                        </Box>
                    </Flex>
                </Card>
            </Container>
        );
    }

    return (
        <Container>
            <Card>
                <Flex direction="column" gap="2">
                    <Flex
                        justify="center"
                        onClick={() => navigate(`/departures/${stopID}`)}
                        style={{
                            cursor: "pointer",
                        }}>
                        <Text size="5" weight="bold" align="center" truncate>
                            {stop}
                        </Text>
                    </Flex>

                    <Box px="2">
                        <Flex
                            direction="column"
                            maxHeight="200px"
                            // minHeight="100px"
                            style={{ flexGrow: 1, overflowY: "auto" }}>
                            {msg ? (
                                <Flex justify="center">
                                    <Text color="red">{msg}</Text>
                                </Flex>
                            ) : (
                                <>
                                    {buses.map((bus) => (
                                        <Container
                                            key={bus.reg}
                                            onClick={() =>
                                                navigate(
                                                    `/buses/${bus.id}/journeys/${bus.journey_id}`
                                                )
                                            }
                                            style={{
                                                cursor: "pointer",
                                            }}>
                                            <Flex
                                                direction="row"
                                                align="center"
                                                justify="between">
                                                <Flex direction="column">
                                                    <Flex
                                                        direction="row"
                                                        gap="1"
                                                        align="center">
                                                        <Text
                                                            size="4"
                                                            weight="bold">
                                                            {
                                                                bus.service
                                                                    .line_name
                                                            }
                                                        </Text>
                                                        <Text
                                                            align="center"
                                                            size="2">
                                                            to
                                                        </Text>
                                                        <Text weight="bold">
                                                            {bus.destination}
                                                        </Text>
                                                    </Flex>
                                                    <Flex
                                                        direction="row"
                                                        gap="3">
                                                        {bus.delay > 30 ? (
                                                            <>
                                                                <Text color="red">
                                                                    <s>
                                                                        {bus.scheduled.toLocaleTimeString(
                                                                            [],
                                                                            {
                                                                                hour: "2-digit",
                                                                                minute: "2-digit",
                                                                            }
                                                                        )}
                                                                    </s>
                                                                </Text>
                                                                <Text color="mint">
                                                                    {bus.expected.toLocaleTimeString()}
                                                                </Text>
                                                            </>
                                                        ) : (
                                                            <Text color="green">
                                                                {bus.scheduled.toLocaleTimeString(
                                                                    [],
                                                                    {
                                                                        hour: "2-digit",
                                                                        minute: "2-digit",
                                                                    }
                                                                )}
                                                            </Text>
                                                        )}
                                                    </Flex>
                                                </Flex>
                                                <Flex
                                                    direction="row"
                                                    gap="2"
                                                    align="center">
                                                    <Badge
                                                        color="amber"
                                                        variant="solid">
                                                        <Text weight="bold">
                                                            {bus.reg}
                                                        </Text>
                                                    </Badge>
                                                    <Badge
                                                        color="iris"
                                                        size="3">
                                                        {bus.timeto}
                                                    </Badge>
                                                </Flex>
                                            </Flex>
                                            <Separator my="2" size="4" />
                                        </Container>
                                    ))}
                                    {buses.length < 4 ? (
                                        <Flex justify="center">
                                            <Text color="gray">
                                                No more departures!
                                            </Text>
                                        </Flex>
                                    ) : (
                                        <></>
                                    )}
                                </>
                            )}
                        </Flex>
                    </Box>
                    <Flex gap="2">
                        <Text color="gray" size="1">
                            Updated {elapsed} ago
                        </Text>
                        <Text color="gray" size="1">
                            ·
                        </Text>
                        <Text color="gray" size="1">
                            Updates every 30s
                        </Text>
                    </Flex>
                </Flex>
            </Card>
        </Container>
    );
}

export default DepartureBoard;

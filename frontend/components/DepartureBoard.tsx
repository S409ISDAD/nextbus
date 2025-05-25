import { useEffect, useState } from "react";
import api from "../src/api";
import type { Bus } from "../models/Bus";
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

interface DeparturesResponse {
    timestamp: number;
    stop_name: string;
    buses: any[];
}

interface Props {
    stop_id: string;
}

function DepartureBoard({ stop_id }: Props) {
    const [buses, setBuses] = useState<Bus[]>([]);
    const [stop, setStop] = useState<String>("");
    const [loading, setLoading] = useState(true);
    const [lastRefreshed, setRefreshed] = useState(new Date());
    const [elapsed, setElapsed] = useState<string>("0s");
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
        const fetchDepartures = async () => {
            try {
                const response = await api.get<DeparturesResponse>(
                    `/departures/?stop_id=${stop_id}`
                );
                const now = new Date();
                const updatedBuses: Bus[] = response.data.buses
                    .map((bus) => {
                        const expected = new Date(bus.expected * 1000);
                        const scheduled = new Date(bus.scheduled * 1000);

                        const diffMs = expected.getTime() - now.getTime();

                        const min = Math.round(diffMs / 1000 / 60);

                        return {
                            ...bus,
                            expected,
                            scheduled,
                            timeto: min < 1 ? "Due" : `${min} min`,
                        };
                    })
                    .filter((bus) => bus.expected > now)
                    .sort(
                        (a, b) => a.expected.getTime() - b.expected.getTime()
                    );

                setBuses(updatedBuses);
                setStop(response.data.stop_name);
                setRefreshed(new Date(response.data.timestamp * 1000));
            } catch (error) {
                console.error("failed to get departures", error);
            } finally {
                setLoading(false);
            }
        };
        fetchDepartures();
        const interval = setInterval(fetchDepartures, 30000);
        return () => clearInterval(interval);
    }, [stop_id]);

    if (loading) {
        return (
            <Container height="300px" minHeight="300px" width="90vw">
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
                                {[1, 2, 3].map(() => (
                                    <Container>
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
        <Container width="90vw">
            <Card>
                <Flex direction="column" gap="2">
                    <Flex justify="center">
                        <Text size="5" weight="bold" align="center" truncate>
                            {stop}
                        </Text>
                    </Flex>

                    <Box style={{ flexGrow: 1, overflowY: "auto" }} px="2">
                        <Flex
                            direction="column"
                            maxHeight="200px"
                            minHeight="100px"
                            justify="center">
                            {buses.map((bus) => (
                                <Container key={bus.reg}>
                                    <Flex
                                        direction="row"
                                        align="center"
                                        justify="between">
                                        <Flex direction="column">
                                            <Flex
                                                direction="row"
                                                gap="1"
                                                align="center">
                                                <Text size="4" weight="bold">
                                                    {bus.service.line_name}
                                                </Text>
                                                <Text align="center" size="2">
                                                    to
                                                </Text>
                                                <Text weight="bold">
                                                    {bus.destination}
                                                </Text>
                                            </Flex>
                                            <Flex direction="row" gap="3">
                                                {bus.delay > 30 ? (
                                                    <>
                                                        <Text color="red">
                                                            <s>
                                                                {bus.scheduled.toLocaleTimeString()}
                                                            </s>
                                                        </Text>
                                                        <Text color="mint">
                                                            {bus.expected.toLocaleTimeString()}
                                                        </Text>
                                                    </>
                                                ) : (
                                                    <Text color="green">
                                                        {bus.scheduled.toLocaleTimeString()}
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
                                            <Badge color="iris" size="3">
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

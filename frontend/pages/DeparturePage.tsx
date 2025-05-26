import { useEffect, useState } from "react";
import type { Bus } from "../models/Bus";
import type { Stop } from "../models/Stop";
import fetchDepartures from "../utils/fetchDepartures";
import getStopData from "../utils/getStopData";
import { useNavigate, useParams } from "react-router";
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

const DeparturePage: React.FC = () => {
    const { stop_id } = useParams();

    const navigate = useNavigate();

    const [buses, setBuses] = useState<Bus[]>([]);
    const [stop, setStop] = useState<Stop>();
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

    useEffect(() => {
        let interval: any;
        const getData = async (id: string) => {
            try {
                const stop = await getStopData(id);

                if (stop) {
                    setStop(stop);
                }

                const departures = await fetchDepartures(id);

                if (departures) {
                    setBuses(departures.updatedBuses);
                    setRefreshed(departures.timestamp);
                } else {
                    setMsg(
                        "Failed to fetch departures. Try reloading the page"
                    );
                }
            } catch {
                console.log("uh oh");
            } finally {
                setLoading(false);
            }
        };
        const init = async (stop_id: string) => {
            try {
                await getData(stop_id);
                interval = setInterval(() => getData(stop_id), 30000);
            } catch (error) {
                console.error("Init error:", error);
                setMsg("Unable to get stop data.");
                setLoading(false);
            }
        };

        if (stop_id) {
            init(stop_id);
        }

        return () => clearInterval(interval);
    }, [stop_id]);

    return (
        <Container p="5">
            <Flex direction="column" gap="2">
                <Flex
                    justify="center"
                    direction="column"
                    gap="1"
                    align="center">
                    <Text size="8" weight="bold" align="center" wrap="pretty">
                        {stop?.stop_name}
                    </Text>
                    <Text align="center">({stop?.long_name})</Text>
                </Flex>
                <Flex direction="row" gap="1" justify="center" wrap="wrap">
                    {stop?.services
                        .sort((a, b) =>
                            new Intl.Collator(undefined, {
                                numeric: true,
                                sensitivity: "base",
                            }).compare(a.line_name, b.line_name)
                        )
                        .map((service) => (
                            <Card key={service.id}>
                                <Text>{service.line_name}</Text>
                            </Card>
                        ))}
                </Flex>

                <Flex gap="2" justify="center">
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

                <Box style={{ flexGrow: 1, overflowY: "scroll" }} p="3">
                    <Flex direction="column" gap="3">
                        {msg ? (
                            <Flex justify="center">
                                <Text color="red">{msg}</Text>
                            </Flex>
                        ) : loading ? (
                            <>
                                {[1, 2, 3, 4, 5].map((i) => (
                                    <Card key={i} style={{ cursor: "pointer" }}>
                                        <Flex
                                            direction="row"
                                            align="center"
                                            justify="between">
                                            <Flex
                                                direction="column"
                                                gap="1"
                                                align="start">
                                                <Skeleton>
                                                    <Text weight="bold">
                                                        123 to Location
                                                    </Text>
                                                </Skeleton>
                                                <Skeleton>
                                                    <Text color="green">
                                                        10:10:10
                                                    </Text>
                                                </Skeleton>
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
                                                            AB12ACB
                                                        </Text>
                                                    </Badge>
                                                </Skeleton>
                                                <Skeleton>
                                                    <Badge
                                                        color="iris"
                                                        size="3">
                                                        <Text size="5">5</Text>
                                                        min
                                                    </Badge>
                                                </Skeleton>
                                            </Flex>
                                        </Flex>
                                    </Card>
                                ))}
                            </>
                        ) : (
                            <>
                                {buses.map((bus) => (
                                    <Card
                                        key={bus.reg}
                                        onClick={() =>
                                            navigate(
                                                `/journeys/${bus.journey_id}`
                                            )
                                        }
                                        style={{ cursor: "pointer" }}>
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
                                                        {bus.service.line_name}
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
                                                {bus.service.detail && (
                                                    <Text>
                                                        Via:{" "}
                                                        {bus.service.detail}
                                                    </Text>
                                                )}
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
                                                    <Text size="5">
                                                        {
                                                            bus.timeto.split(
                                                                " "
                                                            )[0]
                                                        }
                                                    </Text>
                                                    {bus.timeto.split(" ")[1]}
                                                </Badge>
                                            </Flex>
                                        </Flex>
                                    </Card>
                                ))}
                                {buses.length < 4 && (
                                    <Flex justify="center">
                                        <Text color="gray">
                                            No more departures!
                                        </Text>
                                    </Flex>
                                )}
                            </>
                        )}
                    </Flex>
                </Box>
            </Flex>
        </Container>
    );
};

export default DeparturePage;

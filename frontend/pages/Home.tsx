import { Container, Flex, TextField, Text, Button } from "@radix-ui/themes";
import React from "react";
import DepartureBoard from "../components/DepartureBoard";
import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

const Home: React.FC = () => {
    return (
        <div>
            <Flex
                direction="column"
                gap="6"
                pt="9"
                justify="center"
                align="center">
                <Flex
                    direction="column"
                    p="7"
                    gap="8"
                    justify="center"
                    align="center">
                    <Text weight="bold" size="8" align="center">
                        The best way to get the bus.
                    </Text>
                    <TextField.Root
                        placeholder="Search for a stop..."
                        radius="full"
                        size="3"
                        style={{ width: "100%", height: "58px" }}>
                        <TextField.Slot>
                            <Flex ml="2">
                                <FontAwesomeIcon
                                    height="16"
                                    width="16"
                                    icon={faMagnifyingGlass}
                                />
                            </Flex>
                        </TextField.Slot>
                        <TextField.Slot side="right" px="1">
                            <Flex mr="1">
                                <Button size="3">Go</Button>
                            </Flex>
                        </TextField.Slot>
                    </TextField.Root>
                </Flex>
                <Flex
                    direction="row"
                    gap="5"
                    justify="center"
                    align="center"
                    p="5"
                    wrap="wrap">
                    <Text size="6" weight="bold" wrap="pretty" align="center">
                        Departure Boards for Every Operator
                    </Text>
                    <DepartureBoard stop_id="1990PH130449"></DepartureBoard>
                </Flex>
            </Flex>
        </div>
    );
};

export default Home;

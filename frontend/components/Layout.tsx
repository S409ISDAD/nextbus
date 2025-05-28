import { Link, Outlet } from "react-router";
import { Button, Flex, Text } from "@radix-ui/themes";
import Clock from "../components/Clock";

export default function Layout() {
    return (
        <>
            <Flex
                justify="between"
                p="2"
                position="sticky"
                style={{
                    top: 0,
                    background: "#141514",
                    zIndex: 1000,
                    borderBottom: "1px solid #272A2D",
                    borderRadius: "0px 0px 20px 20px",
                }}>
                <Flex gap="2">
                    <Link to="/">
                        <Button
                            variant="surface"
                            size="3"
                            color="iris"
                            style={{
                                cursor: "pointer",
                                height: "100%",
                                borderRadius: "13px",
                            }}>
                            Home
                        </Button>
                    </Link>

                    <Link to="/buses">
                        <Button
                            variant="surface"
                            size="3"
                            color="teal"
                            style={{
                                cursor: "pointer",
                                height: "100%",
                                borderRadius: "13px",
                            }}>
                            Buses
                        </Button>
                    </Link>
                </Flex>
                <Flex align="center">
                    <Text size="6" weight="bold">
                        Bus App
                    </Text>
                </Flex>
                <Flex>
                    <Clock></Clock>
                </Flex>
            </Flex>
            <main>
                <Outlet />
            </main>
        </>
    );
}

import { Link, Outlet } from "react-router";
import { Button, Flex, Text } from "@radix-ui/themes";
import Clock from "../components/Clock";

export default function Layout() {
    return (
        <>
            <Flex justify="between" p="3" pb="2">
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

import { useEffect, useState } from "react";
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

function Navbar() {
    return (
        <Container style={{ backgroundColor: "var(--gray-a3)", width: "100%" }}>
            <Flex>
                <Text>Navbar</Text>
            </Flex>
        </Container>
    );
}

export default Navbar;

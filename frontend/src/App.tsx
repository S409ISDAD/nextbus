import { useEffect, useState } from "react";
import DepartureBoard from "../components/DepartureBoard";
import Navbar from "../components/Navbar";
import { Container, Flex, Text } from "@radix-ui/themes";

function App() {
    return (
        <Container>
            {/* <Navbar></Navbar> */}
            <Flex
                direction="column"
                gap="3"
                p="4"
                justify="center"
                align="center">
                {/* <Text>Bus thing idk</Text> */}
                <DepartureBoard stop_id="149000007530"></DepartureBoard>
                <DepartureBoard stop_id="1900HA110364"></DepartureBoard>
            </Flex>
        </Container>
    );
}

export default App;

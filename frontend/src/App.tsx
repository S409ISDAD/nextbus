import { useEffect, useState } from "react";
import DepartureBoard from "../components/DepartureBoard";
import Navbar from "../components/Navbar";
import { Container, Flex, Text } from "@radix-ui/themes";
import getClosestStop, { getCurrentPosition } from "../utils/closestStop";

function App() {
    return (
        <Container>
            {/* <Navbar></Navbar> */}
            <Flex
                direction="row"
                gap="3"
                p="4"
                justify="center"
                align="center"
                wrap="wrap">
                {/* <Text>Bus thing idk</Text> */}

                <DepartureBoard stop_id="" closest={true}></DepartureBoard>
                <DepartureBoard stop_id="149000007530"></DepartureBoard>
                <DepartureBoard stop_id="1900HA110364"></DepartureBoard>
            </Flex>
        </Container>
    );
}

export default App;

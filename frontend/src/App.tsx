import { useEffect, useState } from "react";
import DepartureBoard from "../components/DepartureBoard";
import { Container, Flex, Text } from "@radix-ui/themes";

function App() {
    return (
        <Flex direction="column" gap="3" p="4" justify="center" align="center">
            <Text>Bus thing idk</Text>
            <DepartureBoard stop_id="149000007530"></DepartureBoard>
            <DepartureBoard stop_id="490016425WA"></DepartureBoard>
        </Flex>
    );
}

export default App;

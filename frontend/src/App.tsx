import { useEffect, useState } from "react";
import DepartureBoard from "../components/DepartureBoard";
import Navbar from "../components/Navbar";
import { Container, Flex, Text } from "@radix-ui/themes";
import getClosestStop, { getCurrentPosition } from "../utils/closestStop";

function App() {
    const [stop_id, setClosestStop] = useState<string>("");
    const [error_msg, setErrorMessage] = useState<string>("");

    useEffect(() => {
        const get_stop_id = async () => {
            try {
                const pos = await getCurrentPosition();
                const stop_id = await getClosestStop(pos);
                if (stop_id) {
                    setClosestStop(stop_id);
                }
            } catch (error) {
                console.log("uh oh");
                // console.error(error);
                setErrorMessage("Failed to get current location.");
            }
        };
        get_stop_id();
        const interval = setInterval(get_stop_id, 30000);
        return () => clearInterval(interval);
    }, [stop_id]);

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

                <DepartureBoard
                    stop_id={stop_id}
                    error_msg={error_msg}></DepartureBoard>
                <DepartureBoard stop_id="149000007530"></DepartureBoard>
                <DepartureBoard stop_id="1900HA110364"></DepartureBoard>
            </Flex>
        </Container>
    );
}

export default App;

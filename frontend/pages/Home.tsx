import { Container, Flex } from "@radix-ui/themes";
import React from "react";
import DepartureBoard from "../components/DepartureBoard";

const Home: React.FC = () => {
    return (
        <Container>
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
};

export default Home;

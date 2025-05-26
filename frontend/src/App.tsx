import { useEffect, useState } from "react";
import DepartureBoard from "../components/DepartureBoard";
import DeparturePage from "../pages/DeparturePage";
import Home from "../pages/Home";
import Navbar from "../components/Navbar";
import { Container, Flex, Text } from "@radix-ui/themes";
import { BrowserRouter, Routes, Route } from "react-router";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="departures/:stop_id" element={<DeparturePage />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;

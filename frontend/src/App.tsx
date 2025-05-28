import { useEffect, useState } from "react";
import DepartureBoard from "../components/DepartureBoard";
import DeparturePage from "../pages/DeparturePage";
import Home from "../pages/Home";
import JourneyPage from "../pages/JourneyPage";
import BusPage from "../pages/BusPage";
import Layout from "../components/Layout";
import Navbar from "../components/Navbar";
import { BrowserRouter, Routes, Route } from "react-router";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route element={<Layout />}>
                    <Route path="/" element={<Home />} />
                    <Route path="/buses" element={<BusPage />} />
                    <Route
                        path="departures/:stop_id"
                        element={<DeparturePage />}
                    />
                    <Route
                        path="/buses/:bus_id/journeys/:journey_id"
                        element={<JourneyPage />}
                    />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;

import { useEffect, useState } from "react";
import DepartureBoard from "../components/DepartureBoard";
import DeparturePage from "../pages/DeparturePage";
import JourneyPage from "../pages/JourneyPage";
import Home from "../pages/Home";
import Navbar from "../components/Navbar";
import { BrowserRouter, Routes, Route } from "react-router";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="departures/:stop_id" element={<DeparturePage />} />
                <Route
                    path="/buses/:bus_id/journeys/:journey_id"
                    element={<JourneyPage />}
                />
            </Routes>
        </BrowserRouter>
    );
}

export default App;

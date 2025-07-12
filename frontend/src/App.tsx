import DeparturePage from "../pages/DeparturePage";
import DepartureScreen from "../pages/DepartureScreen";
import Home from "../pages/Home";
import JourneyPage from "../pages/JourneyPage";
import BusPage from "../pages/BusPage";
import Layout from "../components/Layout";
import { BrowserRouter, Routes, Route } from "react-router";
import { Toaster } from "react-hot-toast";

function App() {
    return (
        <div className="h-full">
            <Toaster position="top-right" reverseOrder={false} />
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
                            path="/buses/:bus_id"
                            element={<JourneyPage />}
                        />
                    </Route>
                    <Route
                        path="departureboard/:stop_id"
                        element={<DepartureScreen />}
                    />
                </Routes>
            </BrowserRouter>
        </div>
    );
}

export default App;

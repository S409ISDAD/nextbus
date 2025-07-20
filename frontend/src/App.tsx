import DeparturePage from "../pages/DeparturePage";
import DepartureScreen from "../pages/DepartureScreen";
import Home from "../pages/Home";
import JourneyPage from "../pages/JourneyPage";
import PrivacyPolicy from "../pages/Privacy";
import Terms from "../pages/Terms";
import BusPage from "../pages/BusPage";
import Layout from "../components/Layout";
import { BrowserRouter, Routes, Route, useLocation } from "react-router";
import { Toaster } from "react-hot-toast";
import { faXmark } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { useState, useEffect } from "react";

function UsefulBanner() {
    const location = useLocation();
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        setVisible(true);
    }, []);

    if (location.pathname === "/" || !visible) return null;
    return (
        <div className="fixed flex items-center justify-center p-3 transform -translate-x-1/2 bg-teal-900 shadow-lg z-[99999] bottom-4 left-1/2 rounded-2xl">
            <span className="text-center text-gray-200 text-nowrap">
                Finding this useful?{" "}
                <a
                    href="https://forms.gle/SxrFyLQ1HedQcLLC7"
                    className="text-teal-400 underline"
                    target="_blank"
                    rel="noopener noreferrer">
                    Help improve it!
                </a>
                <button
                    className="px-2 ml-2 text-gray-100 transition bg-teal-700 rounded-full cursor-pointer hover:bg-teal-800"
                    onClick={() => setVisible(false)}>
                    {" "}
                    <FontAwesomeIcon icon={faXmark} size="sm" />
                </button>
            </span>
        </div>
    );
}

function App() {
    return (
        <div className="flex flex-col min-h-screen">
            <Toaster
                position="top-right"
                reverseOrder={false}
                toastOptions={{
                    style: {
                        borderRadius: "20px",
                        background: "#222",
                        color: "#fff",
                        border: "1px solid #363636",
                        marginTop: "60px",
                    },
                }}
            />
            <BrowserRouter>
                <UsefulBanner />
                <Routes>
                    <Route element={<Layout />}>
                        <Route path="/" element={<Home />} />
                        <Route path="/buses" element={<BusPage />} />
                        <Route path="/privacy" element={<PrivacyPolicy />} />
                        <Route path="/terms" element={<Terms />} />
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
            <footer className="flex flex-row justify-center w-full gap-2 p-3 text-sm text-gray-200 border-t-2 border-neutral-800 grow">
                <span>© 2025 nextbus</span>|
                <a href="/privacy" className="underline">
                    Privacy
                </a>
                |
                <a href="/terms" className="underline">
                    Terms
                </a>
            </footer>
        </div>
    );
}

export default App;

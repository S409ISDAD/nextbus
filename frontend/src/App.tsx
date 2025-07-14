import DeparturePage from "../pages/DeparturePage";
import DepartureScreen from "../pages/DepartureScreen";
import Home from "../pages/Home";
import JourneyPage from "../pages/JourneyPage";
import BusPage from "../pages/BusPage";
import Layout from "../components/Layout";
import { BrowserRouter, Routes, Route } from "react-router";
import { Toaster } from "react-hot-toast";
import { faXmark } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

function App() {
    return (
        <div className="h-full">
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
            <div className="fixed flex items-center justify-center p-3 transform -translate-x-1/2 bg-teal-900 shadow-lg z-99999 bottom-4 left-1/2 rounded-2xl">
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
                        className="px-2 ml-2 text-gray-100 transition bg-teal-700 rounded-full hover:bg-teal-800"
                        onClick={(e) => {
                            (e.target as HTMLElement).closest("div")?.remove();
                        }}
                        aria-label="Close">
                        <FontAwesomeIcon icon={faXmark} size="sm" />
                    </button>
                </span>
            </div>
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

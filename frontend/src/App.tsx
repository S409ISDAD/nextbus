import DeparturePage from "../pages/DeparturePage";
import DepartureScreen from "../pages/DepartureScreen";
import Home from "../pages/Home";
import JourneyPage from "../pages/JourneyPage";
import PrivacyPolicy from "../pages/Privacy";
import Terms from "../pages/Terms";
import BusPage from "../pages/BusPage";
import ServicePage from "../pages/ServicePage";
import Layout from "../components/Layout";
import StationPage from "../pages/StationPage";
import TrainPage from "../pages/TrainPage";
import TrainSearchPage from "../pages/TrainSearchPage";
import { BrowserRouter, Routes, Route, useLocation } from "react-router";
import { Toaster } from "react-hot-toast";
import { faXmark } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { useState, useEffect } from "react";
import {
    Dialog,
    DialogBackdrop,
    DialogPanel,
    DialogTitle,
} from "@headlessui/react";

function UsefulBanner() {
    const location = useLocation();
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        setVisible(true);
    }, []);

    if (location.pathname === "/" || !visible) return null;
    return (
        <div className="fixed flex gap-2 items-center justify-center p-3 transform -translate-x-1/2 bg-neutral-800 shadow-lg z-[99999] bottom-4 left-1/2 rounded-2xl">
            <span className="text-center text-gray-200 text-nowrap">
                Finding this useful?{" "}
                <a
                    href="https://forms.gle/SxrFyLQ1HedQcLLC7"
                    className="underline text-sky-500"
                    target="_blank"
                    rel="noopener noreferrer">
                    Help improve it!
                </a>
            </span>
            <button
                className="flex items-center justify-center px-2 cursor-pointer aspect-square bg-neutral-900/50 rounded-2xl hover:bg-neutral-900"
                onClick={() => setVisible(false)}>
                {" "}
                <FontAwesomeIcon icon={faXmark} size="sm" />
            </button>
        </div>
    );
}

function App() {
    const currentYear = new Date().getFullYear();
    const [isOpen, setIsOpen] = useState(false);
    const params = new URLSearchParams(window.location.search);
    if (params.get("from") === "fly") {
        setIsOpen(true);
        const url = new URL(window.location.href);
        url.searchParams.delete("from");
        window.history.replaceState({}, document.title, url.toString());
    }

    return (
        <BrowserRouter>
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
                <Dialog
                    open={isOpen}
                    as="div"
                    className="relative z-10 focus:outline-none"
                    onClose={close}>
                    <DialogBackdrop className="fixed inset-0 bg-black/60" />
                    <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
                        <div className="flex items-center justify-center min-h-full p-4">
                            <DialogPanel
                                transition
                                className="w-full max-w-md rounded-3xl bg-[#1e1e1e] p-6 duration-300 ease-out data-closed:transform-[scale(95%)] data-closed:opacity-0">
                                <DialogTitle
                                    as="h3"
                                    className="text-2xl font-bold">
                                    We've Moved!
                                </DialogTitle>
                                <p className="mt-2 text-neutral-200/80">
                                    You were redirected from{" "}
                                    <b>nextbus.fly.dev</b> because that address
                                    is no longer in use.
                                </p>
                                <p className="mt-2 text-neutral-200/80">
                                    Please use <b>nextbus.orbitix.dev</b> from
                                    now on, and update any bookmarks you may
                                    have.
                                </p>
                                <div className="mt-4">
                                    <div
                                        className="inline-flex cursor-pointer items-center gap-2 rounded-md bg-blue-500 px-3 py-1.5 text-sm/6 font-semibold text-white  transition-all focus:not-data-focus:outline-none hover:bg-blue-600 data-focus:outline data-focus:outline-white data-hover:bg-gray-600 data-open:bg-gray-700"
                                        onClick={() => setIsOpen(false)}>
                                        Got it, thanks!
                                    </div>
                                </div>
                            </DialogPanel>
                        </div>
                    </div>
                </Dialog>
                <UsefulBanner />
                <Routes>
                    <Route element={<Layout />}>
                        <Route path="/" element={<Home />} />
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
                        <Route
                            path="/services/:service_id"
                            element={<ServicePage />}
                        />
                        <Route
                            path="/stations/:station_id"
                            element={<StationPage />}
                        />
                        <Route
                            path="/search/trains/:fromStationCode/to/:toStationCode"
                            element={<TrainSearchPage />}
                        />
                        <Route
                            path="/trains/:service_id"
                            element={<TrainPage />}
                        />
                    </Route>
                    <Route
                        path="departureboard/:stop_id"
                        element={<DepartureScreen />}
                    />
                </Routes>
                <footer className="flex flex-row flex-wrap justify-center w-full gap-3 p-3 text-sm text-gray-200 border-t-2 max-h-fit border-neutral-800 grow">
                    <span>© {currentYear} nextbus</span>
                    <a href="/privacy" className="underline text-sky-400 h-fit">
                        Privacy
                    </a>

                    <a href="/terms" className="underline text-sky-400 h-fit">
                        Terms
                    </a>

                    <div className="flex gap-1 h-fit">
                        <span>Bus data:</span>
                        <a
                            href="https://bustimes.org"
                            className="underline text-sky-400"
                            target="_blank"
                            rel="noopener noreferrer">
                            bustimes.org
                        </a>
                    </div>

                    <div className="flex gap-1 h-fit">
                        <span>Train data:</span>
                        <a
                            href="https://realtimetrains.co.uk"
                            className="underline text-sky-400"
                            target="_blank"
                            rel="noopener noreferrer">
                            realtimetrains.co.uk
                        </a>
                    </div>
                </footer>
            </div>
        </BrowserRouter>
    );
}

export default App;

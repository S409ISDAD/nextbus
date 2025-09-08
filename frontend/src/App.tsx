import DeparturePage from "../pages/DeparturePage";
import DepartureScreen from "../pages/DepartureScreen";
import Home from "../pages/Home";
import JourneyPage from "../pages/JourneyPage";
import PrivacyPolicy from "../pages/Privacy";
import Terms from "../pages/Terms";
import Data from "../pages/Data";
import BusPage from "../pages/BusPage";
import ServicePage from "../pages/ServicePage";
import Layout from "../components/Layout";
import StationPage from "../pages/StationPage";
import TrainPage from "../pages/TrainPage";
import NotFound from "../pages/NotFound";
import StatsPage from "../pages/Stats";
import TrainSearchPage from "../pages/TrainSearchPage";
import TrainsDashboard from "../pages/Trains";
import { BrowserRouter, Routes, Route, useLocation } from "react-router";
import { Toaster } from "react-hot-toast";
import { faXmark } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import useReloadPrompt from "../components/ReloadPrompt";
import InstallToast from "../components/InstallPrompt";
import useLocalStorageState from "use-local-storage-state";
import version from "../utils/version";
import { useShowAppNav } from "../utils/AppNav";
import toast from "react-hot-toast";

import { useState, useEffect } from "react";
import {
    Dialog,
    DialogBackdrop,
    DialogPanel,
    DialogTitle,
} from "@headlessui/react";
import StopMap from "../components/StopMap";

function UsefulBanner() {
    const location = useLocation();
    const [visible, setVisible] = useState(true);
    const showAppNav = useShowAppNav();

    useEffect(() => {
        setVisible(true);
    }, []);

    if (location.pathname === "/" || !visible) return null;
    return (
        <div
            className={`fixed flex gap-2 items-center justify-center p-3 transform -translate-x-1/2 bg-neutral-800 shadow-lg z-[99999] ${
                showAppNav ? "bottom-19" : "bottom-4"
            } left-1/2 rounded-2xl`}>
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
    const [isOpen, setIsOpen] = useState(false);
    const [haveReset, setHaveReset] = useLocalStorageState<boolean>(
        "haveResetSW",
        {
            defaultValue: false,
        }
    );
    const showAppNav = useShowAppNav();
    const reset = async () => {
        if (!haveReset) {
            const registrations =
                await navigator.serviceWorker.getRegistrations();
            for (const reg of registrations) {
                console.log("Unregistering service worker:", reg);
                await reg.unregister();
            }

            const cacheNames = await caches.keys();
            for (const name of cacheNames) {
                console.log("Deleting cache:", name);
                await caches.delete(name);
            }
            setHaveReset(true);
        }
    };
    useEffect(() => {
        console.log("App mounted");
        console.log("Current version:", version);
        console.log("showAppNav:", showAppNav);

        const params = new URLSearchParams(window.location.search);
        if (params.get("from") === "fly") {
            setIsOpen(true);
            const url = new URL(window.location.href);
            url.searchParams.delete("from");
            window.history.replaceState({}, document.title, url.toString());
        }
        reset();
        const prevVersion = localStorage.getItem("appVersion");
        const currentVersion = version;
        if (prevVersion && prevVersion !== currentVersion) {
            toast.success("App updated to latest version");
        }
        localStorage.setItem("appVersion", currentVersion);
    }, []);

    useReloadPrompt();

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
                            marginRight: "-8px",
                            color: "#fff",
                            border: "1px solid #363636",
                            zIndex: "99",
                        },
                    }}
                />
                <InstallToast />
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
                                        className="inline-flex cursor-pointer items-center gap-2 rounded-md bg-blue-600 px-3 py-1.5 text-sm/6 font-semibold text-white  transition-all focus:not-data-focus:outline-none hover:bg-blue-700 data-focus:outline data-focus:outline-white data-hover:bg-gray-600 data-open:bg-gray-700"
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
                        <Route path="*" element={<NotFound />} />
                        <Route path="/" element={<Home />} />
                        <Route path="/privacy" element={<PrivacyPolicy />} />
                        <Route path="/terms" element={<Terms />} />
                        <Route path="/data" element={<Data />} />
                        <Route path="/stats" element={<StatsPage />} />
                        <Route path="/map" element={<StopMap />} />
                        <Route path="/buses" element={<BusPage />} />
                        <Route
                            path="/buses/stops/:stop_id"
                            element={<DeparturePage />}
                        />
                        <Route
                            path="/buses/:bus_id"
                            element={<JourneyPage />}
                        />
                        <Route
                            path="buses/services/:service_id"
                            element={<ServicePage />}
                        />
                        <Route path="/trains" element={<TrainsDashboard />} />
                        <Route
                            path="/trains/stations/:station_id"
                            element={<StationPage />}
                        />
                        <Route
                            path="trains/search/:fromStationCode/to/:toStationCode"
                            element={<TrainSearchPage />}
                        />
                        <Route
                            path="trains/:service_id"
                            element={<TrainPage />}
                        />
                    </Route>
                    <Route
                        path="departureboard/:stop_id"
                        element={<DepartureScreen />}
                    />
                </Routes>
            </div>
        </BrowserRouter>
    );
}

export default App;

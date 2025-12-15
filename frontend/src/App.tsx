import DeparturePage from "../pages/bus/DeparturePage.tsx";
import DepartureScreen from "../pages/bus/DepartureScreen.tsx";
import Home from "../pages/Home";
import LiveJourneyPage from "../pages/bus/LiveJourneyPage.tsx";
import JourneyPage from "../pages/bus/JourneyPage.tsx";
import PrivacyPolicy from "../pages/Privacy";
import Terms from "../pages/Terms";
import Data from "../pages/Data";
import BusPage from "../pages/bus/BusPage.tsx";
import ServicePage from "../pages/bus/ServicePage.tsx";
import Layout from "../components/Layout";
import StationPage from "../pages/train/StationPage.tsx";
import TrainPage from "../pages/train/TrainPage.tsx";
import NotFound from "../pages/NotFound";
import StatsPage from "../pages/Stats";
import TrainSearchPage from "../pages/train/TrainSearchPage.tsx";
import TrainsDashboard from "../pages/train/Trains.tsx";
import { BrowserRouter, Route, Routes } from "react-router";
import { Toaster } from "react-hot-toast";
import InstallToast from "../components/InstallPrompt";
import version from "../utils/version";
import { useShowAppNav } from "../utils/AppNav";
import { MotionConfig } from "framer-motion";
import SearchPage from "../pages/Search";
import RegionsPage from "../pages/places/Regions.tsx";
import RegionPage from "../pages/places/Region.tsx";
import AdminAreaPage from "../pages/places/AdminArea.tsx";
import DistrictPage from "../pages/places/District.tsx";
import LocalityPage from "../pages/places/Locality.tsx";
import SourcesPage from "../pages/Sources.tsx";
import DataSourcePage from "../pages/DataSource.tsx";
import InstallHelp from "../pages/InstallHelp.tsx";

import { useEffect, useState } from "react";
import {
    Dialog,
    DialogBackdrop,
    DialogPanel,
    DialogTitle,
} from "@headlessui/react";
import Map from "../components/Map";
import PossibleJourneysPage from "../pages/PossibleJourneysPage.tsx";
import PredictionsPage from "../pages/bus/Predictions.tsx";
import ErrorBoundary from "../components/ErrorBoundary.tsx";
import Error from "../pages/Error.tsx";
import Canonical from "./Canonical.tsx";

// function UsefulBanner() {
//     const location = useLocation();
//     const [visible, setVisible] = useState(true);
//     const showAppNav = useShowAppNav();

//     useEffect(() => {
//         setVisible(true);
//     }, []);

//     if (location.pathname === "/" || !visible) return null;
//     return (
//         <div
//             className={`fixed flex gap-2 items-center justify-center p-3 transform -translate-x-1/2 bg-neutral-800 shadow-lg z-[99999] ${
//                 showAppNav ? "bottom-19" : "bottom-4"
//             } left-1/2 rounded-2xl`}>
//             <span className="text-center text-gray-200 text-nowrap">
//                 Finding this useful?{" "}
//                 <a
//                     href="https://forms.`gl`e/SxrFyLQ1HedQcLLC7"
//                     className="underline text-link"
//                     target="_blank"
//                     rel="noopener noreferrer">
//                     Help improve it!
//                 </a>
//             </span>
//             <button
//                 className="flex items-center justify-center px-2 cursor-pointer aspect-square bg-neutral-900/50 rounded-2xl hover:bg-neutral-900"
//                 onClick={() => setVisible(false)}>
//                 {" "}
//                 <FontAwesomeIcon icon={faXmark} size="sm" />
//             </button>
//         </div>
//     );
// }

function App() {
    useEffect(() => {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://bustimes.org/liveries.1.css";
        document.head.appendChild(link);
    }, []);

    const [isOpen, setIsOpen] = useState(false);

    const showAppNav = useShowAppNav();
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
    }, []);

    return (
        <ErrorBoundary fallback={<Error />}>
            <MotionConfig reducedMotion="user">
                <BrowserRouter>
                    <Canonical />
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
                                            <b>nextbus.fly.dev</b> because that
                                            address is no longer in use.
                                        </p>
                                        <p className="mt-2 text-neutral-200/80">
                                            Please use{" "}
                                            <b>nextbus.orbitix.dev</b> from now
                                            on, and update any bookmarks you may
                                            have.
                                        </p>
                                        <div className="mt-4">
                                            <div
                                                className="inline-flex cursor-pointer items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm/6 font-semibold text-white  transition-all focus:not-data-focus:outline-none hover:bg-primary-700 data-focus:outline data-focus:outline-white data-hover:bg-gray-600 data-open:bg-gray-700"
                                                onClick={() =>
                                                    setIsOpen(false)
                                                }>
                                                Got it, thanks!
                                            </div>
                                        </div>
                                    </DialogPanel>
                                </div>
                            </div>
                        </Dialog>
                        {/* <UsefulBanner /> */}
                        <Routes>
                            <Route element={<Layout />}>
                                <Route path="*" element={<NotFound />} />
                                <Route path="/" element={<Home />} />
                                <Route
                                    path="tutorials/install"
                                    element={<InstallHelp />}
                                />
                                <Route
                                    path="/privacy"
                                    element={<PrivacyPolicy />}
                                />
                                <Route path="/terms" element={<Terms />} />
                                <Route path="/data" element={<Data />} />
                                <Route path="/stats" element={<StatsPage />} />
                                <Route
                                    path="/search"
                                    element={<SearchPage />}
                                />
                                <Route path="/map" element={<Map />} />
                                <Route
                                    path="/regions"
                                    element={<RegionsPage />}
                                />
                                <Route
                                    path="/region/:region_id"
                                    element={<RegionPage />}
                                />
                                <Route
                                    path="/adminarea/:admin_area_id"
                                    element={<AdminAreaPage />}
                                />
                                <Route
                                    path="/district/:district_id"
                                    element={<DistrictPage />}
                                />
                                <Route
                                    path="/locality/:locality_id"
                                    element={<LocalityPage />}
                                />
                                <Route
                                    path="/sources"
                                    element={<SourcesPage />}
                                />
                                <Route
                                    path="/sources/:source_id"
                                    element={<DataSourcePage />}
                                />
                                <Route path="/buses" element={<BusPage />} />
                                <Route
                                    path="/buses/journeysearch/:locality/:datetime?"
                                    element={<PossibleJourneysPage />}
                                />
                                <Route
                                    path="/buses/stops/:stop_id"
                                    element={<DeparturePage />}
                                />
                                <Route
                                    path="/buses/predictions"
                                    element={<PredictionsPage />}
                                />
                                <Route
                                    path="/buses/:bus_id"
                                    element={<LiveJourneyPage />}
                                />
                                <Route
                                    path="/buses/dbjourneys/:journey_id"
                                    element={<JourneyPage />}
                                />
                                <Route
                                    path="/buses/trips/:trip_id"
                                    element={<JourneyPage />}
                                />
                                <Route
                                    path="buses/services/:service_id"
                                    element={<ServicePage />}
                                />
                                <Route
                                    path="/trains"
                                    element={<TrainsDashboard />}
                                />
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
            </MotionConfig>
        </ErrorBoundary>
    );
}

export default App;

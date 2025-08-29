import React, { useEffect } from "react";
// import DepartureBoard from "../components/DepartureBoard";
// import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import StopMap from "../components/StopMap";
import TrainSearchCard from "../components/TrainSearch";
import { Card } from "../components/ui/Card";
import { getCurrentPosition } from "../utils/locations";
import type { ServiceInfo } from "../models/ServiceInfo";
import getNearby from "../utils/getNearby";
import type { StationData } from "uk-railway-stations";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faBus,
    faTrain,
    faTrainSubway,
} from "@fortawesome/free-solid-svg-icons";
import { getClosestStop } from "../utils/closestStop";
import { StationCombobox } from "../components/StationCombobox";

const Home: React.FC = () => {
    // const navigate = useNavigate();

    const [services, setServices] = React.useState<ServiceInfo[]>([]);
    const [closestStop, setClosestStop] = React.useState<string | null>(null);
    const [selectedStation, setSelectedStation] =
        React.useState<StationData | null>(null);
    const [showStop, setShowStop] = React.useState(false);

    useEffect(() => {
        document.title = "nextbus";
    }, []);

    useEffect(() => {
        const fetchServices = async () => {
            try {
                const pos = await getCurrentPosition();
                // const fakeCoords = [51.08087, -1.15937];

                const closestStop = await getClosestStop([
                    pos.coords.latitude,
                    pos.coords.longitude,
                ]);
                // const closestStop = await getClosestStop(fakeCoords);
                if (closestStop) {
                    console.log(
                        "closest stop",
                        closestStop,
                        "distance",
                        closestStop.dist
                    );
                    if (closestStop.dist < 8 && closestStop.stop_id) {
                        // 8 meters
                        console.log("stop is close enough, showing popup");
                        setClosestStop(closestStop.stop_id);
                        setShowStop(true);
                    }
                }

                const services = await getNearby([
                    pos.coords.latitude,
                    pos.coords.longitude,
                ]);

                if (services) {
                    setServices(services);
                }
            } catch (error) {
                console.log("uh oh", error);
            }
        };

        fetchServices();
    }, []);

    return (
        <div>
            <div className="flex flex-col items-center justify-center gap-6">
                <div className="flex flex-col items-center justify-center gap-5 pt-0 p-7">
                    <div className="flex flex-row items-center gap-1">
                        <span className="text-5xl font-black text-center pt-7">
                            nextbus
                        </span>
                        <span className="text-xl font-bold h-fit text-sky-500">
                            beta
                        </span>
                    </div>

                    {showStop && closestStop && (
                        <div className="flex flex-col items-center gap-2 p-3 bg-neutral-800 rounded-[24px]">
                            <span className="px-5 font-semibold text-center text-neutral-300 text">
                                It looks like you're at a bus stop!
                                <br /> Would you like to see the departures?
                            </span>
                            <div className="flex flex-row w-full gap-2">
                                <button
                                    className="w-full p-2 mt-2 font-semibold text-white transition-all cursor-pointer bg-neutral-600 rounded-xl hover:bg-neutral-700"
                                    onClick={() => {
                                        setShowStop(false);
                                    }}>
                                    No, thanks.
                                </button>
                                <button
                                    className="w-full p-2 mt-2 font-semibold text-white transition-all bg-blue-600 cursor-pointer text-nowrap rounded-xl hover:bg-blue-700"
                                    onClick={() => {
                                        setShowStop(false);
                                        window.location.href = `/departures/${closestStop}`;
                                    }}>
                                    Yes, show me!{" "}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* <div className="flex items-center w-full py-2 rounded-full shadow-2xl border-1 border-neutral-800 bg-neutral-900">
                        <div className="ml-4 mr-2 text-gray-500">
                            <FontAwesomeIcon
                                icon={faMagnifyingGlass}
                                width={16}
                                height={16}
                            />
                        </div>

                        <input
                            type="text"
                            placeholder="Enter Stop Code (e.g. 1990PH130449)"
                            className="flex-grow font-medium placeholder-gray-400 bg-transparent focus:outline-none"
                        />
                        <button className="mr-2 px-4 py-1.5 font-bold text-black rounded-full bg-teal-400  transition cursor-pointer shadow-[0_0_5px_1px_rgba(0,187,167,0.5)] hover:shadow-[0_0_10px_2px_rgba(0,187,167,0.6)]">
                            Go
                        </button>
                    </div> */}
                    {/* <span className="text-xl font-bold text-center">
                        See your nearest bus stop:
                    </span> */}
                    {/* <DepartureBoard stop_id="" closest={true}></DepartureBoard> */}

                    <div className="flex flex-row flex-wrap items-start justify-center w-full gap-5 p-5">
                        <Card className="max-w-[90vw] flex flex-col items-center gap-2">
                            <div className="flex flex-col items-center justify-center">
                                <span className="text-xl font-bold text-center">
                                    Your bus dashboard
                                </span>
                                <span className="text-sm font-semibold text-center text-neutral-500">
                                    (favorite stops, etc.)
                                </span>
                            </div>
                            <button
                                className="w-full p-2 px-5 mt-2 font-semibold text-white transition-all bg-blue-600 cursor-pointer rounded-xl hover:bg-blue-700"
                                onClick={() => {
                                    window.location.href = `/buses`;
                                }}>
                                Bus Dashboard <FontAwesomeIcon icon={faBus} />
                            </button>
                        </Card>

                        <Card className="max-w-[90vw] flex flex-col items-center gap-2">
                            <span className="text-xl font-bold text-center">
                                Your nearby bus services
                            </span>
                            <div className="flex flex-row items-center justify-center gap-2 overflow-x-auto">
                                {services.length === 0 && (
                                    <span className="text-sm text-neutral-400">
                                        No nearby services found.
                                    </span>
                                )}
                                {services.map((service) => (
                                    <a
                                        key={service.id}
                                        className="flex items-center justify-center px-3 py-1 text-lg font-bold text-center cursor-pointer rounded-xl bg-neutral-800/50"
                                        href={`/services/${service.id}`}>
                                        {service.line_name}
                                    </a>
                                ))}
                            </div>
                        </Card>

                        <TrainSearchCard></TrainSearchCard>

                        <Card className="flex flex-col items-center justify-center gap-3 p-[12px] min-w-[250px]">
                            <div className="flex flex-col items-center justify-center">
                                <span className="text-xl font-bold text-center">
                                    Find a station
                                </span>
                                <span className="text-xs text-center text-neutral-600">
                                    yes i know its a bus website but trains are
                                    cool
                                </span>
                            </div>
                            <StationCombobox
                                placeholder="to station..."
                                value={selectedStation}
                                onChange={setSelectedStation}
                            />
                            <button
                                className={`w-full p-2 px-5 mt-2 font-semibold text-white bg-blue-600 transition-all rounded-xl ${
                                    selectedStation
                                        ? "cursor-pointer hover:bg-blue-700"
                                        : "brightness-50 cursor-not-allowed"
                                }`}
                                disabled={!selectedStation}
                                onClick={() => {
                                    if (selectedStation) {
                                        window.location.href = `/stations/${selectedStation.crsCode}`;
                                    }
                                }}>
                                Go to Trains{" "}
                                <FontAwesomeIcon icon={faTrainSubway} />
                            </button>
                        </Card>
                    </div>

                    <span className="text-xl font-bold text-center">
                        Or find your stop on the map:
                    </span>

                    <StopMap />
                </div>
                {/* <div className="flex flex-row flex-wrap items-center justify-center gap-5 p-5 md:gap-15">
                    <span className="text-3xl font-bold text-center md:text-4xl md:w-80">
                        Departure Boards for Every Operator
                    </span>
                    <DepartureBoard stop_id="1990PH130449"></DepartureBoard>
                </div> */}
            </div>
        </div>
    );
};

export default Home;

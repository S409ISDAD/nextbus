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
    faTrainSubway,
    faWarning,
} from "@fortawesome/free-solid-svg-icons";
import { getClosestStop } from "../utils/closestStop";
import { StationCombobox } from "../components/StationCombobox";

const TrainsDashboard: React.FC = () => {
    // const navigate = useNavigate();

    const [services, setServices] = React.useState<ServiceInfo[]>([]);
    const [closestStop, setClosestStop] = React.useState<string | null>(null);
    const [selectedStation, setSelectedStation] =
        React.useState<StationData | null>(null);
    const [showStop, setShowStop] = React.useState(false);

    useEffect(() => {
        document.title = "trains | nextbus";
    }, []);

    return (
        <div>
            <div className="flex flex-col items-center justify-center gap-6">
                <div className="flex flex-col items-center justify-center gap-5 pt-0 p-7">
                    <div className="flex flex-row flex-wrap items-start justify-center w-full gap-5 p-5">
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
                                placeholder="enter station..."
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
                        <TrainSearchCard></TrainSearchCard>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TrainsDashboard;

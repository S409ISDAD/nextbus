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
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBus } from "@fortawesome/free-solid-svg-icons";

const Home: React.FC = () => {
    // const navigate = useNavigate();

    const [services, setServices] = React.useState<ServiceInfo[]>([]);

    useEffect(() => {
        document.title = "nextbus";
    }, []);

    useEffect(() => {
        let interval: any;

        const fetchServices = async () => {
            try {
                const pos = await getCurrentPosition();

                const services = await getNearby([
                    pos.coords.latitude,
                    pos.coords.longitude,
                ]);

                if (services) {
                    setServices(services);
                }
            } catch {
                console.log("uh oh");
            } finally {
                // setLoading(false);
            }
        };

        fetchServices();

        return () => {
            clearInterval(interval);
        };
    }, []);

    return (
        <div>
            <div className="flex flex-col items-center justify-center gap-6">
                <div className="flex flex-col items-center justify-center gap-5 pt-0 p-7">
                    <span className="text-5xl font-black text-center pt-7">
                        nextbus
                    </span>

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

                    <div className="flex flex-row flex-wrap items-start justify-center w-full p-5 gap-y-3 gap-x-10">
                        <div className="flex flex-col items-center justify-center gap-3 min-w-[350px] ">
                            <span className="text-xl font-bold text-center">
                                Find your train
                            </span>
                            <span className="text-xs text-center text-neutral-600">
                                yes i know its a bus website but trains are cool
                            </span>
                            <TrainSearchCard></TrainSearchCard>
                        </div>
                        <div className="flex flex-col items-center justify-center gap-3">
                            <span className="text-xl font-bold text-center">
                                See nearby bus services
                            </span>
                            <Card className="max-w-[90vw] flex flex-col items-center gap-2">
                                <span className="w-full text-center">
                                    Nearby Services
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
                        </div>
                        <div className="flex flex-col items-center justify-center gap-3">
                            <span className="text-xl font-bold text-center">
                                Go to the bus dashboard
                            </span>
                            <button
                                className="w-full p-2 mt-2 font-semibold text-white transition-all bg-blue-500 cursor-pointer rounded-xl hover:bg-blue-600"
                                onClick={() => {
                                    window.location.href = `/buses`;
                                }}>
                                Bus Dashboard <FontAwesomeIcon icon={faBus} />
                            </button>
                        </div>
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

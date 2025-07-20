import React, { useEffect } from "react";
// import DepartureBoard from "../components/DepartureBoard";
// import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import StopMap from "../components/StopMap";
import DepartureBoard from "../components/DepartureBoard";

const Home: React.FC = () => {
    useEffect(() => {
        document.title = "nextbus";
    }, []);
    return (
        <div>
            <div className="flex flex-col items-center justify-center gap-6">
                <div className="flex flex-col items-center justify-center gap-5 p-7">
                    {/* <span className="text-5xl font-black text-center">
                        The best way to get the bus.
                    </span> */}

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
                    <span className="text-xl font-bold text-center">
                        See your nearest bus stop:
                    </span>
                    <DepartureBoard stop_id="" closest={true}></DepartureBoard>

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

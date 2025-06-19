import React, { useEffect } from "react";
import DepartureBoard from "../components/DepartureBoard";
import { Card } from "../components/ui/Card";

const BusPage: React.FC = () => {
    useEffect(() => {
        document.title = "Bus Page";
    }, []);
    return (
        <div className="md:mx-40">
            <div className="flex flex-row flex-wrap items-center justify-center gap-3 p-4">
                <Card className="flex flex-col gap-2 p-2 bg-teal-950 rounded-4xl">
                    <span className="mt-1 ml-3 text-2xl font-bold">
                        Your Stops
                    </span>
                    <div className="flex flex-row gap-2 overflow-x-auto max-w-[90vw]">
                        <DepartureBoard
                            stop_id=""
                            closest={true}></DepartureBoard>
                        <DepartureBoard stop_id="1900HA110364"></DepartureBoard>
                    </div>
                </Card>
                <DepartureBoard stop_id="1900HA020369"></DepartureBoard>
                <DepartureBoard stop_id="149000007530"></DepartureBoard>
            </div>
        </div>
    );
};

export default BusPage;

import React from "react";
import DepartureBoard from "../components/DepartureBoard";

const BusPage: React.FC = () => {
    return (
        <div className="md:mx-40">
            <div className="flex flex-row flex-wrap items-center justify-center gap-3 p-4">
                <DepartureBoard stop_id="" closest={true}></DepartureBoard>
                <DepartureBoard stop_id="149000007530"></DepartureBoard>
                <DepartureBoard stop_id="1900HA110364"></DepartureBoard>
            </div>
        </div>
    );
};

export default BusPage;

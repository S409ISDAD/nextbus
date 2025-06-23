import React, { useEffect } from "react";
import DepartureBoard from "../components/DepartureBoard";

const BusPage: React.FC = () => {
    useEffect(() => {
        document.title = "Bus Page";
    }, []);
    return (
        <div className="flex flex-row flex-wrap items-center justify-center gap-3 p-4">
            <DepartureBoard stop_id="" closest={true}></DepartureBoard>
            <DepartureBoard stop_id="1900HA110364"></DepartureBoard>
            <DepartureBoard stop_id="1900HA020369"></DepartureBoard>
            <DepartureBoard stop_id="149000007530"></DepartureBoard>
        </div>
    );
};

export default BusPage;

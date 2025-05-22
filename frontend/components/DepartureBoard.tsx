import { useEffect, useState } from "react";
import api from "../src/api";
import type { Bus } from "../models/Bus";

function DepartureBoard(stop_id) {
    const [buses, setBuses] = useState<Bus[]>([]);
    const [stop, setStop] = useState<String>("");
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        const departures = async () => {
            try {
                const response = await api.get<Bus[]>(
                    "/departures/?stop_id=1900HA110102"
                );
                setBuses(response.data["buses"]);
                setStop(response.data["stop_name"]);
                console.log(response);
            } catch (error) {
                console.error("failed to get departures", error);
            } finally {
                setLoading(false);
            }
        };
        departures();
    }, []);

    if (loading) {
        return <p>loading</p>;
    }

    return (
        <div>
            <h2>Departures from {stop}</h2>
            <ul>
                {buses.map((bus) => (
                    <li key={bus.reg}>
                        <div>
                            <h4>
                                {bus.service.line_name} to {bus.destination}
                            </h4>
                            <p>
                                {bus.expected} - {bus.lateness}
                            </p>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default DepartureBoard;

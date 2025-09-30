import { useEffect, useState } from "react";
import { Card } from "./ui/Card";
import { getTimetable } from "../utils/getTimetable";
import type { Timetable } from "../models/Timetable";
import { useNavigate } from "react-router";

type TimetableProps = {
    service_id: number;
    inbound?: boolean;
};

export default function Timetable({
    service_id,
    inbound = true,
}: TimetableProps) {
    const [timetable, setTimetable] = useState<Timetable>();
    const [showAll, setShowAll] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchTimetable = async () => {
            const data = await getTimetable(service_id, inbound);
            if (data) {
                setTimetable(data);
            }
        };

        fetchTimetable();
    }, [service_id, inbound]);

    return (
        <>
            <div className="flex items-center p-2">
                <input
                    type="checkbox"
                    id="showAll"
                    checked={showAll}
                    onChange={() => setShowAll((prev) => !prev)}
                    className="mr-2 rounded-lg cursor-pointer accent-blue-600"
                />
                <span className="text-sm">Show all stops</span>
            </div>
            <div className="overflow-auto border shadow rounded-xl border-neutral-600">
                <table className="w-full text-sm border-collapse table-auto">
                    <thead className="sticky top-0 z-10 text-white bg-neutral-800">
                        <tr>
                            {/* <th className="sticky left-0 z-20 p-2 text-left bg-neutral-800">
                    Stop
                </th>
                {timetable?.journeys.map((j) => (
                    <th key={j.id} className="px-3 py-2 text-center">
                    {j.start_time}
                    </th>
                ))} */}
                        </tr>
                    </thead>
                    <tbody>
                        {timetable?.stops
                            .filter(
                                (stop) =>
                                    showAll || stop.timing_status === "PTP"
                            )
                            .map((stop, i) => (
                                <tr
                                    key={stop.id || stop.name}
                                    className={
                                        i % 2 === 0
                                            ? "bg-neutral-900"
                                            : "bg-neutral-800"
                                    }>
                                    <td
                                        className="sticky left-0 z-10 p-2 py-1 overflow-hidden font-medium text-blue-400 underline cursor-poiner bg-inherit text-nowrap max-w-40 text-ellipsis"
                                        style={{
                                            paddingLeft:
                                                stop.timing_status !== "PTP"
                                                    ? "20px"
                                                    : "",
                                        }}
                                        onClick={() => {
                                            navigate(`/buses/stops/${stop.id}`);
                                        }}>
                                        {stop.name}
                                    </td>
                                    {timetable.journeys.map((journey, j) => {
                                        // Find the correct index for this stop in journey.times
                                        const stopIndex =
                                            timetable.stops.findIndex(
                                                (s) => s.id === stop.id
                                            );
                                        const time = journey.times[stopIndex];
                                        return (
                                            <td
                                                key={j}
                                                className="p-2 py-1 text-center">
                                                {time ?? ""}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                    </tbody>
                </table>
            </div>
        </>
    );
}

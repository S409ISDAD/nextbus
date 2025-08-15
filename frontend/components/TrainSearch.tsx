import { useEffect, useMemo, useState } from "react";
import { Card } from "./ui/Card";
import StationsListJSON from "uk-railway-stations";
import type { StationData } from "uk-railway-stations";
import {
    Combobox,
    ComboboxInput,
    ComboboxOption,
    ComboboxOptions,
} from "@headlessui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowsAltV } from "@fortawesome/free-solid-svg-icons";
import Fuse from "fuse.js";

export default function TrainSearchCard() {
    const [fromQuery, setFromQuery] = useState("");
    const [toQuery, setToQuery] = useState("");
    const [selectedFrom, setSelectedFrom] = useState<StationData | null>(null);
    const [selectedTo, setSelectedTo] = useState<StationData | null>(null);
    const [msg, setMsg] = useState("");

    const stations = StationsListJSON;

    // Make a single Fuse instance for all stations
    const fuse = useMemo(
        () =>
            new Fuse(stations, {
                keys: ["stationName", "crsCode"],
                threshold: 0.4, // lower is stricter
            }),
        [stations]
    );

    // Debounced queries
    const [debouncedFrom, setDebouncedFrom] = useState(fromQuery);
    const [debouncedTo, setDebouncedTo] = useState(toQuery);

    useEffect(() => {
        const handler = setTimeout(() => setDebouncedFrom(fromQuery), 150);
        return () => clearTimeout(handler);
    }, [fromQuery]);

    useEffect(() => {
        const handler = setTimeout(() => setDebouncedTo(toQuery), 150);
        return () => clearTimeout(handler);
    }, [toQuery]);

    const filteredFrom = useMemo(() => {
        if (debouncedFrom === "") return [];
        if (debouncedFrom.length < 3) {
            return [];
        }
        return fuse.search(debouncedFrom, { limit: 5 }).map((r) => r.item);
    }, [debouncedFrom, fuse, stations]);

    const filteredTo = useMemo(() => {
        if (debouncedTo === "") return [];
        if (debouncedTo.length < 3) {
            return [];
        }
        return fuse.search(debouncedTo, { limit: 5 }).map((r) => r.item);
    }, [debouncedTo, fuse, stations]);

    return (
        <Card className="flex flex-col items-center justify-center gap-3 p-[12px] w-full">
            <span className="flex flex-col items-center text-lg font-semibold text-neutral-300">
                Enter your journey details
                <span className="text-xs font-semibold text-center text-neutral-400">
                    direct trains only! no changes or transfers.
                </span>
                <span className="text-xs font-semibold text-center text-neutral-400">
                    only upcoming departures are shown.
                </span>
            </span>

            {msg && <span className="font-semibold text-red-500">{msg}</span>}

            <div className="flex flex-row w-full gap-[12px]">
                <div className="flex flex-col w-full gap-4">
                    {/* FROM */}
                    <Combobox value={selectedFrom} onChange={setSelectedFrom}>
                        <div className="relative">
                            <ComboboxInput
                                className="w-full p-2 font-semibold border border-neutral-700 rounded-xl"
                                onChange={(e) => setFromQuery(e.target.value)}
                                displayValue={(station: StationData) =>
                                    station
                                        ? `${station.stationName} (${station.crsCode})`
                                        : ""
                                }
                                placeholder="from station..."
                            />
                            <ComboboxOptions className="absolute z-[9999999] w-full overflow-auto border shadow-lg max-h-60 rounded-xl border-neutral-700 bg-neutral-900">
                                {filteredFrom.map((s) => (
                                    <ComboboxOption
                                        key={s.crsCode}
                                        value={s}
                                        className="p-2 cursor-pointer hover:bg-neutral-800">
                                        {s.stationName} ({s.crsCode})
                                    </ComboboxOption>
                                ))}
                            </ComboboxOptions>
                        </div>
                    </Combobox>
                    {/* TO */}
                    <Combobox value={selectedTo} onChange={setSelectedTo}>
                        <div className="relative">
                            <ComboboxInput
                                className="w-full p-2 font-semibold border border-neutral-700 rounded-xl"
                                onChange={(e) => setToQuery(e.target.value)}
                                displayValue={(station: StationData) =>
                                    station
                                        ? `${station.stationName} (${station.crsCode})`
                                        : ""
                                }
                                placeholder="to station..."
                            />
                            <ComboboxOptions className="absolute z-[9999999] w-full overflow-auto border shadow-lg max-h-60 rounded-xl border-neutral-700 bg-neutral-900">
                                {filteredTo.map((s) => (
                                    <ComboboxOption
                                        key={s.crsCode}
                                        value={s}
                                        className="p-2 cursor-pointer hover:bg-neutral-800">
                                        {s.stationName} ({s.crsCode})
                                    </ComboboxOption>
                                ))}
                            </ComboboxOptions>
                        </div>
                    </Combobox>
                </div>
                <div className="flex items-center justify-center">
                    <button
                        type="button"
                        aria-label="Flip stations"
                        className="flex items-center justify-center p-2 transition-colors border rounded-full bg-neutral-800 hover:bg-neutral-700 border-neutral-700"
                        onClick={() => {
                            setSelectedFrom(selectedTo);
                            setSelectedTo(selectedFrom);
                            setFromQuery(
                                selectedTo
                                    ? `${selectedTo.stationName} (${selectedTo.crsCode})`
                                    : ""
                            );
                            setToQuery(
                                selectedFrom
                                    ? `${selectedFrom.stationName} (${selectedFrom.crsCode})`
                                    : ""
                            );
                            setMsg("");
                        }}>
                        <FontAwesomeIcon icon={faArrowsAltV} />
                    </button>
                </div>
            </div>
            <button
                className="w-full p-2 mt-2 font-semibold text-white transition-all bg-blue-500 cursor-pointer rounded-xl hover:bg-blue-600"
                onClick={() => {
                    if (!selectedFrom || !selectedTo) {
                        setMsg("Please select both stations.");
                        return;
                    }
                    window.location.href = `/search/trains/${selectedFrom.crsCode}/to/${selectedTo.crsCode}`;
                }}>
                Search
            </button>
        </Card>
    );
}

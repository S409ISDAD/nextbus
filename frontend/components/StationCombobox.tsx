import { useEffect, useMemo, useState } from "react";
import {
    Combobox,
    ComboboxInput,
    ComboboxOption,
    ComboboxOptions,
} from "@headlessui/react";
import type { StationData } from "uk-railway-stations";
import StationsListJSON from "uk-railway-stations";
import Fuse from "fuse.js";

type StationComboboxProps = {
    label?: string;
    placeholder?: string;
    value: StationData | null;
    onChange: (station: StationData | null) => void;
};

export function StationCombobox({
    label,
    placeholder = "Search station...",
    value,
    onChange,
}: StationComboboxProps) {
    const [query, setQuery] = useState("");

    const [debounced, setDebounced] = useState(query);
    useEffect(() => {
        const handler = setTimeout(() => setDebounced(query), 150);
        return () => clearTimeout(handler);
    }, [query]);

    const stations = StationsListJSON;
    const fuse = useMemo(
        () =>
            new Fuse(stations, {
                keys: ["stationName", "crsCode"],
                threshold: 0.4,
            }),
        [stations]
    );

    const results = useMemo(() => {
        if (debounced.length < 3) return [];
        return fuse.search(debounced, { limit: 5 }).map((r) => r.item);
    }, [debounced, fuse]);

    return (
        <div className="flex flex-col w-full">
            {label && (
                <span className="mb-1 text-sm font-semibold text-text-light">
                    {label}
                </span>
            )}
            <Combobox value={value} onChange={onChange}>
                <div className="relative">
                    <ComboboxInput
                        className="w-full p-2 font-semibold border border-neutral-700 rounded-xl"
                        onChange={(e) => setQuery(e.target.value)}
                        displayValue={(station: StationData) =>
                            station
                                ? `${station.stationName} (${station.crsCode})`
                                : ""
                        }
                        placeholder={placeholder}
                    />
                    {results.length > 0 && (
                        <ComboboxOptions className="absolute z-[9999999] w-full overflow-auto border shadow-lg max-h-60 rounded-xl border-neutral-700 bg-bg-medium">
                            {results.map((s) => (
                                <ComboboxOption
                                    key={s.crsCode}
                                    value={s}
                                    className="p-2 cursor-pointer hover:bg-bg-light">
                                    {s.stationName} ({s.crsCode})
                                </ComboboxOption>
                            ))}
                        </ComboboxOptions>
                    )}
                </div>
            </Combobox>
        </div>
    );
}

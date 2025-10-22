import { useState } from "react";
import { Card } from "./ui/Card";
import type { StationData } from "uk-railway-stations";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowsAltV } from "@fortawesome/free-solid-svg-icons";
import { StationCombobox } from "./StationCombobox";

export default function TrainSearchCard() {
    const [selectedFrom, setSelectedFrom] = useState<StationData | null>(null);
    const [selectedTo, setSelectedTo] = useState<StationData | null>(null);
    const [msg, setMsg] = useState("");

    return (
        <Card className="flex flex-col items-center justify-center gap-3 p-[12px] min-w-[350px]">
            <span className="flex flex-col items-center text-xl font-semibold text-neutral-300">
                Find your train
                <span className="text-xs font-semibold text-center text-text-light">
                    direct trains only! no changes or transfers.
                </span>
                <span className="text-xs font-semibold text-center text-text-light">
                    only upcoming departures are shown.
                </span>
            </span>

            {msg && <span className="font-semibold text-red-500">{msg}</span>}

            <div className="flex flex-row w-full gap-[12px]">
                <div className="flex flex-col w-full gap-4">
                    <StationCombobox
                        placeholder="from station..."
                        value={selectedFrom}
                        onChange={setSelectedFrom}
                    />
                    <StationCombobox
                        placeholder="to station..."
                        value={selectedTo}
                        onChange={setSelectedTo}
                    />
                </div>
                <div className="flex items-center justify-center">
                    <button
                        type="button"
                        aria-label="Flip stations"
                        className="flex items-center justify-center p-2 transition-colors border rounded-full bg-bg-light hover:bg-neutral-700 border-neutral-700"
                        onClick={() => {
                            setSelectedFrom(selectedTo);
                            setSelectedTo(selectedFrom);
                            setMsg("");
                        }}>
                        <FontAwesomeIcon icon={faArrowsAltV} />
                    </button>
                </div>
            </div>
            <button
                className={`w-full p-2 mt-2 font-semibold text-text-dark transition-all bg-primary rounded-xl ${
                    selectedFrom && selectedTo
                        ? "cursor-pointer hover:bg-primary-700"
                        : "brightness-50 cursor-not-allowed"
                }`}
                disabled={!selectedFrom || !selectedTo}
                onClick={() => {
                    if (!selectedFrom || !selectedTo) {
                        setMsg("Please select both stations.");
                        return;
                    }
                    window.location.href = `/trains/search/${selectedFrom.crsCode}/to/${selectedTo.crsCode}`;
                }}>
                Search
            </button>
        </Card>
    );
}

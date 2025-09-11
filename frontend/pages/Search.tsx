import React, { useEffect } from "react";
import doSearch from "../utils/doSearch";
import SearchBar from "../components/SearchBar";
import type { Search } from "../models/Search";
import { useNavigate, useParams } from "react-router";
import { Card } from "../components/ui/Card";

const Home: React.FC = () => {
    const navigate = useNavigate();
    const [results, setResults] = React.useState<Search>();
    const { query } = useParams();

    useEffect(() => {
        document.title = `"${query}" | nextbus`;
        if (!query) return;
        const getSearch = async () => {
            try {
                console.log("searching for", query);
                const searchResults = await doSearch(query);
                if (searchResults) {
                    setResults(searchResults);
                }
            } catch (error) {
                console.log("uh oh", error);
            }
        };

        getSearch();
    }, [query]);

    return (
        <div className="flex flex-col items-center justify-center w-full gap-6 p-8">
            <span className="text-4xl font-bold">Search nextbus</span>
            <SearchBar query={query} />
            {query && (
                <div className="flex flex-col w-full max-w-3xl gap-4 mt-4">
                    {results?.lines.length === 0 &&
                    results.services.length === 0 &&
                    results.stops.length === 0 ? (
                        <span className="text-xl font-medium text-center text-gray-400">
                            No results found
                        </span>
                    ) : (
                        <>
                            <div className="flex flex-col gap-2">
                                <span className="text-2xl font-bold">
                                    Lines
                                </span>
                                {results?.lines.length === 0 && (
                                    <span className="text-sm text-gray-400">
                                        No lines found.
                                    </span>
                                )}
                                {results?.lines.map((line) => (
                                    <Card
                                        key={line.id}
                                        className="flex flex-col cursor-pointer"
                                        onClick={() => {
                                            navigate(
                                                line.bt_service_id
                                                    ? `/buses/services/${line.bt_service_id}`
                                                    : ""
                                            );
                                        }}>
                                        <span className="text-lg font-bold">
                                            {line.line_name}
                                        </span>
                                        <span className="text-sm text-gray-400">
                                            {line.inbound_description}
                                        </span>
                                    </Card>
                                ))}
                            </div>
                            <div className="flex flex-col gap-2">
                                <span className="text-2xl font-bold">
                                    Services
                                </span>
                                {results?.services.length === 0 && (
                                    <span className="text-sm text-gray-400">
                                        No services found.
                                    </span>
                                )}
                                {results?.services.map((service) => (
                                    <Card
                                        key={service.service_code}
                                        className="flex flex-col cursor-pointer">
                                        <span className="text-lg font-bold">
                                            {service.line_names} -{" "}
                                            {service.description}
                                        </span>
                                        <span className="text-sm text-gray-400">
                                            Via: {service.vias}
                                        </span>
                                    </Card>
                                ))}
                            </div>
                            <div className="flex flex-col gap-2">
                                <span className="text-2xl font-bold">
                                    Stops
                                </span>
                                {results?.stops.length === 0 && (
                                    <span className="text-sm text-gray-400">
                                        No stops found.
                                    </span>
                                )}
                                {results?.stops.map((stop) => (
                                    <Card
                                        key={stop.atco_code}
                                        className="flex flex-col cursor-pointer"
                                        onClick={() => {
                                            navigate(
                                                `/buses/stops/${stop.atco_code}`
                                            );
                                        }}>
                                        <span className="text-lg font-bold">
                                            {stop.common_name ??
                                                stop.common_short_name}
                                        </span>
                                        <span className="text-sm text-gray-400">
                                            {stop.indicator} - {stop.street}
                                        </span>
                                    </Card>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            )}
        </div>
    );
};

export default Home;

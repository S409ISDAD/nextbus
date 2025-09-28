import React, { useEffect } from "react";
import doSearch from "../utils/doSearch";
import SearchBar from "../components/SearchBar";
import type { Search } from "../models/Search";
import { useNavigate, useParams } from "react-router";

const SearchPage: React.FC = () => {
    const navigate = useNavigate();
    const [results, setResults] = React.useState<Search>();
    const [loading, setLoading] = React.useState(false);
    const [tab, setTab] = React.useState<"services" | "places">("services");
    const { query } = useParams();

    useEffect(() => {
        document.title = `"${query ?? "search"}" | nextbus`;
        if (!query) return;
        const getSearch = async () => {
            try {
                console.log("searching for", query);
                setLoading(true);
                const searchResults = await doSearch(query);
                setLoading(false);
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
        <div className="flex flex-col items-center justify-center w-full p-8 pb-0">
            <span className="text-4xl font-bold">Search nextbus</span>
            <SearchBar query={query} className="my-6" />
            <div className="flex flex-row justify-center gap-4 mb-4">
                <button
                    className={`px-4 py-2 text-lg font-semibold rounded-xl transition-all duration-150 cursor-pointer ${
                        tab === "services"
                            ? " bg-neutral-800 text-blue-400 scale-105"
                            : " bg-neutral-900 text-neutral-400 hover:text-blue-300"
                    }`}
                    onClick={() => setTab("services")}
                    aria-selected={tab === "services"}>
                    {results?.services.length} Services
                </button>
                <button
                    className={`px-4 py-2 text-lg font-semibold rounded-xl transition-all duration-150 cursor-pointer ${
                        tab === "places"
                            ? " bg-neutral-800 text-blue-400 scale-105"
                            : " bg-neutral-900 text-neutral-400 hover:text-blue-300"
                    }`}
                    onClick={() => setTab("places")}
                    aria-selected={tab === "places"}>
                    {results?.localities.length} Places
                </button>
            </div>
            {loading && (
                <span className="mb-5 text-xl font-medium text-center text-gray-400">
                    Loading...
                </span>
            )}
            {query && !loading && (
                <div className="flex flex-col w-full max-w-3xl gap-4">
                    {tab === "services" ? (
                        <div className="flex flex-col gap-2">
                            {results?.services.length === 0 ? (
                                <span className="w-full mb-5 text-sm text-center text-gray-400">
                                    No services found.
                                </span>
                            ) : (
                                <div className="mb-8">
                                    {results?.services.map((service, idx) => (
                                        <>
                                            <div className="flex items-center gap-2 mb-0.5">
                                                <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                                <span className="text-[10px] text-neutral-600">
                                                    nextbus
                                                </span>
                                                <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                            </div>
                                            <div
                                                key={service.service_id}
                                                className="flex flex-col cursor-pointer"
                                                onClick={() => {
                                                    navigate(
                                                        `/buses/services/${service.service_id}`
                                                    );
                                                }}>
                                                <div className="flex flex-row items-stretch mb-1">
                                                    <div className="flex items-center px-3 py-1 bg-blue-700 rounded-l-2xl">
                                                        <span className="flex items-center justify-center text-xl font-bold text-center">
                                                            {service.line_name}
                                                        </span>
                                                    </div>
                                                    <div className="flex flex-col justify-center px-3 bg-neutral-800/50 rounded-r-2xl">
                                                        <span className="font-semibold text">
                                                            {
                                                                service.description
                                                            }
                                                        </span>
                                                    </div>
                                                </div>
                                                <span className="text-sm text-gray-400">
                                                    {service.operator}
                                                </span>
                                                {service.vias && (
                                                    <span className="text-sm text-gray-400">
                                                        via {service.vias}
                                                    </span>
                                                )}
                                            </div>
                                            {idx ===
                                                results.services.length - 1 && (
                                                <div className="flex items-center gap-2 mb-0.5">
                                                    <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                                    <span className="text-[10px] text-neutral-600">
                                                        nextbus
                                                    </span>
                                                    <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                                </div>
                                            )}
                                        </>
                                    ))}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col">
                            {results?.localities.length === 0 ? (
                                <span className="w-full mb-5 text-sm text-center text-gray-400">
                                    No places found.
                                </span>
                            ) : (
                                <div className="gap-4 mb-8 columns-2 sm:columns-3">
                                    {results?.localities.map((locality) => (
                                        <div
                                            key={locality.id}
                                            className="flex flex-col mb-2 cursor-pointer break-inside-avoid"
                                            onClick={() =>
                                                navigate(
                                                    `/locality/${locality.id}`
                                                )
                                            }>
                                            <span className="underline text-sky-500">
                                                {locality.name}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default SearchPage;

import React, {useEffect} from "react";
import doSearch from "../utils/doSearch";
import SearchBar from "../components/SearchBar";
import type {Search} from "../models/Search";
import {useNavigate, useParams} from "react-router";

const SearchPage: React.FC = () => {
    const navigate = useNavigate();
    const [results, setResults] = React.useState<Search>();
    const [loading, setLoading] = React.useState(false);
    const {query} = useParams();

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
        <div className="flex flex-col items-center justify-center w-full gap-6 p-8">
            <span className="text-4xl font-bold">Search nextbus</span>
            <SearchBar query={query}/>
            {loading && (
                <span className="text-xl font-medium text-center text-gray-400">
                    Loading...
                </span>
            )}
            {query && !loading && (
                <div className="flex flex-col w-full max-w-3xl gap-4 mt-4">
                    {results?.lines.length === 0 &&
                    results.localities.length === 0 ? (
                        <span className="text-xl font-medium text-center text-gray-400">
                            No results found
                        </span>
                    ) : (
                        <>
                            <div className="flex flex-col gap-2">
                                <span className="text-2xl font-bold">
                                    {results?.lines.length} Services
                                </span>
                                {results?.lines.length === 0 && (
                                    <span className="text-sm text-gray-400">
                                        No services found.
                                    </span>
                                )}

                                {results?.lines.map((line, idx) => (
                                    <>
                                        <div className="flex items-center gap-2 mb-0.5">
                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                            <span className="text-[10px] text-neutral-600">
                                                nextbus
                                            </span>
                                            <div className="flex-grow border-t border-dashed border-neutral-600"></div>
                                        </div>
                                        <div
                                            key={line.line_id}
                                            className="flex flex-col cursor-pointer"
                                            onClick={() => {
                                                navigate(
                                                    `/buses/lines/${line.line_id}`
                                                );
                                            }}>
                                            <div className="flex flex-row items-stretch mb-1">
                                                <div className="flex items-center px-3 py-1 bg-blue-700 rounded-l-2xl">
                                                    <span
                                                        className="flex items-center justify-center text-xl font-bold text-center">
                                                        {line.line_name}
                                                    </span>
                                                </div>
                                                <div
                                                    className="flex flex-col justify-center px-3 bg-neutral-800/50 rounded-r-2xl">
                                                    <span className="font-semibold text">
                                                        {line.description}
                                                    </span>
                                                </div>
                                            </div>
                                            <span className="text-sm text-gray-400">
                                                {line.vias}
                                            </span>
                                        </div>
                                        {idx === results.lines.length - 1 && (
                                            <div className="flex items-center gap-2 mb-0.5">
                                                <div
                                                    className="flex-grow border-t border-dashed border-neutral-600"></div>
                                                <span className="text-[10px] text-neutral-600">
                                                    nextbus
                                                </span>
                                                <div
                                                    className="flex-grow border-t border-dashed border-neutral-600"></div>
                                            </div>
                                        )}
                                    </>
                                ))}
                            </div>
                            <div className="flex flex-col">
                                <span className="text-2xl font-bold">
                                    {results?.localities.length} Places
                                </span>
                                <span className="text-sm text-gray-400 mb-2">
                                    (not clickable yet)
                                </span>
                                {results?.localities.length === 0 && (
                                    <span className="text-sm text-gray-400">
                                        No places found.
                                    </span>
                                )}
                                <div className="flex flex-col gap-2">
                                    {results?.localities.map((locality) => (
                                        <div
                                            key={locality.id}
                                            className="flex flex-col cursor-not-allowed w-fit"
                                            // onClick={() => {
                                            //     navigate(
                                            //         `/buses/stops/${stop.atco_code}`
                                            //     );
                                            // }}
                                        >
                                        <span className="text-neutral-300">
                                            {locality.name} {locality.qualifier_name ? `(${locality.qualifier_name})` : ""}
                                        </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}
        </div>
    );
};

export default SearchPage;

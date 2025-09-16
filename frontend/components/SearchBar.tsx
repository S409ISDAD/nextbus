import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useState } from "react";
import { useNavigate } from "react-router";
import { motion } from "framer-motion";

export default function SearchBar(queryProp?: { query?: string }) {
    const [searchQuery, setSearchQuery] = useState(queryProp?.query || "");
    const navigate = useNavigate();
    return (
        <motion.div
            layout
            key={"search-bar"}
            layoutId="search-bar"
            className="flex items-center w-[90vw] lg:w-[50%] py-2 rounded-full shadow-2xl border-1 border-neutral-800 bg-neutral-900">
            <div className="ml-4 mr-2 text-gray-500">
                <FontAwesomeIcon
                    icon={faMagnifyingGlass}
                    width={16}
                    height={16}
                />
            </div>

            <input
                type="text"
                placeholder="Search for a stop or route"
                className="flex-grow font-medium placeholder-gray-400 bg-transparent focus:outline-none"
                onChange={(e) => setSearchQuery(e.target.value)}
                value={searchQuery}
                onKeyDown={(e) => {
                    if (e.key === "Enter") {
                        navigate(`/search/${searchQuery}`);
                    }
                }}
            />
            <button
                className="mr-2 px-4 py-1.5 font-bold text-white rounded-full bg-blue-500  transition cursor-pointer shadow-[0_0_5px_1px_rgba(43,127,255,0.5)] hover:shadow-[0_0_10px_2px_rgba(43,127,255,0.6)]"
                onClick={() => {
                    navigate(`/search/${searchQuery}`);
                }}>
                Go
            </button>
        </motion.div>
    );
}

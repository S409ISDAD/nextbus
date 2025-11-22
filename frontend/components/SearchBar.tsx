import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useState } from "react";
import { useNavigate } from "react-router";
import { motion } from "framer-motion";
import { cn } from "../utils/cn";

export default function SearchBar(queryProp?: {
    query?: string;
    className?: string;
}) {
    const [searchQuery, setSearchQuery] = useState(queryProp?.query || "");
    const className = queryProp?.className || "";
    const navigate = useNavigate();
    return (
        <motion.div
            layout
            key={"search-bar"}
            layoutId="search-bar"
            className={cn(
                "flex items-center w-[90vw] lg:w-[50%] py-2 rounded-full shadow-2xl border border-neutral-800 bg-neutral-900",
                className
            )}>
            <div className="ml-4 mr-2 text-gray-500">
                <FontAwesomeIcon
                    icon={faMagnifyingGlass}
                    width={16}
                    height={16}
                />
            </div>

            <input
                type="text"
                placeholder="Search for a route or place"
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
                className="mr-2 px-4 py-1.5 font-bold text-white rounded-full bg-primary-500  transition cursor-pointer shadow-[0_0_5px_1px_var(--shadow-primary)] hover:shadow-[0_0_10px_2px_var(--shadow-primary-hover)]"
                onClick={() => {
                    navigate(`/search/${searchQuery}`);
                }}>
                Go
            </button>
        </motion.div>
    );
}

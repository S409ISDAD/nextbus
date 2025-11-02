import { Link, Outlet, useLocation, useNavigate } from "react-router";
import { isIOS, useShowAppNav, whereAmI } from "../utils/AppNav";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faBus,
    faHome,
    faMagnifyingGlass,
    faMap,
    faTrainSubway,
} from "@fortawesome/free-solid-svg-icons";
import { faDiscord } from "@fortawesome/free-brands-svg-icons";
import version from "../utils/version";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
// import ThemeToggle from "./ThemeToggle";
import { useLocalSetting } from "../src/settings";

function NavSearchBar(queryProp?: { query?: string }) {
    const [searchQuery, setSearchQuery] = useState(queryProp?.query || "");
    const navigate = useNavigate();

    return (
        <motion.div
            layout
            key={"search-bar-nav"}
            layoutId="search-bar-nav"
            className="flex items-center rounded-full shadow-2xl w-fit border-1 border-neutral-800 bg-neutral-900">
            <div className="ml-3 mr-2 text-gray-500">
                <FontAwesomeIcon
                    icon={faMagnifyingGlass}
                    width={12}
                    height={12}
                />
            </div>

            <input
                type="text"
                placeholder="Search for a route or place"
                className="flex-grow text-sm font-medium placeholder-gray-400 bg-transparent focus:outline-none"
                onChange={(e) => setSearchQuery(e.target.value)}
                value={searchQuery}
                onKeyDown={(e) => {
                    if (e.key === "Enter") {
                        navigate(`/search/${searchQuery}`);
                    }
                }}
            />
            <button
                className="mr-2 px-3 py-1 font-bold text-sm text-white rounded-full bg-primary-500  transition cursor-pointer shadow-[0_0_5px_1px_var(--shadow-primary)] hover:shadow-[0_0_10px_2px_var(--shadow-primary-hover)]"
                onClick={() => {
                    navigate(`/search/${searchQuery}`);
                }}>
                Go
            </button>
        </motion.div>
    );
}

const footer = (currentYear: number) => (
    <footer className="flex flex-row flex-wrap items-start justify-center w-full gap-2 p-3 text-sm text-gray-200 border-t-2 max-h-fit border-neutral-800">
        <span>© {currentYear} nextbus</span> ·
        <a href="/data" className="underline text-link-400 max-h-fit">
            Data Sources
        </a>
        ·
        <a href="/privacy" className="underline text-link-400 max-h-fit">
            Privacy
        </a>
        ·
        <a href="/terms" className="underline text-link-400 max-h-fit">
            Terms
        </a>
        ·
        <a href="/stats" className="underline text-link-400 max-h-fit">
            Stats
        </a>
        ·{/* <ThemeToggle /> · */}
        <a
            href="https://discord.gg/dyEmZSkwge"
            target="_blank"
            rel="noopener noreferrer">
            <FontAwesomeIcon icon={faDiscord} />
        </a>{" "}
        {/* ·
        <a
            href="https://github.com/Orbitix/nextbus"
            target="_blank"
            rel="noopener noreferrer">
            <FontAwesomeIcon icon={faGithub} />
        </a> */}
        ·<span>version {version}</span>
    </footer>
);

export default function Layout() {
    const currentYear = new Date().getFullYear();
    const showAppNav = useShowAppNav();
    const navigate = useNavigate();
    const location = useLocation();

    const [lastBusPage, setLastBusPage] = useLocalSetting(
        "lastBusPage",
        "/buses"
    );
    const [lastTrainPage, setLastTrainPage] = useLocalSetting(
        "lastTrainPage",
        "/trains"
    );

    useEffect(() => {
        // update last visited bus/train page, even if its the root
        if (location.pathname.startsWith("/buses")) {
            setLastBusPage(location.pathname);
        }
        if (location.pathname.startsWith("/trains")) {
            setLastTrainPage(location.pathname);
        }
    }, [location.pathname]);

    function handleNavClick(target: "buses" | "trains") {
        const root = `/${target}`;
        const last = target === "buses" ? lastBusPage : lastTrainPage;

        // if already inside the section, go to root
        if (location.pathname.startsWith(root)) {
            navigate(root);
        } else {
            navigate(last);
        }
    }

    if (!showAppNav) {
        return (
            <div className="h-full">
                <div className="top-0 flex justify-between p-[8px] z-[99] border-b-1 border-neutral-800 rounded-b-[24px] fixed w-full bg-[#131313] shadow-2xl md:shadow-xl">
                    <div className="flex gap-2">
                        <Link to="/">
                            <div className="flex flex-col items-center h-full mx-4">
                                <span className="font-bold text-lg/6 ">
                                    nextbus
                                </span>
                                <span className="font-semibold text-xs/2 text-link ">
                                    beta
                                </span>
                            </div>
                        </Link>

                        <Link to="/map">
                            <button className="p-2 px-3 transition-all cursor-pointer border-neutral-800 h-max rounded-2xl border-1 hover:border-primary-700 ">
                                map
                            </button>
                        </Link>
                        <Link to="/buses">
                            <button className="p-2 px-3 transition-all cursor-pointer border-neutral-800 h-max rounded-2xl border-1 hover:border-primary-700 ">
                                buses
                            </button>
                        </Link>
                        {/* <Link to="/trains">
                            <button className="p-2 px-3 transition-all cursor-pointer border-neutral-800 h-max rounded-2xl border-1 hover:border-primary-700 ">
                                trains
                            </button>
                        </Link> */}
                    </div>
                    <NavSearchBar />
                </div>
                <main>
                    <div className="h-15"></div>
                    <Outlet />
                    {whereAmI() !== "map" && footer(currentYear)}
                </main>
            </div>
        );
    } else {
        const items = [
            { name: "home", href: "/", icon: faHome },
            { name: "map", href: "/map", icon: faMap },
            { name: "buses", href: "/buses", icon: faBus },
            { name: "trains", href: "/trains", icon: faTrainSubway },
        ];
        return (
            <div className="h-full">
                <motion.div
                    whileTap={{ scale: 0.9, transition: { duration: 0.1 } }}
                    onClick={() => {
                        navigate("/search");
                    }}
                    className="fixed z-[100] bottom-22 right-4 bg-link/30 text-white rounded-full shadow-lg w-12 h-12 flex items-center justify-center transition-all"
                    aria-label="Search">
                    <span className="text-lg font-bold">
                        <FontAwesomeIcon icon={faMagnifyingGlass} />
                    </span>
                </motion.div>
                <nav
                    className="bottom-0 left-0 text-neutral-200 right-0 flex justify-around items-center p-3 z-[99] border-t border-neutral-800 rounded-t-2xl fixed w-full shadow-2xl md:shadow-xl bg-[#131313]"
                    style={isIOS() ? { paddingBottom: "20px" } : {}}>
                    {items.map((item) => {
                        const isBus = item.name === "buses";
                        const isTrain = item.name === "trains";
                        const onClick = isBus
                            ? () => handleNavClick("buses")
                            : isTrain
                            ? () => handleNavClick("trains")
                            : () => navigate(item.href);

                        return (
                            <button
                                key={item.name}
                                onClick={onClick}
                                className="flex flex-col items-center w-5 gap-1 transition-colors hover:text-white ">
                                <FontAwesomeIcon
                                    icon={item.icon}
                                    size="lg"
                                    className={`${
                                        whereAmI() == item.name
                                            ? "px-4 rounded-full bg-link/30"
                                            : ""
                                    } transition-all p-1`}
                                />
                                <span
                                    className={`${
                                        whereAmI() == item.name
                                            ? "text-primary-300 font-bold"
                                            : ""
                                    } px-2 text-xs font-semibold`}>
                                    {item.name}
                                </span>
                            </button>
                        );
                    })}
                </nav>
                <main>
                    <Outlet />
                    {whereAmI() !== "map" && footer(currentYear)}
                    <div className="h-18"></div>
                </main>
            </div>
        );
    }
}

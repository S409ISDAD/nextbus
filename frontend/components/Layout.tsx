import { Link, Outlet } from "react-router";
import Clock from "../components/Clock";
import { useShowAppNav, whereAmI } from "../utils/AppNav";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
    faBus,
    faHome,
    faMap,
    faTrainSubway,
} from "@fortawesome/free-solid-svg-icons";
import version from "../utils/version";

export default function Layout() {
    const currentYear = new Date().getFullYear();
    const showAppNav = useShowAppNav();
    if (!showAppNav) {
        return (
            <div className="h-full">
                <div className="top-0 flex justify-between p-[8px] z-[99] border-b-1 border-neutral-800 rounded-b-[24px] fixed w-full bg-[#131313] shadow-2xl md:shadow-xl">
                    <div className="flex gap-2">
                        <Link to="/">
                            <div className="flex flex-col items-center h-full mx-4">
                                <span className="font-bold text-xl/6 ">
                                    nextbus
                                </span>
                                <span className="font-semibold text-sm/2 text-sky-500 ">
                                    beta
                                </span>
                            </div>
                        </Link>

                        <Link to="/map">
                            <button className="p-2 px-3 transition-all cursor-pointer border-neutral-800 h-max rounded-2xl border-1 hover:border-blue-700 ">
                                map
                            </button>
                        </Link>
                        <Link to="/buses">
                            <button className="p-2 px-3 transition-all cursor-pointer border-neutral-800 h-max rounded-2xl border-1 hover:border-blue-700 ">
                                buses
                            </button>
                        </Link>
                        <Link to="/trains">
                            <button className="p-2 px-3 transition-all cursor-pointer border-neutral-800 h-max rounded-2xl border-1 hover:border-blue-700 ">
                                trains
                            </button>
                        </Link>
                    </div>
                    <div className="flex items-center gap-2">
                        <Clock></Clock>
                    </div>
                </div>
                <main>
                    <div className="h-15"></div>
                    <Outlet />
                    {whereAmI() !== "map" && (
                        <footer className="flex flex-row flex-wrap items-start justify-center w-full gap-2 p-3 text-sm text-gray-200 border-t-2 max-h-fit border-neutral-800">
                            <span>© {currentYear} nextbus</span> ·
                            <a
                                href="/data"
                                className="underline text-sky-400 max-h-fit">
                                Data Sources
                            </a>
                            ·
                            <a
                                href="/privacy"
                                className="underline text-sky-400 max-h-fit">
                                Privacy
                            </a>
                            ·
                            <a
                                href="/terms"
                                className="underline text-sky-400 max-h-fit">
                                Terms
                            </a>
                            ·
                            <a
                                href="/stats"
                                className="underline text-sky-400 max-h-fit">
                                Stats
                            </a>
                            ·
                            <a
                                href="https://discord.gg/dyEmZSkwge"
                                className="underline text-sky-400 max-h-fit"
                                target="_blank"
                                rel="noopener noreferrer">
                                Join the Discord!{" "}
                            </a>
                            ·<span>v{version}</span>
                        </footer>
                    )}
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
                <nav className="bottom-0 left-0 right-0 flex justify-around items-center p-3 z-[99] border-t border-neutral-800 rounded-t-2xl fixed w-full shadow-2xl md:shadow-xl bg-[#131313]">
                    {items.map((item) => (
                        <Link
                            to={item.href}
                            className="flex flex-col items-center w-5 gap-1 transition-colors hover:text-white ">
                            <FontAwesomeIcon
                                icon={item.icon}
                                size="lg"
                                className={`${
                                    whereAmI() == item.name
                                        ? "px-4 rounded-full bg-sky-500/30"
                                        : ""
                                } transition-all p-1`}
                            />
                            <span className="px-2 text-xs font-semibold">
                                {item.name}
                            </span>
                        </Link>
                    ))}
                </nav>
                <main>
                    <Outlet />
                    {whereAmI() !== "map" && (
                        <footer className="flex flex-row flex-wrap items-start justify-center w-full gap-2 p-3 text-sm text-gray-200 border-t-2 max-h-fit border-neutral-800">
                            <span>© {currentYear} nextbus</span> ·
                            <a
                                href="/data"
                                className="underline text-sky-400 max-h-fit">
                                Data Sources
                            </a>
                            ·
                            <a
                                href="/privacy"
                                className="underline text-sky-400 max-h-fit">
                                Privacy
                            </a>
                            ·
                            <a
                                href="/terms"
                                className="underline text-sky-400 max-h-fit">
                                Terms
                            </a>
                            ·
                            <a
                                href="/stats"
                                className="underline text-sky-400 max-h-fit">
                                Stats
                            </a>
                            ·
                            <a
                                href="https://discord.gg/dyEmZSkwge"
                                className="underline text-sky-400 max-h-fit"
                                target="_blank"
                                rel="noopener noreferrer">
                                Join the Discord!{" "}
                            </a>
                            ·<span>v{version}</span>
                        </footer>
                    )}
                    <div className="h-16"></div>
                </main>
            </div>
        );
    }
}

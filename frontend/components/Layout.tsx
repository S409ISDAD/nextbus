import { Link, Outlet } from "react-router";
import Clock from "../components/Clock";
import version from "../utils/version";

export default function Layout() {
    return (
        <div className="h-full">
            <div className="top-0 flex justify-between p-[8px] z-[99999] border-b-1 border-neutral-800 rounded-b-[24px] fixed w-full bg-[#131313] shadow-2xl md:shadow-xl">
                <div className="flex gap-2">
                    <Link to="/">
                        <div className="flex items-center h-full mx-4">
                            <span className="text-xl font-bold ">nextbus</span>
                        </div>
                    </Link>

                    <Link to="/buses">
                        <button className="p-2 px-3 transition-all cursor-pointer border-neutral-800 h-max rounded-2xl border-1 hover:border-blue-700 ">
                            Buses
                        </button>
                    </Link>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">v{version}</span>
                    <Clock></Clock>
                </div>
            </div>
            <main>
                <div className="h-15"></div>
                <Outlet />
            </main>
        </div>
    );
}

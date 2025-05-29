import { Link, Outlet } from "react-router";
import Clock from "../components/Clock";

export default function Layout() {
    return (
        <div className="h-full">
            <div className="top-0 flex justify-between p-[8px] z-[1000] border-b-1 border-neutral-800 rounded-b-[24px] fixed w-full backdrop-blur-2xl shadow-2xl">
                <div className="flex gap-2">
                    <div className="flex items-center mx-4">
                        <span className="text-xl font-bold">Bus App</span>
                    </div>
                    <Link to="/">
                        <button className="p-2 px-3 transition-all cursor-pointer border-neutral-800 bg-neutral-900 h-max rounded-2xl border-1 hover:border-teal-700">
                            Home
                        </button>
                    </Link>

                    <Link to="/buses">
                        <button className="p-2 px-3 transition-all cursor-pointer border-neutral-800 bg-neutral-900 h-max rounded-2xl border-1 hover:border-teal-700">
                            Buses
                        </button>
                    </Link>
                </div>

                <Clock></Clock>
            </div>
            <main>
                <div className="h-15"></div>
                <Outlet />
            </main>
        </div>
    );
}

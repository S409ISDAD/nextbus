import { useLocation } from "react-router";
import { useEffect, useState } from "react";

export const useShowAppNav = (): boolean => {
    const [show, setShow] = useState<boolean>(false);

    useEffect(() => {
        const mediaQuery = window.matchMedia("(max-width: 640px)");
        setShow(mediaQuery.matches);
        const handler = (e: MediaQueryListEvent) => setShow(e.matches);

        mediaQuery.addEventListener("change", handler);
        return () => mediaQuery.removeEventListener("change", handler);
    }, []);

    return show;
};

export const whereAmI = () => {
    // use location to get the current path, and from there determine what section of the app we are in.
    const location = useLocation();
    if (location.pathname.startsWith("/buses")) {
        return "buses";
    }
    if (location.pathname.startsWith("/trains")) {
        return "trains";
    }
    if (location.pathname === "/account") {
        return "account";
    }
    if (location.pathname === "/") {
        return "home";
    }
    return "other";
}
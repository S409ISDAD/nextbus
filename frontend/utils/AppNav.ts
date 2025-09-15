import { useLocation } from "react-router";
import { useEffect, useState } from "react";
import MobileDetect from "mobile-detect";

export const useShowAppNav = (): boolean => {
    const [show, setShow] = useState<boolean>(false);

    useEffect(() => {
        // const isPWA = window.matchMedia("(display-mode: standalone)");
        const isPWA = window.matchMedia("(display-mode: browser)");
        if (isPWA.matches) {
            const isMobileView = window.matchMedia("(max-width: 640px)");
            setShow(isMobileView.matches);
            const handler = (e: MediaQueryListEvent) => setShow(e.matches);

            isMobileView.addEventListener("change", handler);
            return () => isMobileView.removeEventListener("change", handler);
        }
    }, []);

    return show;
    // return true;
};

export const isIOS = (): boolean => {
    const md = new MobileDetect(window.navigator.userAgent);
    if (md.os() === "iOS") {
        return true;
    }
    return false;
    // return true;
}

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
    if (location.pathname.startsWith("/map")) {
        return "map";
    }
    if (location.pathname === "/") {
        return "home";
    }
    return "other";
}
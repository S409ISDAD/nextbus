import { useLocation } from "react-router";

export const showAppNav = () => {
    // decide wether to show an app-like bottom nav or a normal website nav, based on screen size, and weather it is a pwa.
    if (window.matchMedia("(display-mode: standalone)").matches) {
        return true;
    }
    if (window.matchMedia("(max-width: 640px)").matches) {
        return true;
    }
    return false;
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
    if (location.pathname === "/") {
        return "home";
    }
    return "other";
}
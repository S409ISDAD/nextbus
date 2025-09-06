import { createRoot } from "react-dom/client";
import "@radix-ui/themes/styles.css";
import "leaflet/dist/leaflet.css";
import "leaflet/dist/leaflet.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import App from "./App.tsx";

if ("serviceWorker" in navigator) {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
        for (const registration of registrations) {
            console.log("Unregistering old service worker", registration);
            registration.unregister();
        }
    });
}

createRoot(document.getElementById("root")!).render(<App />);

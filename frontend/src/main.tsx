import { createRoot } from "react-dom/client";
import "@radix-ui/themes/styles.css";
import "leaflet/dist/leaflet.css";
import "leaflet/dist/leaflet.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import App from "./App.tsx";
import "./theme.ts";

createRoot(document.getElementById("root")!).render(<App />);

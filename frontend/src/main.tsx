import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@radix-ui/themes/styles.css";
import App from "./App.tsx";
import "./global.css";
import { Theme, ThemePanel } from "@radix-ui/themes";

createRoot(document.getElementById("root")!).render(
    <Theme accentColor="mint" radius="large" appearance="dark">
        <App />
        {/* <ThemePanel></ThemePanel> */}
    </Theme>
);

import React, { useEffect, useState } from "react";
const ThemeToggle: React.FC = () => {
    const [theme, setTheme] = useState<"halloween" | "dark" | "light">(
        (localStorage.getItem("theme") as "halloween" | "dark" | "light") ||
            "halloween"
    );

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme((prev) => {
            if (prev === "halloween") return "dark";
            if (prev === "dark") return "light";
            return "halloween";
        });
    };

    const getThemeLabel = () => {
        if (theme === "halloween") return "halloween";
        if (theme === "dark") return "dark";
        return "light";
    };

    return (
        <span
            onClick={toggleTheme}
            className="underline cursor-pointer text-link-400">
            {getThemeLabel()} theme
        </span>
    );
};

export default ThemeToggle;

import React, { useEffect, useState } from "react";

const ThemeToggle: React.FC = () => {
    const [theme, setTheme] = useState<"orange" | "blue">("orange");

    useEffect(() => {
        const savedTheme = localStorage.getItem("theme") as
            | "orange"
            | "blue"
            | null;
        if (savedTheme) {
            setTheme(savedTheme);
            document.documentElement.setAttribute("data-theme", savedTheme);
        } else {
            document.documentElement.setAttribute("data-theme", theme);
        }
    }, []);

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme((prev) => (prev === "orange" ? "blue" : "orange"));
    };

    return (
        <span
            onClick={toggleTheme}
            className="underline cursor-pointer text-link">
            change theme
        </span>
    );
};

export default ThemeToggle;

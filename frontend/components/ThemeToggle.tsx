import React, { useEffect, useState } from "react";

const ThemeToggle: React.FC = () => {
    const [theme, setTheme] = useState<"orange" | "blue">(
        (localStorage.getItem("theme") as "orange" | "blue") || "orange"
    );

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
    }, [theme]);

    const toggleTheme = () =>
        setTheme((prev) => (prev === "orange" ? "blue" : "orange"));

    return (
        <span
            onClick={toggleTheme}
            className="underline cursor-pointer text-link">
            change theme
        </span>
    );
};

export default ThemeToggle;

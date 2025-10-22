(function () {
    try {
        const savedTheme = localStorage.getItem("theme");
        if (savedTheme === "dark" || savedTheme === "halloween" || savedTheme === "light") {
            document.documentElement.setAttribute("data-theme", savedTheme);
        } else {
            localStorage.setItem("theme", "halloween");
            document.documentElement.setAttribute("data-theme", "halloween");
        }
    } catch (err) {
        console.warn("Unable to access localStorage for theme:", err);
    }
})();

(function () {
    try {
        document.documentElement.setAttribute("data-theme", "blue");
        localStorage.setItem("theme", "blue");
        // const savedTheme = localStorage.getItem("theme");
        // if (savedTheme === "blue" || savedTheme === "orange") {
        //     document.documentElement.setAttribute("data-theme", savedTheme);
        // } else {
        //     document.documentElement.setAttribute("data-theme", "orange");
        // }
    } catch (err) {
        console.warn("Unable to access localStorage for theme:", err);
    }
})();

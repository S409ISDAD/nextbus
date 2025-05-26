import { Link, Outlet } from "react-router";
import { Button } from "@radix-ui/themes";

export default function Layout() {
    return (
        <>
            <Link
                to="/"
                style={{
                    position: "fixed",
                    top: "1rem",
                    left: "1rem",
                    zIndex: 1000,
                }}>
                <Button
                    variant="soft"
                    size="2"
                    color="gray"
                    style={{ cursor: "pointer" }}>
                    Home
                </Button>
            </Link>
            <main>
                <Outlet />
            </main>
        </>
    );
}

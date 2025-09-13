import React, { use, useEffect, useState } from "react";
import { cn } from "../utils/cn";

export function canUseGeolocation() {
    return localStorage.getItem("geo-permission") === "granted";
}

export function useGeolocationPermission() {
    const [status, setStatus] = useState<PermissionState | null>(null);
    const [position, setPosition] = useState<GeolocationPosition | null>(null);

    useEffect(() => {
        if (!("permissions" in navigator)) return;
        navigator.permissions.query({ name: "geolocation" }).then((res) => {
            setStatus(res.state);
            res.onchange = () => setStatus(res.state);
        });
    }, []);

    useEffect(() => {
        localStorage.setItem("geo-permission", status || "unknown");
    }, [status]);

    const requestLocation = () => {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                setPosition(pos);
                setStatus("granted");
            },
            (err) => {
                console.error("Geolocation error:", err);
                if (err.code === err.PERMISSION_DENIED) {
                    setStatus("denied");
                }
            }
        );
    };

    return { status, position, requestLocation };
}

export function LocationPrompt({
    children,
    className,
}: {
    children: React.ReactNode;
    className?: string;
}) {
    const { status, position, requestLocation } = useGeolocationPermission();

    if (status === "granted" && position) {
        return <>{children}</>;
    }

    if (status === "denied") {
        return (
            <div className={cn("text-center flex flex-col gap-1", className)}>
                <span className="text-neutral-400">
                    Location is blocked. Please enable it in your browser
                    settings.
                </span>
            </div>
        );
    }
    return (
        <div className={cn("text-center flex flex-col gap-1", className)}>
            <span className="text-neutral-400">
                We use your location to show nearby features. Your location is
                never stored.
            </span>
            <button onClick={requestLocation} className="button">
                Enable Location
            </button>
        </div>
    );
}

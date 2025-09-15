import React, { useEffect, useState, useRef } from "react";
import { cn } from "../utils/cn";

export function useIsLocationGranted(): boolean {
    const { status } = useGeolocationPermission();
    const [granted, setGranted] = useState(false);

    useEffect(() => {
        setGranted(status === "granted");
    }, [status]);

    return granted;
}

export function useGeolocationPermission() {
    const [status, setStatus] = useState<PermissionState | null>(null);
    const [position, setPosition] = useState<GeolocationPosition | null>(null);
    const initialized = useRef(false);

    useEffect(() => {
        if (!("permissions" in navigator)) return;

        navigator.permissions
            .query({ name: "geolocation" as PermissionName })
            .then((res) => {
                setStatus(res.state);
                res.onchange = () => setStatus(res.state);
            });
    }, []);

    useEffect(() => {
        if (status === "granted" && !position && !initialized.current) {
            initialized.current = true;
            navigator.geolocation.getCurrentPosition(
                (pos) => setPosition(pos),
                (err) => console.error("Failed to get position:", err)
            );
        }
    }, [status, position]);

    const requestLocation = () => {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                setPosition(pos);
                setStatus("granted");
            },
            (err) => {
                console.error("Geolocation error:", err);
                if (err.code === err.PERMISSION_DENIED) setStatus("denied");
            }
        );
    };
    console.log("Geolocation status:", status);

    return { status, position, requestLocation };
}

export function LocationPrompt({
    children,
    className,
    isGeolocationAvailable,
    isGeolocationEnabled,
}: {
    children: React.ReactNode;
    className?: string;
    isGeolocationAvailable?: boolean;
    isGeolocationEnabled?: boolean;
}) {
    const requestLocation = () => {
        navigator.geolocation.getCurrentPosition(() => {
            console.log("Geolocation aquired");
        });
    };
    if (isGeolocationEnabled) {
        return <>{children}</>;
    }
    if (!isGeolocationEnabled) {
        return (
            <div className={cn("text-center flex flex-col gap-1", className)}>
                <span className="text-neutral-400">
                    Location is blocked. Please enable it in your browser
                    settings.
                </span>
            </div>
        );
    }

    if (!isGeolocationAvailable) {
        return (
            <div className={cn("text-center flex flex-col gap-1", className)}>
                <span className="text-neutral-400">
                    We use your location to show nearby features. Your location
                    is never stored.
                </span>
                <button onClick={requestLocation} className="button">
                    Enable Location
                </button>
            </div>
        );
    }
}

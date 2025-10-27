export const SHOW_BUSES = true;

export const SETTINGS_KEYS = {
    veg: "veg_mode",
};


import { useState, useEffect } from "react";

export function useLocalSetting<T>(key: string, defaultValue: T) {
    const [value, setValue] = useState<T>(() => {
        const saved = localStorage.getItem(key);
        return saved ? JSON.parse(saved) : defaultValue;
    });

    useEffect(() => {
        localStorage.setItem(key, JSON.stringify(value));
    }, [key, value]);

    return [value, setValue] as const;
}
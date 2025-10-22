import { useEffect, useState } from "react";
import { cn } from "../../utils/cn";

function formatTimeSince(time: Date) {
    const now = new Date();
    const seconds = Math.floor((now.getTime() - time.getTime()) / 1000);

    if (seconds < 60) {
        return `${seconds}s ago`;
    } else if (seconds < 3600) {
        const min = Math.floor(seconds / 60);
        return `${min}m ago`;
    } else if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600);
        return `${hours}h ago`;
    } else {
        const days = Math.floor(seconds / 86400);
        return `${days}d ago`;
    }
}

export function TimeSince({
    time,
    className,
}: {
    time: Date | string;
    className?: string;
}) {
    const [text, setText] = useState(() =>
        formatTimeSince(new Date(time))
    );

    useEffect(() => {
        const interval = setInterval(() => {
            setText(formatTimeSince(new Date(time)));
        }, 1000);

        return () => clearInterval(interval);
    }, [time]);

    return <span className={cn("text-neutral-400", className)}>{text}</span>;
}
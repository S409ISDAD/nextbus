import { useState, useEffect } from "react";

function Clock() {
    const [now, setNow] = useState(new Date());

    useEffect(() => {
        const interval = setInterval(() => {
            setNow(new Date());
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-2 px-3 rounded-2xl border-1 border-neutral-800 bg-neutral-900">
            {now.toLocaleTimeString()}
        </div>
    );
}

export default Clock;

import { Card } from "@radix-ui/themes";
import React, { useState, useEffect } from "react";

function Clock() {
    const [now, setNow] = useState(new Date());

    useEffect(() => {
        const interval = setInterval(() => {
            setNow(new Date());
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div>
            <Card>{now.toLocaleTimeString()}</Card>
        </div>
    );
}

export default Clock;

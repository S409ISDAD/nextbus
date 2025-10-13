import React, { useEffect } from "react";

const Terms: React.FC = () => {
    useEffect(() => {
        document.title = "Terms of Service";
    }, []);
    return (
        <div className="flex flex-col max-w-3xl gap-5 p-6 mx-auto">
            <span className="text-4xl font-bold">Terms of Service</span>
            <span>
                <strong>Last updated:</strong> 01/09/2025
            </span>

            <span>By using nextbus, you agree to these terms:</span>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">
                    1. Use at your own risk
                </span>
                <span>
                    NextBus is provided “as is.” We do our best to provide
                    accurate information, but we do not guarantee that bus
                    times, stops, or other data are always correct. Visit the{" "}
                    <strong>
                        <a
                            href="/data"
                            className="underline text-link-400 h-fit">
                            Data Sources
                        </a>
                    </strong>{" "}
                    page for more details on where our data comes from.
                </span>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">2. Location</span>
                <span>
                    You can choose to share your location with nextbus to find
                    nearby stops. You are responsible for managing your device's
                    location permissions.
                </span>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">3. Feedback</span>
                <p>
                    If you submit feedback or your email through our{" "}
                    <strong>
                        <a
                            href="https://forms.gle/SxrFyLQ1HedQcLLC7"
                            className="underline text-link"
                            target="_blank"
                            rel="noopener noreferrer">
                            Google Form
                        </a>
                    </strong>
                    , you agree we can use this information to improve nextbus
                    and contact you about updates.
                </p>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">4. No misuse</span>
                <p>
                    You agree not to misuse our service or API - for example, by
                    trying to break it, overload it, or use it for any illegal
                    purpose. We may apply rate limits and other measures to
                    protect the service from abuse.
                </p>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">5. Changes</span>
                <p>
                    We may update these terms at any time. Significant changes
                    will be posted on this page.
                </p>
            </div>
        </div>
    );
};

export default Terms;

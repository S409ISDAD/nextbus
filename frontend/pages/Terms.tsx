import React, { useEffect } from "react";

const Terms: React.FC = () => {
    useEffect(() => {
        document.title = "Terms of Service";
    }, []);
    return (
        <div className="flex flex-col max-w-3xl gap-5 p-6 mx-auto">
            <span className="text-4xl font-bold">Terms of Service</span>
            <span>
                <strong>Last updated:</strong> January 27th, 2026
            </span>

            <span>By using nextbus, you agree to these terms:</span>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">
                    1. Use at your own risk
                </span>
                <span>
                    nextbus is provided “as is.” We do our best to provide
                    accurate information, but we do not guarantee that bus
                    times, stops, or other data is always correct. Visit the{" "}
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
                    nearby stops and services. You are responsible for managing
                    your device's location permissions.
                </span>
            </div>
            <div className="flex flex-col gap-3">
                <span className="text-2xl font-bold">
                    3. API Usage & Fair Use
                </span>
                <p>
                    Our API is provided <strong>free and open for all</strong>{" "}
                    under the following fair use guidelines:
                </p>
                <ul className="ml-6 space-y-3 list-disc">
                    <li>
                        <strong>Rate Limits:</strong> API requests are
                        rate-limited to ensure service availability. Exceeding
                        limits or circumventing them is prohibited.
                    </li>
                    <li>
                        <strong>No Commercial Resale:</strong> You may not sell,
                        lease, or charge for access to this API without written
                        consent.
                    </li>
                    <li>
                        <strong>Attribution Required:</strong> Provide clear
                        attribution to <strong>nextbus</strong> with a link back
                        to this site.
                    </li>
                    <li>
                        <strong>No Impersonation:</strong> Do not misrepresent
                        data as official or suggest affiliation with transit
                        authorities or nextbus/orbitix.dev.
                    </li>
                    <li>
                        <strong>Right to Terminate:</strong> We may block access
                        for violations or service impact.
                    </li>
                    <li>
                        <strong>Questions?</strong> Contact{" "}
                        <a
                            href="mailto:contact@orbitix.dev"
                            className="underline text-link">
                            contact@orbitix.dev
                        </a>{" "}
                        for higher limits or commercial inquiries.
                    </li>
                </ul>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">4. Changes</span>
                <p>
                    We may update these terms at any time. Significant changes
                    will be posted on this page.
                </p>
            </div>
        </div>
    );
};

export default Terms;

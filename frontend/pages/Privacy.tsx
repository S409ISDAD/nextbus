import React, { useEffect } from "react";

const Privacy: React.FC = () => {
    useEffect(() => {
        document.title = "Privacy Policy";
    }, []);
    return (
        <div className="flex flex-col max-w-3xl gap-5 p-6 mx-auto">
            <span className="text-4xl font-bold">Privacy Policy</span>
            <span>
                <strong>Last updated:</strong> July 15, 2025
            </span>

            <span>
                This website "nextbus" cares about your privacy. We do not
                collect or store any personal data on our servers.
            </span>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">Location Data</span>
                <span>
                    When you use our location-based features, we use your
                    approximate location solely to find your nearest bus stop.
                    Your location is briefly sent to our server and then passed
                    to{" "}
                    <strong>
                        <a
                            href="https://bustimes.org/privacy"
                            className="underline text-sky-500"
                            target="_blank"
                            rel="noopener noreferrer">
                            bustimes.org
                        </a>
                    </strong>{" "}
                    to look up stop data. We do not store your location, and we
                    are not responsible for how{" "}
                    <strong>
                        <a
                            href="https://bustimes.org/privacy"
                            className="underline text-sky-500"
                            target="_blank"
                            rel="noopener noreferrer">
                            bustimes.org
                        </a>
                    </strong>{" "}
                    handles your data once it is shared.
                </span>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">Google Form</span>
                <span>
                    If you choose to submit our Google Form (e.g. to provide
                    feedback), the information you provide is stored by Google
                    Forms and may include your email address or other
                    information you choose to share. We use this information
                    only to contact you about NextBus updates or feedback.
                </span>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">Cookies & Analytics</span>
                <p>We do not use cookies or analytics services at this time.</p>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">Contact</span>
                <p>
                    If you have any questions, please contact:{" "}
                    <a
                        href="mailto:contact@orbitix.dev"
                        className="underline text-sky-500">
                        contact@orbitix.dev
                    </a>
                </p>
            </div>
        </div>
    );
};

export default Privacy;

import React, { useEffect } from "react";
import useLocalStorageState from "use-local-storage-state";

const Privacy: React.FC = () => {
    const [_, setFavStops] = useLocalStorageState<
        Record<string, [number, number]>
    >("favStops", {
        defaultValue: {},
    });
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
                <span>
                    We use cookies for the stop favoriting feature. The stop
                    code and coordinates of the stop are stored in the browser's
                    localStorage under{" "}
                    <span className="p-1 rounded-lg bg-neutral-800">
                        favStops
                    </span>
                    . You can delete this data at any time by pressing the
                    'Clear Favorites' button in the Bus Page or here.
                </span>
                <button
                    className="p-1.5 px-4 w-fit text-sm font-semibold text-white transition-all bg-blue-500 cursor-pointer rounded-xl hover:bg-blue-600"
                    onClick={() => setFavStops({})}>
                    Clear Favorites
                </button>
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

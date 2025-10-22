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
                <strong>Last updated:</strong> October 2nd, 2025
            </span>

            <span>
                This website "nextbus" cares about your privacy. I do not
                collect or store any personal data (data linked to you or your
                identity) on the servers.
            </span>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">Location Data</span>
                <span>
                    When you use the location-based features, I use your
                    approximate location solely to find your nearest bus stop.
                    Your location is briefly sent to the server and then passed
                    to{" "}
                    <strong>
                        <a
                            href="https://bustimes.org/privacy"
                            className="underline text-link"
                            target="_blank"
                            rel="noopener noreferrer">
                            bustimes.org
                        </a>
                    </strong>{" "}
                    to look up stop data. I do not store your location, and I am
                    not responsible for how{" "}
                    <strong>
                        <a
                            href="https://bustimes.org/privacy"
                            className="underline text-link"
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
                    If you choose to fill out the Google Form (e.g. to provide
                    feedback), the information you provide is stored by Google
                    Forms and may include your email address or other
                    information you choose to share. I use this information only
                    to contact you about nextbus updates or feedback.
                </span>
            </div>
            <div className="flex flex-col gap-2">
                <span className="text-2xl font-bold">Cookies & Analytics</span>
                <span>
                    I use cookies for the stop favoriting feature. The stop code
                    and coordinates of the stop are stored in the browser's
                    localStorage under{" "}
                    <span className="p-1 rounded-lg bg-bg-light">favStops</span>
                    . You can delete this data at any time by pressing the
                    'Clear Favorites' button in the Bus Page or here. I also
                    store a randomly generated client ID in your browser's
                    localStorage under{" "}
                    <span className="p-1 rounded-lg bg-bg-light">
                        ws-client-id
                    </span>
                    . This ID is used to identify your WebSocket connection or
                    API request and is not linked to any personal information.
                    This data is used to generate the statistics on the{" "}
                    <a href="/stats" className="underline text-link">
                        Stats Page.
                    </a>{" "}
                    You can delete the ID at any time by clearing your browser's
                    localStorage, however a new one will be generated when you
                    next use the site.
                </span>
                <button
                    className="p-1.5 px-4 w-fit text-sm font-semibold text-text-dark transition-all bg-primary cursor-pointer rounded-xl hover:bg-primary-700"
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
                        className="underline text-link">
                        contact@orbitix.dev
                    </a>
                </p>
            </div>
        </div>
    );
};

export default Privacy;

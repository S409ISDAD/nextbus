import React, { useEffect } from "react";
import { Card } from "../components/ui/Card";
// import DepartureBoard from "../components/DepartureBoard";
// import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

// import type { Locality } from "../models/Locality.ts";
// import { getDestinations } from "../utils/JourneyPlanning.ts";

interface Step {
    text: string;
    imgSrc: string;
    alt: string;
}

const DeviceSteps: React.FC<{ title: string; steps: Step[] }> = ({
    title,
    steps,
}) => (
    <div className="flex flex-col items-center gap-6 p-2 bg-neutral-900 rounded-4xl">
        <h2 className="text-2xl font-semibold">{title}</h2>
        <div className="flex flex-wrap justify-center gap-6">
            {steps.map((step, idx) => (
                <Card
                    key={idx}
                    className="w-[20rem] flex flex-col gap-2 items-center h-fit">
                    <span>{step.text}</span>
                    <img
                        src={step.imgSrc}
                        alt={step.alt}
                        className="shadow-lg rounded-xl"
                    />
                </Card>
            ))}
        </div>
    </div>
);

const InstallHelp: React.FC = () => {
    useEffect(() => {
        document.title = "app install | nextbus";
    }, []);

    const androidSteps: Step[] = [
        {
            text: "Open the Chrome menu by clicking the 3 dots icon in the top-right corner.",
            imgSrc: "https://cdn.orbitix.dev/nextbus_android_3dots.png",
            alt: "Click the 3 dots menu",
        },
        {
            text: 'Select "Add to Home screen" from the menu.',
            imgSrc: "https://cdn.orbitix.dev/nextbus_android_addtohomescreen.png",
            alt: "Select Add to Home screen",
        },
        {
            text: "Accept the install prompt.",
            imgSrc: "https://cdn.orbitix.dev/nextbus_android_installapp.png",
            alt: "Accept the install prompt",
        },
    ];

    const iosSteps: Step[] = [
        {
            text: "Open the Safari menu by clicking the 3 dots icon in the bottom-right corner.",
            imgSrc: "https://cdn.orbitix.dev/nextbus_ios26_3dots.jpg",
            alt: "Click the 3 dots menu",
        },
        {
            text: 'Select "Share" from the menu.',
            imgSrc: "https://cdn.orbitix.dev/nextbus_ios26_share.jpg",
            alt: "Select Share option",
        },
        {
            text: 'Press the "Add to Home Screen" button and accept the prompt.',
            imgSrc: "https://cdn.orbitix.dev/nextbus_ios26_addtohomescreen.jpeg",
            alt: "Add to Home Screen option",
        },
    ];

    return (
        <div className="flex flex-col items-center max-w-6xl gap-8 p-6 mx-auto">
            <h1 className="text-4xl font-bold text-center">
                Installing nextbus
            </h1>
            <span className="max-w-2xl text-lg text-center text-neutral-200">
                nextbus can be installed as an app on your device, which makes
                it easier to access. This is recommended.
            </span>
            <span className="max-w-2xl text-center text-neutral-300">
                iOS is first, scroll down for Android.
            </span>

            <DeviceSteps title="On iOS 26 (Safari):" steps={iosSteps} />
            <DeviceSteps title="On Android (Chrome):" steps={androidSteps} />
        </div>
    );
};

export default InstallHelp;

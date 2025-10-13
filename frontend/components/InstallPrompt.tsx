import { useEffect } from "react";
import toast from "react-hot-toast";
import { useInstallPrompt } from "../utils/useInstallPrompt";
import useLocalStorageState from "use-local-storage-state";

function InstallToast() {
    const deferredPrompt = useInstallPrompt();
    const [lastPrompted, setLastPrompted] =
        useLocalStorageState<Date>("lastPromptedPWA");

    useEffect(() => {
        if (!deferredPrompt) return;
        const now = new Date();
        if (
            lastPrompted &&
            now.getTime() - new Date(lastPrompted).getTime() <
                24 * 60 * 60 * 1000
        )
            return;
        setLastPrompted(now);
        toast.custom(
            (t) => (
                <div
                    className={`transform transition-all duration-300 ${
                        t.visible
                            ? "opacity-100 translate-y-0"
                            : "opacity-0 -translate-y-2"
                    } flex items-center gap-3 px-4 py-3 shadow-lg`}
                    style={{
                        borderRadius: "20px",
                        background: "#222",
                        color: "#fff",
                        border: "1px solid #363636",
                    }}>
                    <div className="flex flex-col gap-2">
                        <span className="text-lg font-bold">
                            Add NextBus to your device
                        </span>
                        <span>
                            Get quick access and a better experience by
                            installing nextbus as an app.
                        </span>
                        <div className="flex w-full gap-2">
                            <button
                                className="w-full px-3 py-1 text-sm font-medium rounded-lg cursor-pointer hover:bg-primary"
                                style={{ background: "#2563eb", color: "#fff" }}
                                onClick={async () => {
                                    deferredPrompt.prompt();
                                    const { outcome } =
                                        await deferredPrompt.userChoice;
                                    console.log(
                                        "User install choice:",
                                        outcome
                                    );
                                    toast.dismiss(t.id);
                                }}>
                                Install
                            </button>
                            <button
                                className="w-full px-3 py-1 text-sm font-medium rounded-lg cursor-pointer hover:bg-primary"
                                style={{
                                    background: "#414141FF",
                                    color: "#fff",
                                }}
                                onClick={() => {
                                    console.log(
                                        "User dismissed install prompt"
                                    );
                                    toast.dismiss(t.id);
                                }}>
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            ),
            {
                duration: Infinity, // stays until user acts
                id: "install-toast", // only one at a time
            }
        );
    }, [deferredPrompt]);

    return null;
}

export default InstallToast;

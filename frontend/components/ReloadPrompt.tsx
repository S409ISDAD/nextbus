import { useEffect } from "react";
import { toast } from "react-hot-toast";
import { useRegisterSW } from "virtual:pwa-register/react";

export default function useReloadPrompt() {
    const {
        offlineReady: [offlineReady, setOfflineReady],
        needRefresh: [needRefresh, setNeedRefresh],
        updateServiceWorker,
    } = useRegisterSW();

    useEffect(() => {
        if (offlineReady) {
            toast.success("App ready to work offline", {
                duration: 4000,
            });
            setOfflineReady(false);
        }

        if (needRefresh) {
            toast(
                (t) => (
                    <div className="flex flex-col items-center gap-2 sm:flex-row">
                        <span className="text-white">
                            New content available, click reload to update.
                        </span>
                        <div className="flex gap-2 mt-2 sm:mt-0">
                            <button
                                className="px-3 py-1 text-white bg-blue-500 rounded hover:bg-blue-600"
                                onClick={() => {
                                    updateServiceWorker(true);
                                    toast.dismiss(t.id);
                                }}>
                                Reload
                            </button>
                            <button
                                className="px-3 py-1 text-white bg-gray-600 rounded hover:bg-gray-700"
                                onClick={() => {
                                    toast.dismiss(t.id);
                                    setNeedRefresh(false);
                                }}>
                                Close
                            </button>
                        </div>
                    </div>
                ),
                { duration: Infinity }
            );
        }
    }, [offlineReady, needRefresh]);

    return null;
}

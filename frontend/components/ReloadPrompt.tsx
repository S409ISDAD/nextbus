import { useEffect } from "react";
import { toast } from "react-hot-toast";
import { useRegisterSW } from "virtual:pwa-register/react";

export default function useReloadPrompt() {
    const {
        offlineReady: [offlineReady],
        needRefresh: [needRefresh],
    } = useRegisterSW();

    useEffect(() => {
        if (offlineReady) {
            toast.success("App initialised successfully", {
                duration: 4000,
            });
        }
    }, [offlineReady, needRefresh]);

    return null;
}

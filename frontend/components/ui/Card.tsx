import { cn } from "../../utils/cn";

export function Card({
    children,
    className,
}: React.PropsWithChildren<{ className?: string }>) {
    return (
        <div
            className={cn(
                "rounded-3xl shadow-xl p-4 bg-neutral-900 border-1 border-neutral-800 backdrop-blur-sm transition-all",
                className
            )}>
            {children}
        </div>
    );
}

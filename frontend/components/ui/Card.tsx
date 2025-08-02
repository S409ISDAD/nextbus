import { cn } from "../../utils/cn";

export function Card({
    children,
    className,
}: React.PropsWithChildren<{ className?: string }>) {
    return (
        <div
            className={cn(
                "rounded-3xl p-4 border-1 border-neutral-800 bg-neutral-800/25 transition-all",
                className
            )}>
            {children}
        </div>
    );
}

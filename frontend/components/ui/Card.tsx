import { cn } from "../../utils/cn";

export function Card({
    children,
    className,
}: React.PropsWithChildren<{ className?: string }>) {
    return (
        <div
            className={cn(
                "rounded-3xl p-4 border-1 border-neutral-800 backdrop-blur-sm transition-all backdrop-brightness-130",
                className
            )}>
            {children}
        </div>
    );
}

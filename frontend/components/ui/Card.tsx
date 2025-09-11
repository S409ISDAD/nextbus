import { cn } from "../../utils/cn";

export function Card({
    children,
    className,
    onClick,
}: React.PropsWithChildren<{
    className?: string | undefined;
    onClick?: () => void;
}>) {
    return (
        <div
            className={cn(
                "rounded-3xl p-4 border-1 border-neutral-800 bg-neutral-800/25 transition-all",
                className
            )}
            onClick={onClick}>
            {children}
        </div>
    );
}

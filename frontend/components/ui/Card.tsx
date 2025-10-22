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
                "rounded-3xl p-4 border-1 border-bg-light bg-bg-light/25 transition-all",
                className
            )}
            onClick={onClick}>
            {children}
        </div>
    );
}

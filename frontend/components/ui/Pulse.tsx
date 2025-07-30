export const Pulse = ({
    size = 36,
    color = "bg-rose-400",
    duration = 2,
}: {
    size?: number;
    color?: string;
    duration?: number;
}) => {
    return (
        <span
            className={`absolute rounded-full ${color} pointer-events-none`}
            style={{
                width: size,
                height: size,
                left: "50%",
                top: "50%",
                transform: "translate(-50%, -50%)",
                zIndex: 0,
                animation: `pulse ${duration}s cubic-bezier(0.4,0,0.2,1) infinite`,
            }}
        />
    );
};

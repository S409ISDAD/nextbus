import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            error,
        };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        console.error("ErrorBoundary caught an error:", error, errorInfo);
    }

    render(): ReactNode {
        if (this.state.hasError) {
            return (
                this.props.fallback || (
                    <div>
                        <h2>Something went wrong.</h2>
                        <details style={{ whiteSpace: "pre-wrap" }}>
                            {this.state.error?.toString()}
                        </details>
                    </div>
                )
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;

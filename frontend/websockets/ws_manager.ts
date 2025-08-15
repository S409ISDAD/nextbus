import { v4 as uuidv4 } from "uuid";

export type WSMessage = {
    type: string;
    [key: string]: any;
};

type Callback = (msg: WSMessage) => void;

export class WebSocketManager {
    private static instances: Map<string, WebSocketManager> = new Map();

    private socket: WebSocket | null = null;
    private url: string;
    private autoReconnect: boolean = true;
    private reconnectDelay: number = 2000;
    private clientId: string;

    private onMessageCallbacks: Callback[] = [];
    private onOpenCallbacks: (() => void)[] = [];
    private onCloseCallbacks: (() => void)[] = [];

    private constructor(url: string) {
        this.url = url;
        let storedClientId = localStorage.getItem("ws-client-id");
        if (!storedClientId) {
            const newId = uuidv4();
            localStorage.setItem("ws-client-id", newId);
            this.clientId = newId;
        } else {
            this.clientId = storedClientId;
        }
    }

    public static getInstance(url: string): WebSocketManager {
        if (!this.instances.has(url)) {
            const instance = new WebSocketManager(url);
            this.instances.set(url, instance);
            instance.connect();
        }
        return this.instances.get(url)!;
    }

    connect() {
        if (this.socket && this.socket.readyState < 2) return;
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        this.socket = new WebSocket(
            `${protocol}://${window.location.host}/ws/${this.url}?client_id=${encodeURIComponent(this.clientId)}`
        );

        this.socket.onopen = () => {
            this.onOpenCallbacks.forEach(cb => cb());
        };

        this.socket.onmessage = (event: MessageEvent) => {
            try {
                const msg: WSMessage = JSON.parse(event.data);
                this.onMessageCallbacks.forEach(cb => cb(msg));
            } catch (err) {
                console.error("WS message parse error", err);
            }
        };

        this.socket.onclose = () => {
            this.onCloseCallbacks.forEach(cb => cb());
            if (this.autoReconnect) {
                setTimeout(() => this.connect(), this.reconnectDelay);
            }
        };

        this.socket.onerror = (err) => {
            console.error("WS error:", err);
            this.socket?.close();
        };
    }

    send(data: object) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        }
    }

    onMessage(callback: Callback) {
        this.onMessageCallbacks.push(callback);
    }

    onOpen(callback: () => void) {
        this.onOpenCallbacks.push(callback);
    }

    onClose(callback: () => void) {
        this.onCloseCallbacks.push(callback);
    }

    close() {
        this.autoReconnect = false;
        this.socket?.close();
        this.socket = null;
    }

    clearCallbacks() {
        this.onMessageCallbacks = [];
        this.onOpenCallbacks = [];
        this.onCloseCallbacks = [];
    }

    reconnect() {
        this.close();
        this.autoReconnect = true;
        this.connect();
    }

    isConnected(): boolean {
        return this.socket?.readyState === WebSocket.OPEN;
    }
}
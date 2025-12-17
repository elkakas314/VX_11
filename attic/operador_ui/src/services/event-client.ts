/**
 * Cliente de eventos Centrado-en-Eventos (Event-Centric)
 * Conecta a WebSocket del backend para recibir eventos canónicos
 */

import type { CanonicalEvent } from "../types/canonical-events";
import { isCanonicalEvent } from "../types/canonical-events";

type EventHandler = (event: CanonicalEvent) => void;

export class EventClient {
    private ws: WebSocket | null = null;
    private url: string;
    private handlers: Map<string, EventHandler[]> = new Map();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 3000; // 3 segundos

    constructor(url: string) {
        this.url = url;
    }

    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    this.reconnectAttempts = 0;
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const payload = JSON.parse(event.data);
                        if (isCanonicalEvent(payload)) {
                            this.dispatch(payload);
                        }
                    } catch {
                        // Silencio en producción
                    }
                };

                this.ws.onerror = () => {
                    reject(new Error("WebSocket connection failed"));
                };

                this.ws.onclose = () => {
                    this.attemptReconnect();
                };
            } catch (err) {
                reject(err);
            }
        });
    }

    private attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect().catch(() => { }), this.reconnectDelay);
        }
    }

    subscribe(eventType: string, handler: EventHandler): void {
        if (!this.handlers.has(eventType)) {
            this.handlers.set(eventType, []);
        }
        this.handlers.get(eventType)!.push(handler);
    }

    unsubscribe(eventType: string, handler: EventHandler): void {
        const handlers = this.handlers.get(eventType);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    private dispatch(event: CanonicalEvent): void {
        // Dispatch genérico
        const genericHandlers = this.handlers.get("*") || [];
        genericHandlers.forEach((h) => h(event));

        // Dispatch específico por tipo
        const handlers = this.handlers.get(event.type) || [];
        handlers.forEach((h) => h(event));
    }

    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
    }
}

// Cliente singleton
let eventClient: EventClient | null = null;

export function getEventClient(url: string): EventClient {
    if (!eventClient) {
        eventClient = new EventClient(url);
    }
    return eventClient;
}

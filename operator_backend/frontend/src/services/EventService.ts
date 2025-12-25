/**
 * EventService: Manages SSE connection to /api/events with reconnection
 * 
 * Features:
 * - Automatic reconnection on disconnect
 * - Exponential backoff (1s, 2s, 4s, 8s, 30s max)
 * - Request ID tracking from stream events
 * - Event filtering by source/type/severity
 * - Type-safe event handling
 */

import React from "react";

export interface StreamEvent {
    id?: number;
    type: string;
    source?: string;
    severity?: string;
    request_id?: string;
    payload?: Record<string, any>;
    error?: string;
    timestamp: string;
}

export interface EventListener {
    (event: StreamEvent): void;
}

export type EventFilter = {
    source?: string;
    event_type?: string;
    severity?: string;
};

export class EventService {
    private eventSource: EventSource | null = null;
    private listeners: Set<EventListener> = new Set();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 10;
    private baseBackoffMs = 1000;
    private maxBackoffMs = 30000;
    private token: string;
    private filter: EventFilter;
    private currentRequestId: string | null = null;
    private isManuallyClosed = false;

    constructor(token: string, filter: EventFilter = {}) {
        this.token = token;
        this.filter = filter;
    }

    /**
     * Connect to SSE stream and start listening
     */
    public connect(): void {
        if (this.eventSource) {
            return; // Already connected
        }

        this.isManuallyClosed = false;

        // Build query string
        const params = new URLSearchParams();
        if (this.filter.source) params.append("source", this.filter.source);
        if (this.filter.event_type) params.append("event_type", this.filter.event_type);
        if (this.filter.severity) params.append("severity", this.filter.severity);

        const queryString = params.toString();
        const url = `/api/events${queryString ? "?" + queryString : ""}`;

        try {
            this.eventSource = new EventSource(url);

            // Add auth token (EventSource doesn't support custom headers directly)
            // Client should handle via request interceptor or CORS + cookies

            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data) as StreamEvent;

                    // Track request_id from stream
                    if (data.request_id) {
                        this.currentRequestId = data.request_id;
                    }

                    // Emit to listeners
                    this.listeners.forEach((listener) => listener(data));

                    // Reset reconnect attempts on successful message
                    this.reconnectAttempts = 0;
                } catch (e) {
                    console.error("Failed to parse SSE event:", e);
                }
            };

            this.eventSource.onerror = (event) => {
                console.warn("SSE connection error:", event);
                this.handleDisconnect();
            };

            console.log("SSE connected to /api/events", { url, currentRequestId: this.currentRequestId });
        } catch (e) {
            console.error("Failed to create EventSource:", e);
            this.handleDisconnect();
        }
    }

    /**
     * Handle disconnection with exponential backoff reconnection
     */
    private handleDisconnect(): void {
        if (this.isManuallyClosed) {
            return;
        }

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error("Max reconnection attempts reached");
            return;
        }

        this.reconnectAttempts++;
        const backoffMs = Math.min(
            this.baseBackoffMs * Math.pow(2, this.reconnectAttempts - 1),
            this.maxBackoffMs
        );

        console.log(`Reconnecting in ${backoffMs}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => this.connect(), backoffMs);
    }

    /**
     * Add event listener
     */
    public on(listener: EventListener): () => void {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    /**
     * Add typed event listener (for specific event types)
     */
    public on_type(eventType: string, listener: EventListener): () => void {
        const typedListener = (event: StreamEvent) => {
            if (event.type === eventType) {
                listener(event);
            }
        };
        return this.on(typedListener);
    }

    /**
     * Disconnect and stop listening
     */
    public disconnect(): void {
        this.isManuallyClosed = true;
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.listeners.clear();
        this.reconnectAttempts = 0;
    }

    /**
     * Get current request ID from stream
     */
    public getRequestId(): string | null {
        return this.currentRequestId;
    }

    /**
     * Get reconnection status
     */
    public isConnected(): boolean {
        return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN;
    }

    /**
     * Get reconnection attempts
     */
    public getReconnectAttempts(): number {
        return this.reconnectAttempts;
    }

    /**
     * Update filter and reconnect
     */
    public setFilter(filter: EventFilter): void {
        this.filter = filter;
        if (this.isConnected()) {
            this.disconnect();
            this.connect();
        }
    }
}

/**
 * React Hook for EventService
 */
export const useEvents = (token: string, filter: EventFilter = {}) => {
    const [service] = React.useState(() => new EventService(token, filter));
    const [events, setEvents] = React.useState<StreamEvent[]>([]);
    const [isConnected, setIsConnected] = React.useState(false);
    const [requestId, setRequestId] = React.useState<string | null>(null);

    React.useEffect(() => {
        service.connect();

        const unsubscribe = service.on((event) => {
            setEvents((prev) => [...prev, event]);
            setRequestId(service.getRequestId());
        });

        // Check connection status periodically
        const intervalId = setInterval(() => {
            setIsConnected(service.isConnected());
        }, 1000);

        return () => {
            unsubscribe();
            clearInterval(intervalId);
            service.disconnect();
        };
    }, [service]);

    return {
        events,
        isConnected,
        requestId,
        service,
    };
};

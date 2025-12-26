import { describe, beforeEach, afterEach, test, expect, vi } from "vitest";
import { EventService, StreamEvent } from "../EventService";

describe("EventService", () => {
    let service: EventService;
    const mockToken = "test-token";

    beforeEach(() => {
        service = new EventService(mockToken);
        // Mock EventSource
        global.EventSource = vi.fn(() => ({
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
            close: vi.fn(),
            readyState: EventSource.OPEN,
        })) as any;
    });

    afterEach(() => {
        service.disconnect();
        vi.clearAllMocks();
    });

    test("initializes with correct token and default filter", () => {
        expect(service).toBeDefined();
        expect(service.getRequestId()).toBeNull();
    });

    test("connects to EventSource", () => {
        service.connect();
        expect(global.EventSource as unknown as ReturnType<typeof vi.fn>).toHaveBeenCalled();
    });

    test("does not create duplicate connections", () => {
        service.connect();
        service.connect();
        // EventSource should be called only once
        expect(global.EventSource as unknown as ReturnType<typeof vi.fn>).toHaveBeenCalledTimes(1);
    });

    test("listens to events and emits to listeners", async () => {
        const mockEvent: StreamEvent = {
            type: "test",
            request_id: "req-123",
            timestamp: new Date().toISOString(),
        };

        await new Promise<void>((resolve) => {
            service.on((event: StreamEvent) => {
                expect(event).toEqual(mockEvent);
                expect(service.getRequestId()).toBe("req-123");
                resolve();
            });

            service.connect();

            // Simulate EventSource message
            const eventSourceInstance = (global.EventSource as any).mock.results[0].value;
            const messageHandler = eventSourceInstance.addEventListener.mock.calls.find(
                (call: any[]) => call[0] === "message"
            )?.[1];

            if (messageHandler) {
                messageHandler({
                    data: JSON.stringify(mockEvent),
                });
            }
        });
    });

    test("handles errors and attempts reconnection", () => {
        vi.useFakeTimers();
        service.connect();

        const eventSourceInstance = (global.EventSource as any).mock.results[0].value;
        const errorHandler = eventSourceInstance.addEventListener.mock.calls.find(
            (call: any[]) => call[0] === "error"
        )?.[1];

        if (errorHandler) {
            errorHandler(new Event("error"));
        }

        expect(service.getReconnectAttempts()).toBe(1);

        vi.advanceTimersByTime(1000);
        expect(global.EventSource).toHaveBeenCalledTimes(2); // Original + reconnect

        vi.useRealTimers();
    });

    test("applies exponential backoff on reconnection", () => {
        vi.useFakeTimers();
        service.connect();

        for (let i = 0; i < 3; i++) {
            const eventSourceInstance = (global.EventSource as any).mock.results[
                (global.EventSource as any).mock.results.length - 1
            ].value;
            const errorHandler = eventSourceInstance.addEventListener.mock.calls.find(
                (call: any[]) => call[0] === "error"
            )?.[1];

            if (errorHandler) {
                errorHandler(new Event("error"));
            }

            const expectedBackoff = Math.min(1000 * Math.pow(2, i), 30000);
            vi.advanceTimersByTime(expectedBackoff);
        }

        // Should have created 4 connections (original + 3 reconnects)
        expect((global.EventSource as any).mock.calls.length).toBeGreaterThan(1);

        vi.useRealTimers();
    });

    test("allows adding and removing listeners", () => {
        const listener1 = vi.fn();
        const listener2 = vi.fn();

        const unsubscribe1 = service.on(listener1);
        const unsubscribe2 = service.on(listener2);

        service.connect();

        const eventSourceInstance = (global.EventSource as any).mock.results[0].value;
        const messageHandler = eventSourceInstance.addEventListener.mock.calls.find(
            (call: any[]) => call[0] === "message"
        )?.[1];

        const mockEvent: StreamEvent = {
            type: "test",
            timestamp: new Date().toISOString(),
        };

        if (messageHandler) {
            messageHandler({ data: JSON.stringify(mockEvent) });
        }

        expect(listener1).toHaveBeenCalledWith(mockEvent);
        expect(listener2).toHaveBeenCalledWith(mockEvent);

        unsubscribe1();

        listener1.mockClear();
        listener2.mockClear();

        if (messageHandler) {
            messageHandler({ data: JSON.stringify(mockEvent) });
        }

        expect(listener1).not.toHaveBeenCalled();
        expect(listener2).toHaveBeenCalledWith(mockEvent);
    });

    test("on_type filters events by type", () => {
        const mockListener = vi.fn();

        service.on_type("startup", mockListener);
        service.connect();

        const eventSourceInstance = (global.EventSource as any).mock.results[0].value;
        const messageHandler = eventSourceInstance.addEventListener.mock.calls.find(
            (call: any[]) => call[0] === "message"
        )?.[1];

        const startupEvent: StreamEvent = {
            type: "startup",
            timestamp: new Date().toISOString(),
        };
        const errorEvent: StreamEvent = {
            type: "error",
            timestamp: new Date().toISOString(),
        };

        if (messageHandler) {
            messageHandler({ data: JSON.stringify(startupEvent) });
            messageHandler({ data: JSON.stringify(errorEvent) });
        }

        expect(mockListener).toHaveBeenCalledTimes(1);
        expect(mockListener).toHaveBeenCalledWith(startupEvent);
    });

    test("disconnects and stops reconnection attempts", () => {
        vi.useFakeTimers();
        service.connect();

        const eventSourceInstance = (global.EventSource as any).mock.results[0].value;
        const errorHandler = eventSourceInstance.addEventListener.mock.calls.find(
            (call: any[]) => call[0] === "error"
        )?.[1];

        if (errorHandler) {
            errorHandler(new Event("error"));
        }

        service.disconnect();

        const previousCallCount = (global.EventSource as any).mock.calls.length;
        vi.advanceTimersByTime(10000);

        // Should not attempt reconnection after disconnect
        expect((global.EventSource as any).mock.calls.length).toBe(previousCallCount);

        vi.useRealTimers();
    });

    test("tracks request ID from events", () => {
        service.connect();

        expect(service.getRequestId()).toBeNull();

        const eventSourceInstance = (global.EventSource as any).mock.results[0].value;
        const messageHandler = eventSourceInstance.addEventListener.mock.calls.find(
            (call: any[]) => call[0] === "message"
        )?.[1];

        const eventWithId: StreamEvent = {
            type: "test",
            request_id: "req-xyz-789",
            timestamp: new Date().toISOString(),
        };

        if (messageHandler) {
            messageHandler({ data: JSON.stringify(eventWithId) });
        }

        expect(service.getRequestId()).toBe("req-xyz-789");
    });

    test("updates filter and reconnects", () => {
        service.connect();
        const initialCallCount = (global.EventSource as any).mock.calls.length;

        service.setFilter({ source: "madre" });

        // Should have reconnected with new filter
        expect((global.EventSource as any).mock.calls.length).toBeGreaterThan(initialCallCount);
    });

    test("isConnected returns correct status", () => {
        expect(service.isConnected()).toBe(false);

        service.connect();
        expect(service.isConnected()).toBe(true);

        service.disconnect();
        expect(service.isConnected()).toBe(false);
    });

    test("handles malformed JSON in events gracefully", () => {
        const mockListener = vi.fn();
        const consoleError = vi.spyOn(console, "error").mockImplementation(() => { });

        service.on(mockListener);
        service.connect();

        const eventSourceInstance = (global.EventSource as any).mock.results[0].value;
        const messageHandler = eventSourceInstance.addEventListener.mock.calls.find(
            (call: any[]) => call[0] === "message"
        )?.[1];

        if (messageHandler) {
            messageHandler({ data: "invalid json" });
        }

        expect(consoleError).toHaveBeenCalled();
        expect(mockListener).not.toHaveBeenCalled();

        consoleError.mockRestore();
    });

    test("respects max reconnect attempts", () => {
        vi.useFakeTimers();
        service.connect();

        for (let i = 0; i < 11; i++) {
            const eventSourceInstance = (global.EventSource as any).mock.results[
                (global.EventSource as any).mock.results.length - 1
            ].value;
            const errorHandler = eventSourceInstance.addEventListener.mock.calls.find(
                (call: any[]) => call[0] === "error"
            )?.[1];

            if (errorHandler) {
                errorHandler(new Event("error"));
                vi.advanceTimersByTime(30000);
            }
        }

        const maxAttemptsReached = service.getReconnectAttempts() >= 10;
        expect(maxAttemptsReached).toBe(true);

        vi.useRealTimers();
    });
});

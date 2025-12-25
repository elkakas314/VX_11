import { renderHook, act, waitFor } from "@testing-library/react";
import { useChat } from "./useChat";
import * as canonicalApi from "../api/canonical";

jest.mock("../api/canonical", () => ({
    sendChat: jest.fn(),
}));

describe("useChat Hook", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test("initializes with default state", () => {
        const { result } = renderHook(() => useChat());

        expect(result.current.messages).toEqual([]);
        expect(result.current.input).toBe("");
        expect(result.current.loading).toBe(false);
        expect(result.current.mode).toBe("default");
        expect(result.current.degradedMode).toBe(false);
    });

    test("sends a message with unified response", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-123",
            route_taken: "tentaculo_link",
            degraded: false,
            errors: [],
            data: { response: "Hello!" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        const { result } = renderHook(() => useChat());

        act(() => {
            result.current.setInput("Hi");
        });

        await act(async () => {
            await result.current.send();
        });

        await waitFor(() => {
            expect(result.current.messages).toHaveLength(2);
            expect(result.current.messages[0].role).toBe("user");
            expect(result.current.messages[0].content).toBe("Hi");
            expect(result.current.messages[1].role).toBe("assistant");
            expect(result.current.messages[1].content).toBe("Hello!");
            expect(result.current.messages[1].requestId).toBe("req-123");
            expect(result.current.messages[1].routeTaken).toBe("tentaculo_link");
        });
    });

    test("handles degraded response", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-456",
            route_taken: "madre",
            degraded: true,
            errors: [{ step: "tentaculo", hint: "Timeout" }],
            data: { response: "[DEGRADED] Fallback" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        const { result } = renderHook(() => useChat());

        act(() => {
            result.current.setInput("Test");
        });

        await act(async () => {
            await result.current.send();
        });

        await waitFor(() => {
            expect(result.current.degradedMode).toBe(true);
            expect(result.current.degradedHint).toBe("Timeout");
            expect(result.current.messages[1].status).toBe("degraded");
            expect(result.current.messages[1].degraded).toBe(true);
        });
    });

    test("handles error response", async () => {
        const mockError = { error: "Network error" };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockError);

        const { result } = renderHook(() => useChat());

        act(() => {
            result.current.setInput("Test");
        });

        await act(async () => {
            await result.current.send();
        });

        await waitFor(() => {
            expect(result.current.messages[1].status).toBe("error");
            expect(result.current.messages[1].content).toContain("Network error");
        });
    });

    test("respects maxMessageLength option", () => {
        const alertSpy = jest.spyOn(window, "alert").mockImplementation();
        const { result } = renderHook(() => useChat({ maxMessageLength: 100 }));

        act(() => {
            result.current.setInput("a".repeat(101));
        });

        act(() => {
            result.current.send();
        });

        expect(alertSpy).toHaveBeenCalledWith("Message too long (max 100 chars)");
        alertSpy.mockRestore();
    });

    test("changes mode", () => {
        const { result } = renderHook(() => useChat());

        expect(result.current.mode).toBe("default");

        act(() => {
            result.current.setMode("analyze");
        });

        expect(result.current.mode).toBe("analyze");
    });

    test("clears messages", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-789",
            route_taken: "tentaculo_link",
            degraded: false,
            errors: [],
            data: { response: "Response" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        const { result } = renderHook(() => useChat());

        act(() => {
            result.current.setInput("Message");
        });

        await act(async () => {
            await result.current.send();
        });

        await waitFor(() => {
            expect(result.current.messages).toHaveLength(2);
        });

        act(() => {
            result.current.clearMessages();
        });

        expect(result.current.messages).toHaveLength(0);
        expect(result.current.degradedMode).toBe(false);
        expect(result.current.degradedHint).toBe("");
    });

    test("extracts errors array from unified response", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-999",
            route_taken: "madre",
            degraded: true,
            errors: [
                { step: "tentaculo", hint: "Timeout" },
                { step: "switch", hint: "No response" },
            ],
            data: { response: "Degraded" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        const { result } = renderHook(() => useChat());

        act(() => {
            result.current.setInput("Test");
        });

        await act(async () => {
            await result.current.send();
        });

        await waitFor(() => {
            expect(result.current.messages[1].errors).toEqual([
                { step: "tentaculo", hint: "Timeout" },
                { step: "switch", hint: "No response" },
            ]);
        });
    });

    test("detects legacy response format without unified schema", async () => {
        const mockResponse = {
            response: "[DEGRADED] Legacy fallback",
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        const { result } = renderHook(() => useChat());

        act(() => {
            result.current.setInput("Legacy test");
        });

        await act(async () => {
            await result.current.send();
        });

        await waitFor(() => {
            expect(result.current.degradedMode).toBe(true);
            expect(result.current.messages[1].routeTaken).toBe("unknown");
        });
    });

    test("sets degraded hint from errors", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-111",
            route_taken: "madre",
            degraded: true,
            errors: [{ step: "tentaculo", hint: "Custom error hint" }],
            data: { response: "Failed" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        const { result } = renderHook(() => useChat());

        act(() => {
            result.current.setInput("Test");
        });

        await act(async () => {
            await result.current.send();
        });

        await waitFor(() => {
            expect(result.current.degradedHint).toBe("Custom error hint");
        });
    });

    test("sets default degraded hint when no errors", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-222",
            route_taken: "madre",
            degraded: true,
            errors: [],
            data: { response: "Degraded but no errors" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        const { result } = renderHook(() => useChat());

        act(() => {
            result.current.setInput("Test");
        });

        await act(async () => {
            await result.current.send();
        });

        await waitFor(() => {
            expect(result.current.degradedHint).toBe("Fallback endpoint active");
        });
    });
});

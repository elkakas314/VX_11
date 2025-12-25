import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatTab } from "./ChatTab";
import * as canonicalApi from "../api/canonical";

// Mock the API
jest.mock("../api/canonical", () => ({
    sendChat: jest.fn(),
}));

describe("ChatTab Component", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test("renders initial state without messages", () => {
        render(<ChatTab />);
        expect(screen.getByText(/no messages yet/i)).toBeInTheDocument();
    });

    test("sends a message and receives a unified response (ok)", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-123-abc",
            route_taken: "tentaculo_link",
            degraded: false,
            errors: [],
            data: { response: "Hello from Tentaculo!" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        render(<ChatTab />);

        const input = screen.getByRole("textbox");
        const sendBtn = screen.getByRole("button", { name: /send/i });

        await userEvent.type(input, "Hi there");
        fireEvent.click(sendBtn);

        await waitFor(() => {
            expect(screen.getByText("Hi there")).toBeInTheDocument();
            expect(screen.getByText("Hello from Tentaculo!")).toBeInTheDocument();
        });

        // Verify no degraded banner
        expect(screen.queryByText(/DEGRADED MODE ACTIVE/)).not.toBeInTheDocument();
    });

    test("shows degraded mode banner when response.degraded=true", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-456-def",
            route_taken: "madre",
            degraded: true,
            errors: [{ step: "tentaculo_link", hint: "Connection timeout" }],
            data: { response: "[DEGRADED] Fallback response" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        render(<ChatTab />);

        const input = screen.getByRole("textbox");
        const sendBtn = screen.getByRole("button", { name: /send/i });

        await userEvent.type(input, "Message");
        fireEvent.click(sendBtn);

        await waitFor(() => {
            expect(screen.getByText(/DEGRADED MODE ACTIVE/i)).toBeInTheDocument();
            expect(screen.getByText(/Connection timeout/)).toBeInTheDocument();
        });
    });

    test("displays request_id and route_taken info", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-789-ghi",
            route_taken: "tentaculo_link",
            degraded: false,
            errors: [],
            data: { response: "Response from Tentaculo" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        render(<ChatTab />);

        const input = screen.getByRole("textbox");
        const sendBtn = screen.getByRole("button", { name: /send/i });

        await userEvent.type(input, "Test");
        fireEvent.click(sendBtn);

        await waitFor(() => {
            expect(screen.getByText(/ID: req-789/)).toBeInTheDocument();
            expect(screen.getByText(/Route: tentaculo_link/)).toBeInTheDocument();
        });
    });

    test("handles error response", async () => {
        const mockError = { error: "Network error" };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockError);

        render(<ChatTab />);

        const input = screen.getByRole("textbox");
        const sendBtn = screen.getByRole("button", { name: /send/i });

        await userEvent.type(input, "Test");
        fireEvent.click(sendBtn);

        await waitFor(() => {
            expect(screen.getByText(/❌ Error: Network error/)).toBeInTheDocument();
        });
    });

    test("mode selector changes message mode", async () => {
        render(<ChatTab />);

        const analyzeBtn = screen.getByRole("button", { name: "analyze" });
        fireEvent.click(analyzeBtn);

        expect(analyzeBtn).toHaveClass("bg-blue-600");
    });

    test("prevents messages longer than maxMessageLength", async () => {
        const alertSpy = jest.spyOn(window, "alert").mockImplementation();
        render(<ChatTab />);

        const input = screen.getByRole("textbox") as HTMLInputElement;
        const sendBtn = screen.getByRole("button", { name: /send/i });

        const longMessage = "a".repeat(4097);
        await userEvent.type(input, longMessage);
        fireEvent.click(sendBtn);

        expect(alertSpy).toHaveBeenCalledWith(
            "Message too long (max 4096 chars)"
        );
        alertSpy.mockRestore();
    });

    test("color-codes messages based on route_taken", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-999",
            route_taken: "tentaculo_link",
            degraded: false,
            errors: [],
            data: { response: "Green border (tentaculo)" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        render(<ChatTab />);

        const input = screen.getByRole("textbox");
        const sendBtn = screen.getByRole("button", { name: /send/i });

        await userEvent.type(input, "Test");
        fireEvent.click(sendBtn);

        await waitFor(() => {
            const msgDiv = screen.getByText("Green border (tentaculo)").closest("div");
            expect(msgDiv).toHaveClass("bg-green-900", "border-green-500");
        });
    });

    test("dismisses degraded banner on click", async () => {
        const mockResponse = {
            ok: true,
            request_id: "req-abc",
            route_taken: "madre",
            degraded: true,
            errors: [{ step: "tentaculo", hint: "Timeout" }],
            data: { response: "[DEGRADED] Fallback" },
        };
        (canonicalApi.sendChat as jest.Mock).mockResolvedValueOnce(mockResponse);

        render(<ChatTab />);

        const input = screen.getByRole("textbox");
        const sendBtn = screen.getByRole("button", { name: /send/i });

        await userEvent.type(input, "Message");
        fireEvent.click(sendBtn);

        await waitFor(() => {
            expect(screen.getByText(/DEGRADED MODE ACTIVE/i)).toBeInTheDocument();
        });

        const dismissBtn = screen.getByRole("button", { name: /dismiss/i });
        fireEvent.click(dismissBtn);

        await waitFor(() => {
            expect(screen.queryByText(/DEGRADED MODE ACTIVE/i)).not.toBeInTheDocument();
        });
    });
});

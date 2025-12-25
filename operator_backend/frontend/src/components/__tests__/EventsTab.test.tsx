import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EventsTab } from "./EventsTab";
import * as EventServiceModule from "../services/EventService";

jest.mock("../services/EventService");

describe("EventsTab Component", () => {
    let mockEventService: any;
    const mockToken = "test-token";

    beforeEach(() => {
        mockEventService = {
            connect: jest.fn(),
            on: jest.fn((listener) => {
                // Call listener with a test event
                setTimeout(() => {
                    listener({
                        type: "startup",
                        source: "madre",
                        severity: "info",
                        request_id: "req-123",
                        timestamp: new Date().toISOString(),
                    });
                }, 0);
                return jest.fn(); // unsubscribe
            }),
            setFilter: jest.fn(),
            disconnect: jest.fn(),
            getRequestId: jest.fn(() => "req-123"),
            isConnected: jest.fn(() => true),
            getReconnectAttempts: jest.fn(() => 0),
        };

        (EventServiceModule.EventService as any).mockImplementation(() => mockEventService);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test("renders connection status", async () => {
        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText(/Connected/)).toBeInTheDocument();
        });
    });

    test("displays events from stream", async () => {
        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText("startup")).toBeInTheDocument();
        });
    });

    test("shows event details", async () => {
        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText("madre")).toBeInTheDocument();
            expect(screen.getByText(/req-123/)).toBeInTheDocument();
        });
    });

    test("allows filtering by source", async () => {
        render(<EventsTab token={mockToken} />);

        const sourceInput = screen.getByPlaceholderText("Filter by source...");
        await userEvent.type(sourceInput, "shubniggurath");

        expect(mockEventService.setFilter).toHaveBeenCalledWith({
            source: "shubniggurath",
            event_type: undefined,
            severity: undefined,
        });
    });

    test("allows filtering by event type", async () => {
        render(<EventsTab token={mockToken} />);

        const typeInput = screen.getByPlaceholderText("Filter by type...");
        await userEvent.type(typeInput, "error");

        expect(mockEventService.setFilter).toHaveBeenCalledWith({
            source: "",
            event_type: "error",
            severity: undefined,
        });
    });

    test("allows filtering by severity", async () => {
        render(<EventsTab token={mockToken} />);

        const severityInput = screen.getByPlaceholderText("Filter by severity...");
        await userEvent.type(severityInput, "critical");

        expect(mockEventService.setFilter).toHaveBeenCalledWith({
            source: "",
            event_type: "",
            severity: "critical",
        });
    });

    test("clears events on clear button click", async () => {
        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText("startup")).toBeInTheDocument();
        });

        const clearButton = screen.getByRole("button", { name: "Clear" });
        fireEvent.click(clearButton);

        expect(screen.getByText(/No events yet/)).toBeInTheDocument();
    });

    test("auto-scroll checkbox works", async () => {
        render(<EventsTab token={mockToken} />);

        const autoScrollCheckbox = screen.getByRole("checkbox");
        expect(autoScrollCheckbox).toBeChecked();

        fireEvent.click(autoScrollCheckbox);
        expect(autoScrollCheckbox).not.toBeChecked();
    });

    test("displays event icons based on type", async () => {
        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText("🚀")).toBeInTheDocument(); // startup icon
        });
    });

    test("shows event timestamps", async () => {
        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText(/:\d{2}/)).toBeInTheDocument(); // Time format MM:SS
        });
    });

    test("displays request ID in events", async () => {
        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText(/Request ID: req-12/)).toBeInTheDocument();
        });
    });

    test("shows total event count", async () => {
        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText(/Total events: \d+/)).toBeInTheDocument();
        });
    });

    test("disconnects on unmount", () => {
        const { unmount } = render(<EventsTab token={mockToken} />);

        unmount();

        expect(mockEventService.disconnect).toHaveBeenCalled();
    });

    test("displays reconnect attempts", async () => {
        mockEventService.getReconnectAttempts = jest.fn(() => 2);

        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText(/Reconnect attempts: 2/)).toBeInTheDocument();
        });
    });

    test("color-codes events by severity", async () => {
        const { container } = render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            const eventDiv = container.querySelector("[class*='bg-blue-900']");
            expect(eventDiv).toBeInTheDocument(); // info severity = blue
        });
    });

    test("handles multiple events", async () => {
        const events = [
            {
                type: "startup",
                source: "madre",
                severity: "info",
                request_id: "req-1",
                timestamp: new Date().toISOString(),
            },
            {
                type: "error",
                source: "shubniggurath",
                severity: "error",
                request_id: "req-2",
                timestamp: new Date().toISOString(),
            },
        ];

        mockEventService.on = jest.fn((listener) => {
            events.forEach((event) => {
                setTimeout(() => listener(event), 0);
            });
            return jest.fn();
        });

        render(<EventsTab token={mockToken} />);

        await waitFor(() => {
            expect(screen.getByText("startup")).toBeInTheDocument();
            expect(screen.getByText("error")).toBeInTheDocument();
        });

        expect(screen.getByText(/Total events: 2/)).toBeInTheDocument();
    });
});

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DegradedModeBanner } from "./DegradedModeBanner";

describe("DegradedModeBanner Component", () => {
    test("does not render when visible=false", () => {
        const { container } = render(
            <DegradedModeBanner visible={false} hint="Test hint" />
        );
        expect(container.firstChild).toBeEmptyDOMNode();
    });

    test("renders when visible=true", () => {
        render(<DegradedModeBanner visible={true} hint="Test hint" />);
        expect(screen.getByText(/DEGRADED MODE ACTIVE/)).toBeInTheDocument();
        expect(screen.getByText("Test hint")).toBeInTheDocument();
    });

    test("displays default hint when not provided", () => {
        render(<DegradedModeBanner visible={true} />);
        expect(screen.getByText(/Limited functionality - using fallback/)).toBeInTheDocument();
    });

    test("displays custom hint when provided", () => {
        render(<DegradedModeBanner visible={true} hint="Connection timeout occurred" />);
        expect(screen.getByText("Connection timeout occurred")).toBeInTheDocument();
    });

    test("calls onDismiss when dismiss button clicked", () => {
        const mockOnDismiss = jest.fn();
        render(
            <DegradedModeBanner
                visible={true}
                hint="Test"
                onDismiss={mockOnDismiss}
            />
        );

        const dismissBtn = screen.getByRole("button", { name: /dismiss/i });
        fireEvent.click(dismissBtn);

        expect(mockOnDismiss).toHaveBeenCalled();
    });

    test("auto-dismisses after specified duration", async () => {
        const mockOnDismiss = jest.fn();
        render(
            <DegradedModeBanner
                visible={true}
                hint="Test"
                autoDismissMs={100}
                onDismiss={mockOnDismiss}
            />
        );

        expect(screen.getByText(/DEGRADED MODE ACTIVE/)).toBeInTheDocument();

        await waitFor(
            () => {
                expect(mockOnDismiss).toHaveBeenCalled();
            },
            { timeout: 200 }
        );
    });

    test("does not auto-dismiss when autoDismissMs=0", async () => {
        const mockOnDismiss = jest.fn();
        render(
            <DegradedModeBanner
                visible={true}
                hint="Test"
                autoDismissMs={0}
                onDismiss={mockOnDismiss}
            />
        );

        await new Promise((resolve) => setTimeout(resolve, 100));
        expect(mockOnDismiss).not.toHaveBeenCalled();
        expect(screen.getByText(/DEGRADED MODE ACTIVE/)).toBeInTheDocument();
    });

    test("hides when visible transitions from true to false", async () => {
        const { rerender } = render(
            <DegradedModeBanner visible={true} hint="Test" autoDismissMs={0} />
        );
        expect(screen.getByText(/DEGRADED MODE ACTIVE/)).toBeInTheDocument();

        rerender(<DegradedModeBanner visible={false} hint="Test" autoDismissMs={0} />);

        await waitFor(() => {
            expect(screen.queryByText(/DEGRADED MODE ACTIVE/)).not.toBeInTheDocument();
        });
    });

    test("cancels auto-dismiss timer when component unmounts", async () => {
        jest.useFakeTimers();
        const mockOnDismiss = jest.fn();

        const { unmount } = render(
            <DegradedModeBanner
                visible={true}
                hint="Test"
                autoDismissMs={5000}
                onDismiss={mockOnDismiss}
            />
        );

        unmount();
        jest.runAllTimers();

        expect(mockOnDismiss).not.toHaveBeenCalled();
        jest.useRealTimers();
    });

    test("applies correct CSS classes", () => {
        const { container } = render(
            <DegradedModeBanner visible={true} hint="Test" autoDismissMs={0} />
        );
        const banner = container.querySelector("div");
        expect(banner).toHaveClass("bg-yellow-950", "border-2", "border-yellow-500", "rounded-lg");
    });

    test("warning icon is displayed", () => {
        render(<DegradedModeBanner visible={true} />);
        expect(screen.getByText(/⚠️/)).toBeInTheDocument();
    });

    test("close icon is displayed", () => {
        render(<DegradedModeBanner visible={true} />);
        expect(screen.getByText(/✕/)).toBeInTheDocument();
    });
});

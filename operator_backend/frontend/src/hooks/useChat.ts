import { useState } from "react";
import { sendChat } from "../api/canonical";
import { ChatResponse, ErrorResponse } from "../types/canonical";

export interface ChatMessage {
    role: "user" | "assistant";
    content: string;
    status?: "ok" | "degraded" | "error";
    requestId?: string;
    routeTaken?: string;
    degraded?: boolean;
    errors?: Array<{ step: string; hint: string }>;
}

export interface UseChatOptions {
    maxMessageLength?: number;
}

export const useChat = (options: UseChatOptions = {}) => {
    const { maxMessageLength = 4096 } = options;
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [loadingStatus, setLoadingStatus] = useState("");
    const [mode, setMode] = useState("default");
    const [degradedMode, setDegradedMode] = useState(false);
    const [degradedHint, setDegradedHint] = useState("");

    const send = async () => {
        if (!input.trim()) return;
        if (input.length > maxMessageLength) {
            alert(`Message too long (max ${maxMessageLength} chars)`);
            return;
        }

        const userMsg = input;
        setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
        setInput("");
        setLoading(true);
        setLoadingStatus("Sending to Madre...");

        const result = await sendChat(userMsg, mode);

        if ("error" in result) {
            const err = result as ErrorResponse;
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: `❌ Error: ${err.error || "Request failed"}`,
                    status: "error"
                },
            ]);
        } else {
            const resp = result as any;  // Unified response type

            // Detect if response is unified format (has ok, route_taken, degraded)
            const isUnified =
                resp.ok !== undefined &&
                resp.route_taken !== undefined &&
                resp.degraded !== undefined;

            // Extract fields
            const isDegraded = isUnified ? resp.degraded : resp.response?.includes("[DEGRADED]");
            const routeTaken = isUnified ? resp.route_taken : "unknown";
            const requestId = isUnified ? resp.request_id : "N/A";
            const msgContent = isUnified ? resp.data?.response : resp.response;
            const errors = isUnified ? resp.errors : [];

            // Update global degraded state
            setDegradedMode(isDegraded);
            setDegradedHint(errors.length > 0 ? errors[0].hint : "Fallback endpoint active");

            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: msgContent,
                    status: isDegraded ? "degraded" : "ok",
                    requestId,
                    routeTaken,
                    degraded: isDegraded,
                    errors
                }
            ]);
        }

        setLoading(false);
        setLoadingStatus("");
    };

    const clearMessages = () => {
        setMessages([]);
        setDegradedMode(false);
        setDegradedHint("");
    };

    return {
        messages,
        input,
        loading,
        loadingStatus,
        mode,
        degradedMode,
        degradedHint,
        send,
        setInput,
        setMode,
        setDegradedMode,
        clearMessages,
    };
};

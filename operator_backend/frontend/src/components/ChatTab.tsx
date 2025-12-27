import React, { useState, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import { DegradedModeBanner } from "./DegradedModeBanner";

export const ChatTab: React.FC = () => {
    const {
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
    } = useChat({ maxMessageLength: 4096 });

    const [streamingText, setStreamingText] = useState("");

    // Simulate streaming response when loading
    useEffect(() => {
        if (!loading) {
            setStreamingText("");
            return;
        }

        const streamMessages = [
            "Processing query",
            "Checking madre health",
            "Routing to switch",
            "Generating response",
            "Streaming tokens: 12/100",
        ];

        let idx = 0;
        const interval = setInterval(() => {
            if (idx < streamMessages.length) {
                setStreamingText(streamMessages[idx]);
                idx++;
            } else {
                idx = 0; // Loop
            }
        }, 800);

        return () => clearInterval(interval);
    }, [loading]);

    const handleSend = () => send();

    return (
        <div className="h-full flex flex-col">
            {/* Degraded Mode Banner */}
            <DegradedModeBanner
                visible={degradedMode}
                hint={degradedHint}
                autoDismissMs={5000}
                onDismiss={() => setDegradedMode(false)}
            />

            {loading && (
                <div className="mb-3 p-3 bg-blue-900 border border-blue-500 rounded text-sm text-blue-100 animate-pulse">
                    ⏳ {loadingStatus}
                </div>
            )}

            <div className="mb-4 flex gap-2">
                {["default", "analyze", "reasoning"].map((m) => (
                    <button
                        key={m}
                        onClick={() => setMode(m)}
                        disabled={loading}
                        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${mode === m ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-300 hover:bg-slate-600"} ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
                    >
                        {m}
                    </button>
                ))}
            </div>

            <div className="flex-1 overflow-y-auto bg-slate-900 rounded-lg p-4 mb-4 space-y-4 border border-slate-700">
                {messages.length === 0 ? (
                    <div className="text-slate-400 text-center py-12 flex flex-col items-center gap-3">
                        <div className="text-3xl">💬</div>
                        <p className="text-sm">No messages yet. Start a conversation!</p>
                        <p className="text-xs text-slate-500">Tip: Try asking about system status</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className="flex flex-col space-y-2">
                            <div
                                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div
                                    className={`max-w-md px-4 py-3 rounded-lg border-l-4 ${msg.role === "user" ? "bg-blue-600 text-white border-blue-500" : msg.status === "degraded" ? "bg-yellow-900 text-yellow-100 border-yellow-600" : msg.status === "error" ? "bg-red-900 text-red-100 border-red-600" : msg.routeTaken === "tentaculo_link" ? "bg-emerald-900 text-emerald-100 border-emerald-600" : msg.routeTaken === "madre" ? "bg-purple-900 text-purple-100 border-purple-600" : "bg-slate-700 text-slate-100 border-slate-600"}`}
                                >
                                    <p className="text-sm leading-relaxed">{msg.content}</p>
                                </div>
                            </div>
                            {msg.role === "assistant" && (
                                <div className="flex gap-2 px-4 flex-wrap text-xs">
                                    <span className="bg-slate-800 text-slate-300 px-2 py-1 rounded border border-slate-700">
                                        Route: {msg.routeTaken || "unknown"}
                                    </span>
                                    {msg.requestId && (
                                        <span className="bg-slate-800 text-slate-300 px-2 py-1 rounded border border-slate-700">
                                            ID: {msg.requestId.substring(0, 8)}...
                                        </span>
                                    )}
                                    {msg.status && (
                                        <span className={`px-2 py-1 rounded border ${msg.status === "degraded" ? "bg-yellow-900 text-yellow-300 border-yellow-700" :
                                                msg.status === "error" ? "bg-red-900 text-red-300 border-red-700" :
                                                    "bg-green-900 text-green-300 border-green-700"
                                            }`}>
                                            Status: {msg.status}
                                        </span>
                                    )}
                                </div>
                            )}
                        </div>
                    ))
                )}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800 text-slate-200 px-4 py-3 rounded-lg border border-slate-700 animate-pulse flex gap-2">
                            <span className="inline-block">▌</span>
                            <span>{streamingText || "Processing..."}</span>
                        </div>
                    </div>
                )}
            </div>

            <div className="flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Type a message (max 4KB)..."
                    disabled={loading}
                    className="flex-1 bg-slate-700 border border-slate-600 rounded px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                />
                <button
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white px-6 py-2 rounded font-medium transition-colors"
                >
                    Send
                </button>
            </div>
        </div>
    );
};

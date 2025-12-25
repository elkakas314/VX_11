import React from "react";
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

            <div className="flex-1 overflow-y-auto bg-slate-800 rounded-lg p-4 mb-4 space-y-3">
                {messages.length === 0 ? (
                    <div className="text-slate-400 text-center py-8">
                        <p>No messages yet. Start a conversation!</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className="flex flex-col space-y-1">
                            <div
                                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div
                                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg border-l-4 ${msg.role === "user" ? "bg-blue-600 text-white border-blue-500" : msg.status === "degraded" ? "bg-yellow-900 text-yellow-100 border-yellow-500" : msg.status === "error" ? "bg-red-900 text-red-100 border-red-500" : msg.routeTaken === "tentaculo_link" ? "bg-green-900 text-green-100 border-green-500" : msg.routeTaken === "madre" ? "bg-slate-700 text-slate-100 border-slate-600" : "bg-slate-700 text-slate-100 border-slate-600"}`}
                                >
                                    <p className="text-sm">{msg.content}</p>
                                </div>
                            </div>
                            {msg.requestId && (
                                <div className="text-xs text-slate-500 px-4">
                                    ID: {msg.requestId.substring(0, 8)}... | Route: {msg.routeTaken}
                                </div>
                            )}
                        </div>
                    ))
                )}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-700 text-slate-100 px-4 py-2 rounded-lg animate-pulse">
                            <span>Waiting for response...</span>
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

import React, { useState } from "react";
import { sendChat } from "../api/canonical";
import { ChatResponse, ErrorResponse } from "../types/canonical";

export const ChatTab: React.FC = () => {
    const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [mode, setMode] = useState("default");

    const handleSend = async () => {
        if (!input.trim()) return;

        // Add user message
        const userMsg = input;
        setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
        setInput("");
        setLoading(true);

        // Send to backend
        const result = await sendChat(userMsg, mode);

        if ("error" in result) {
            const err = result as ErrorResponse;
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: `❌ Error: ${err.error || "Request failed"}` },
            ]);
        } else {
            const resp = result as ChatResponse;
            setMessages((prev) => [...prev, { role: "assistant", content: resp.response }]);
        }

        setLoading(false);
    };

    return (
        <div className="h-full flex flex-col">
            {/* Mode selector */}
            <div className="mb-4 flex gap-2">
                {["default", "analyze", "reasoning"].map((m) => (
                    <button
                        key={m}
                        onClick={() => setMode(m)}
                        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${mode === m
                                ? "bg-blue-600 text-white"
                                : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                            }`}
                    >
                        {m}
                    </button>
                ))}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto bg-slate-800 rounded-lg p-4 mb-4 space-y-3">
                {messages.length === 0 ? (
                    <div className="text-slate-400 text-center py-8">
                        <p>No messages yet. Start a conversation!</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div
                                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${msg.role === "user"
                                        ? "bg-blue-600 text-white"
                                        : "bg-slate-700 text-slate-100"
                                    }`}
                            >
                                <p className="text-sm">{msg.content}</p>
                            </div>
                        </div>
                    ))
                )}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-700 text-slate-100 px-4 py-2 rounded-lg">
                            <p className="text-sm">⏳ Processing...</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Type a message..."
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

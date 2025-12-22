import { useEffect, useState } from "react";
import { subscribeToEvents } from "../api/canonical";
import { SystemEvent } from "../types/canonical";

export const EventsTab: React.FC = () => {
    const [events, setEvents] = useState<SystemEvent[]>([]);
    const [paused, setPaused] = useState(false);
    const [filter, setFilter] = useState("");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let eventSource: EventSource | null = null;

        const startSSE = () => {
            eventSource = subscribeToEvents(
                (event) => {
                    if (!paused) {
                        setEvents((prev) => [event, ...prev].slice(0, 100)); // Keep last 100
                    }
                },
                (err) => {
                    setError(err);
                },
                () => {
                    console.log("EventSource closed");
                }
            );
        };

        if (!paused) {
            startSSE();
        }

        return () => {
            if (eventSource) {
                eventSource.close();
            }
        };
    }, [paused]);

    const filteredEvents = events.filter(
        (e) => !filter || e.source.toLowerCase().includes(filter.toLowerCase()) || e.type.toLowerCase().includes(filter.toLowerCase())
    );

    return (
        <div className="space-y-4">
            {error && (
                <div className="p-4 bg-red-900 border-l-4 border-red-500 rounded">
                    <p className="text-red-100 text-sm">{error}</p>
                </div>
            )}

            {/* Controls */}
            <div className="flex gap-2 flex-wrap">
                <button
                    onClick={() => setPaused(!paused)}
                    className={`px-4 py-2 rounded font-medium transition-colors ${paused
                        ? "bg-red-600 hover:bg-red-700 text-white"
                        : "bg-green-600 hover:bg-green-700 text-white"
                        }`}
                >
                    {paused ? "⏸ Resume" : "▶ Pause"}
                </button>

                <input
                    type="text"
                    placeholder="Filter by source or type..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="flex-1 min-w-[200px] bg-slate-700 border border-slate-600 rounded px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                <button
                    onClick={() => setEvents([])}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded font-medium transition-colors"
                >
                    Clear
                </button>
            </div>

            {/* Events List */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 max-h-[600px] overflow-y-auto">
                {filteredEvents.length === 0 ? (
                    <div className="p-8 text-center text-slate-400">
                        {events.length === 0 ? "Waiting for events..." : "No events match filter"}
                    </div>
                ) : (
                    <div className="divide-y divide-slate-700">
                        {filteredEvents.map((event, idx) => (
                            <div key={idx} className="p-4 hover:bg-slate-700/50 transition-colors">
                                <div className="flex items-start justify-between mb-2">
                                    <div>
                                        <p className="text-white font-semibold">{event.type}</p>
                                        <p className="text-slate-400 text-sm">{event.source}</p>
                                    </div>
                                    <p className="text-slate-400 text-xs whitespace-nowrap">
                                        {new Date(event.timestamp).toLocaleTimeString()}
                                    </p>
                                </div>

                                {Object.keys(event.data).length > 0 && (
                                    <details className="cursor-pointer">
                                        <summary className="text-slate-300 text-sm hover:text-white transition-colors">
                                            Details ({Object.keys(event.data).length})
                                        </summary>
                                        <pre className="bg-slate-900 rounded p-3 mt-2 text-xs text-slate-200 overflow-x-auto">
                                            {JSON.stringify(event.data, null, 2)}
                                        </pre>
                                    </details>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Status */}
            <div className="text-slate-400 text-xs">
                {paused ? "⏸ Paused" : "▶ Streaming"} • Showing {filteredEvents.length} of {events.length} events
            </div>
        </div>
    );
};

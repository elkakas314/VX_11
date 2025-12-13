/**
 * Forensic Timeline — Lazy-loaded, chronological events
 * Features:
 * - Lazy load: 100 items initially, 50 more on scroll
 * - Filters: by module, severity
 * - Correlation: small grafo if system.correlation_update arrives
 * - Lense of Time: timestamp selector → snapshot request
 */

import React, { useEffect, useState, useRef, useCallback } from "react";
import { TimelineEvent, CorrelationUpdate, HormigueroLevel } from "../../types/v8_1_extensions";

const BATCH_SIZE = 50;
const INITIAL_LOAD = 100;

interface ForensicTimelineProps {
    events: TimelineEvent[];
    correlations?: CorrelationUpdate | null;
    onSnapshotRequest?: (timestamp: number) => void;
}

export const ForensicTimeline: React.FC<ForensicTimelineProps> = ({
    events = [],
    correlations = null,
    onSnapshotRequest,
}) => {
    const [displayedCount, setDisplayedCount] = useState(INITIAL_LOAD);
    const [selectedModule, setSelectedModule] = useState<string | null>(null);
    const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);
    const [selectedTimestamp, setSelectedTimestamp] = useState<number | null>(null);
    const [snapshotLoading, setSnapshotLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Filtered events
    const filtered = events
        .filter((e) => !selectedModule || e.module === selectedModule)
        .filter((e) => !selectedSeverity || e.severity === selectedSeverity)
        .slice(0, displayedCount);

    // Unique modules and severities for filters
    const modules = Array.from(new Set(events.map((e) => e.module)));
    const severities = Array.from(new Set(events.map((e) => e.severity)));

    // Scroll detection for lazy load
    const handleScroll = useCallback(() => {
        if (!scrollRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
        if (scrollHeight - scrollTop <= clientHeight * 1.2 && displayedCount < events.length) {
            setDisplayedCount((prev) => Math.min(prev + BATCH_SIZE, events.length));
        }
    }, [displayedCount, events.length]);

    useEffect(() => {
        const ref = scrollRef.current;
        if (!ref) return;
        ref.addEventListener("scroll", handleScroll);
        return () => ref.removeEventListener("scroll", handleScroll);
    }, [handleScroll]);

    const handleSnapshotRequest = (timestamp: number) => {
        setSelectedTimestamp(timestamp);
        setSnapshotLoading(true);
        onSnapshotRequest?.(timestamp);
        setTimeout(() => setSnapshotLoading(false), 2000); // Fallback timeout
    };

    return (
        <div className="flex flex-col gap-4 p-4">
            <div className="text-lg font-semibold">Forensic Timeline</div>

            {/* Filters */}
            <div className="flex gap-4 flex-wrap">
                <select
                    value={selectedModule ?? ""}
                    onChange={(e) => setSelectedModule(e.target.value || null)}
                    className="px-3 py-1 border rounded text-sm"
                >
                    <option value="">All Modules</option>
                    {modules.map((m) => (
                        <option key={m} value={m}>
                            {m}
                        </option>
                    ))}
                </select>

                <select
                    value={selectedSeverity ?? ""}
                    onChange={(e) => setSelectedSeverity(e.target.value || null)}
                    className="px-3 py-1 border rounded text-sm"
                >
                    <option value="">All Severities</option>
                    {severities.map((s) => (
                        <option key={s} value={s}>
                            {s}
                        </option>
                    ))}
                </select>
            </div>

            {/* Lense of Time */}
            <div className="p-3 bg-blue-50 rounded border border-blue-200">
                <div className="text-sm font-semibold mb-2">🕐 Lense of Time</div>
                <div className="flex gap-2">
                    <input
                        type="text"
                        placeholder="Timestamp (ms)"
                        value={selectedTimestamp ?? ""}
                        onChange={(e) => setSelectedTimestamp(e.target.value ? parseInt(e.target.value) : null)}
                        className="px-2 py-1 border rounded text-sm"
                    />
                    <button
                        onClick={() => selectedTimestamp && handleSnapshotRequest(selectedTimestamp)}
                        disabled={!selectedTimestamp || snapshotLoading}
                        className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:bg-gray-400"
                    >
                        {snapshotLoading ? "⏳ Loading..." : "Snapshot"}
                    </button>
                </div>
                {snapshotLoading && <div className="text-xs text-gray-600 mt-2">Fetching state snapshot...</div>}
            </div>

            {/* Timeline Events (Lazy Loaded) */}
            <div
                ref={scrollRef}
                className="max-h-96 overflow-y-auto border rounded p-3 space-y-2 bg-gray-50"
            >
                {filtered.length === 0 ? (
                    <div className="text-sm text-gray-500">No events match filter</div>
                ) : (
                    filtered.map((event) => (
                        <div
                            key={event.id}
                            className="p-2 bg-white border-l-4 rounded text-sm"
                            style={{
                                borderLeftColor:
                                    event.severity === "critical"
                                        ? "#dc2626"
                                        : event.severity === "error"
                                            ? "#f97316"
                                            : event.severity === "warning"
                                                ? "#eab308"
                                                : "#6b7280",
                            }}
                        >
                            <div className="flex justify-between">
                                <span className="font-semibold text-xs">{event.module}</span>
                                <span className="text-xs text-gray-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
                            </div>
                            <div className="text-xs mt-1">{event.message}</div>
                        </div>
                    ))
                )}
            </div>

            {displayedCount < events.length && (
                <div className="text-xs text-gray-600 text-center">
                    Showing {displayedCount} of {events.length} events (scroll to load more)
                </div>
            )}

            {/* Correlation Graph (Stub) */}
            {correlations && correlations.nodes.length > 0 && (
                <div className="p-3 bg-purple-50 rounded border border-purple-200">
                    <div className="text-sm font-semibold mb-2">📊 Correlation ({correlations.nodes.length} nodes)</div>
                    <div className="text-xs text-gray-600">
                        Nodes: {correlations.nodes.map((n) => n.label).join(", ")}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                        Edges: {correlations.edges.length > 0 ? "Connected" : "None"}
                    </div>
                </div>
            )}
        </div>
    );
};

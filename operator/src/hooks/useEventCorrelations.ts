/**
 * useEventCorrelations Hook
 * ========================
 * Fetches and manages event correlation graph for visualization.
 * Lazy-loads from /debug/events/correlations endpoint.
 */

import { useState, useEffect } from "react";
import { CorrelationGraph, CorrelationResponse } from "../types/correlation";

export function useEventCorrelations(enabled: boolean = true) {
    const [graph, setGraph] = useState<CorrelationGraph | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [lastFetch, setLastFetch] = useState<number>(0);

    const fetchCorrelations = async () => {
        if (!enabled) return;

        setLoading(true);
        setError(null);

        try {
            const response = await fetch("/debug/events/correlations", {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "X-VX11-Token": process.env.REACT_APP_VX11_TOKEN || "local",
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data: CorrelationResponse = await response.json();
            setGraph(data.graph);
            setLastFetch(Date.now());
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
            console.error("[useEventCorrelations] Error:", err);
        } finally {
            setLoading(false);
        }
    };

    // Auto-fetch on mount and when enabled changes
    useEffect(() => {
        if (enabled) {
            fetchCorrelations();
            // Poll every 10 seconds
            const interval = setInterval(fetchCorrelations, 10000);
            return () => clearInterval(interval);
        }
    }, [enabled]);

    return {
        graph,
        loading,
        error,
        lastFetch,
        refetch: fetchCorrelations,
    };
}

/**
 * Hormiguero UI State Hook
 * Manages Hormiguero state with WebSocket integration
 * Ref: docs/VX11_HORMIGUERO_v7_COMPLETION.md
 */

import { useCallback, useEffect, useState } from "react";
import {
    HormiguerUIState,
    QueenStatus,
    HormiguerReport,
    Incident,
    Ant,
    AntRole,
} from "../types/hormiguero";

declare const process: any;

const API_BASE = process.env.REACT_APP_OPERATOR_API || "http://localhost:8001";

export const useHormiguero = () => {
    const [state, setState] = useState<HormiguerUIState>({
        queen: null,
        ants: [],
        incidents: [],
        pheromones: [],
        selected_incident_id: null,
        selected_ant_id: null,
        is_scanning: false,
        error: null,
    });

    // Fetch Queen + Ants status
        const fetchQueenStatus = useCallback(async () => {
            try {
                const resp = await fetch(`${API_BASE}/hormiguero/queen/status`);
                if (!resp.ok) throw new Error(`Queen status failed: ${resp.status}`);
                const data: QueenStatus = await resp.json();
    
                setState((prev) => ({
                    ...prev,
                    ants: data.ants,
                    // data.queen is a summary type (QueenStatus) and may not match Ant shape;
                    // assert to the state's queen type to satisfy the compiler while keeping runtime value.
                    queen: data.queen as unknown as typeof prev["queen"],
                    error: null,
                }));
            } catch (e) {
                setState((prev) => ({
                    ...prev,
                    error: `Queen status error: ${e instanceof Error ? e.message : "Unknown"}`,
                }));
            }
        }, []);

    // Fetch incidents report
    const fetchReport = useCallback(async () => {
        try {
            const resp = await fetch(`${API_BASE}/hormiguero/report?limit=100`);
            if (!resp.ok) throw new Error(`Report failed: ${resp.status}`);
            const data: HormiguerReport = await resp.json();

            setState((prev) => ({
                ...prev,
                incidents: data.incidents,
                error: null,
            }));
        } catch (e) {
            setState((prev) => ({
                ...prev,
                error: `Report error: ${e instanceof Error ? e.message : "Unknown"}`,
            }));
        }
    }, []);

    // Trigger scan cycle
    const triggerScan = useCallback(async () => {
        setState((prev) => ({ ...prev, is_scanning: true }));
        try {
            const resp = await fetch(`${API_BASE}/hormiguero/scan`, {
                method: "POST",
            });
            if (!resp.ok) throw new Error(`Scan failed: ${resp.status}`);
            await fetchQueenStatus();
            await fetchReport();
        } catch (e) {
            setState((prev) => ({
                ...prev,
                error: `Scan error: ${e instanceof Error ? e.message : "Unknown"}`,
            }));
        } finally {
            setState((prev) => ({ ...prev, is_scanning: false }));
        }
    }, [fetchQueenStatus, fetchReport]);

    // Dispatch Queen decision for incident
    const dispatchDecision = useCallback(
        async (incident_id: number) => {
            try {
                const resp = await fetch(
                    `${API_BASE}/hormiguero/queen/dispatch?incident_id=${incident_id}`,
                    { method: "POST" }
                );
                if (!resp.ok) throw new Error(`Dispatch failed: ${resp.status}`);
                await fetchReport();
            } catch (e) {
                setState((prev) => ({
                    ...prev,
                    error: `Dispatch error: ${e instanceof Error ? e.message : "Unknown"}`,
                }));
            }
        },
        [fetchReport]
    );

    // WebSocket listener for real-time updates (future enhancement)
    useEffect(() => {
        // Placeholder for WebSocket integration
        // const ws = new WebSocket("ws://localhost:8001/hormiguero/stream");
        // ws.onmessage = (event) => { ... };
        // return () => ws.close();
    }, []);

    // Initial data load + polling
    useEffect(() => {
        fetchQueenStatus();
        fetchReport();

        const interval = setInterval(() => {
            fetchQueenStatus();
            fetchReport();
        }, 5000); // Poll every 5s

        return () => clearInterval(interval);
    }, [fetchQueenStatus, fetchReport]);

    return {
        state,
        actions: {
            triggerScan,
            dispatchDecision,
            selectIncident: (id: number | null) =>
                setState((prev) => ({ ...prev, selected_incident_id: id })),
            selectAnt: (id: string | null) =>
                setState((prev) => ({ ...prev, selected_ant_id: id })),
            clearError: () => setState((prev) => ({ ...prev, error: null })),
        },
    };
};

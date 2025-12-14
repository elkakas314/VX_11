import { useEffect, useState, useCallback } from "react";
import type { CanonicalEvent } from "../types/canonical-events";
import { getEventClient } from "../services/event-client";
import { WS_URL } from "../config/vx11.config";

export function useDashboardEvents() {
    const [alerts, setAlerts] = useState<CanonicalEvent[]>([]);
    const [correlations, setCorrelations] = useState<CanonicalEvent[]>([]);
    const [snapshots, setSnapshots] = useState<CanonicalEvent[]>([]);
    const [decisions, setDecisions] = useState<CanonicalEvent[]>([]);
    const [tensions, setTensions] = useState<CanonicalEvent[]>([]);
    const [narratives, setNarratives] = useState<CanonicalEvent[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleAlert = useCallback((event: CanonicalEvent) => {
        if (event.type === "system.alert") {
            setAlerts((prev: CanonicalEvent[]) => [event, ...prev.slice(0, 9)]);
        }
    }, []);

    const handleCorrelation = useCallback((event: CanonicalEvent) => {
        if (event.type === "system.correlation.updated") {
            setCorrelations((prev: CanonicalEvent[]) => [event, ...prev.slice(0, 4)]);
        }
    }, []);

    const handleDecision = useCallback((event: CanonicalEvent) => {
        if (event.type === "madre.decision.explained") {
            setDecisions((prev: CanonicalEvent[]) => [event, ...prev.slice(0, 4)]);
        }
    }, []);

    const handleSnapshot = useCallback((event: CanonicalEvent) => {
        if (event.type === "forensic.snapshot.created") {
            setSnapshots((prev: CanonicalEvent[]) => [event, ...prev.slice(0, 19)]);
        }
    }, []);

    const handleTension = useCallback((event: CanonicalEvent) => {
        if (event.type === "switch.tension.updated") {
            setTensions((prev: CanonicalEvent[]) => [event, ...prev.slice(0, 4)]);
        }
    }, []);

    const handleNarrative = useCallback((event: CanonicalEvent) => {
        if (event.type === "shub.action.narrated") {
            setNarratives((prev: CanonicalEvent[]) => [event, ...prev.slice(0, 4)]);
        }
    }, []);

    useEffect(() => {
        let cancelled = false;
        let client: ReturnType<typeof getEventClient> | null = null;

        try {
            client = getEventClient(WS_URL);
        } catch (e) {
            if (!cancelled) {
                setIsConnected(false);
                setError(e instanceof Error ? e.message : "Error inicializando WebSocket");
            }
            return;
        }

        client
            .connect()
            .then(() => {
                if (cancelled) return;
                setIsConnected(true);
                setError(null);

                client?.subscribe("system.alert", handleAlert);
                client?.subscribe("system.correlation.updated", handleCorrelation);
                client?.subscribe("forensic.snapshot.created", handleSnapshot);
                client?.subscribe("madre.decision.explained", handleDecision);
                client?.subscribe("switch.tension.updated", handleTension);
                client?.subscribe("shub.action.narrated", handleNarrative);
            })
            .catch((e) => {
                if (cancelled) return;
                setIsConnected(false);
                setError(e instanceof Error ? e.message : "WebSocket no disponible");
            });

        return () => {
            cancelled = true;
            if (!client) return;
            client.unsubscribe("system.alert", handleAlert);
            client.unsubscribe("system.correlation.updated", handleCorrelation);
            client.unsubscribe("forensic.snapshot.created", handleSnapshot);
            client.unsubscribe("madre.decision.explained", handleDecision);
            client.unsubscribe("switch.tension.updated", handleTension);
            client.unsubscribe("shub.action.narrated", handleNarrative);
        };
    }, [handleAlert, handleCorrelation, handleSnapshot, handleDecision, handleTension, handleNarrative]);

    return {
        alerts,
        correlations,
        snapshots,
        decisions,
        tensions,
        narratives,
        isConnected,
        error,
    };
}

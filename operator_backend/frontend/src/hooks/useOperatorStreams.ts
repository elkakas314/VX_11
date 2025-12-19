import { useEffect, useState } from "react";
import { EVENTS_LIMIT, POLL_INTERVAL_MS } from "../config";
import { fetchSystemStatus, fetchUiEvents, fetchBridgeHealth } from "../services/api";
import { createOperatorWebSocket } from "../services/websocket";
import { useOperatorStore } from "../store/operatorStore";

type EventMessage = { type?: string; payload?: any; data?: any; timestamp?: string };

export function useOperatorStreams() {
  const { setStatus: setStatusStore, setStatusError: setStatusErrorStore, setBridgeHealth: setBridgeHealthStore } = useOperatorStore(
    (state) => state.system
  );
  const { setEvents: setTraceEvents, addEvent } = useOperatorStore((state) => state.traces);
  const { setEvents: setHormigueroEvents } = useOperatorStore((state) => state.hormiguero);
  const [status, setStatus] = useState<any>({});
  const [events, setEvents] = useState<EventMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [bridgeHealth, setBridgeHealth] = useState<any>(null);

  // Poll de estado tentacular
  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const res = await fetchSystemStatus();
        if (!cancelled) {
          if (res?.error) {
            setStatusError(res.error || "status_error");
            setStatusErrorStore(res.error || "status_error");
          } else {
            setStatusError(null);
            setStatusErrorStore(null);
          }
          setStatus(res);
          setStatusStore(res);
        }
      } catch {
        if (!cancelled) {
          setStatusError("status_error");
          setStatusErrorStore("status_error");
        }
      }
    };
    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // Eventos + WebSocket
  useEffect(() => {
    let active = true;
    const pollBridge = async () => {
      try {
        const bh = await fetchBridgeHealth();
        if (active) {
          setBridgeHealth(bh);
          setBridgeHealthStore(bh);
        }
      } catch {
        if (active) {
          const fallback = { ok: false, error: "bridge_unreachable" };
          setBridgeHealth(fallback);
          setBridgeHealthStore(fallback);
        }
      }
    };
    const pollEvents = async () => {
      try {
        const res = await fetchUiEvents();
        if (active && res?.events) {
          setEvents(res.events);
          setEventsError(null);
          setTraceEvents(res.events);
          setHormigueroEvents(res.events);
        }
        if (active && res?.error) setEventsError(res.error);
      } catch {
        if (active) setEventsError("events_error");
      }
    };
    pollEvents();
    pollBridge();
    const interval = setInterval(pollEvents, POLL_INTERVAL_MS * 2);
    const bridgeInterval = setInterval(pollBridge, POLL_INTERVAL_MS * 3);
    const socket = createOperatorWebSocket({
      onMessage: (msg) => {
        try {
          const data = JSON.parse(msg.data);
          if (data?.type === "bootstrap" && Array.isArray(data.events)) {
            setEvents((prev) => [...data.events, ...prev].slice(0, EVENTS_LIMIT));
            setTraceEvents(data.events);
            setHormigueroEvents(data.events);
            return;
          }
          const normalized = data && typeof data === "object" && !data.data && data.payload ? { ...data, data: data.payload } : data;
          setEvents((prev) => [normalized, ...prev].slice(0, EVENTS_LIMIT));
          addEvent(normalized);
        } catch {
          const fallback = { type: "raw", payload: msg.data, timestamp: new Date().toISOString() };
          setEvents((prev) => [fallback, ...prev].slice(0, EVENTS_LIMIT));
          addEvent(fallback);
        }
      },
      onOpen: () => setConnected(true),
      onClose: () => setConnected(false),
    });
    return () => {
      active = false;
      clearInterval(interval);
      clearInterval(bridgeInterval);
      socket?.close();
    };
  }, []);

  return { status, events, connected, statusError, eventsError, bridgeHealth };
}

import { WS_BASE_URL } from "../config";

type OperatorWebSocketOptions = {
  url?: string;
  heartbeatMs?: number;
  maxReconnectMs?: number;
  onMessage: (event: MessageEvent) => void;
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
};

/**
 * WebSocket cliente con reconexión exponencial y heartbeat.
 * Usa WS_BASE_URL por defecto; puede recibir url explícita.
 */
export function createOperatorWebSocket({
  url,
  heartbeatMs = 30_000,
  maxReconnectMs = 30_000,
  onMessage,
  onOpen,
  onClose,
}: OperatorWebSocketOptions) {
  let socket: WebSocket | null = null;
  let stopped = false;
  let reconnectDelay = 2_000;
  let heartbeatId: number | null = null;
  const wsUrl = (url || WS_BASE_URL || "").replace(/\/$/, "") || "";

  const cleanupHeartbeat = () => {
    if (heartbeatId) {
      clearInterval(heartbeatId);
      heartbeatId = null;
    }
  };

  const startHeartbeat = () => {
    if (heartbeatId || !heartbeatMs) return;
    if (typeof window === "undefined") return;
    heartbeatId = window.setInterval(() => {
      try {
        socket?.send(JSON.stringify({ type: "ping", ts: Date.now() }));
      } catch {
        /* noop */
      }
    }, heartbeatMs);
  };

  const connect = () => {
    if (!wsUrl || stopped) return;
    socket = new WebSocket(wsUrl);
    socket.onopen = () => {
      reconnectDelay = 2_000;
      onOpen?.();
      cleanupHeartbeat();
      startHeartbeat();
    };
    socket.onmessage = onMessage;
    socket.onclose = (event) => {
      cleanupHeartbeat();
      onClose?.(event);
      if (stopped) return;
      setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(Math.round(reconnectDelay * 1.5), maxReconnectMs);
    };
    socket.onerror = () => {
      socket?.close();
    };
  };

  connect();

  const close = () => {
    stopped = true;
    cleanupHeartbeat();
    socket?.close();
  };

  return { close };
}

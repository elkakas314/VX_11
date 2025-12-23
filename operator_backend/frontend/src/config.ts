// Canonical VX11 Operator Frontend Config
// Legacy headers (kept for backward compat, but canonical uses JWT Bearer)
export const TOKEN_HEADER = "X-VX11-Token";
export const TOKEN_VALUE = import.meta.env.VITE_VX11_TOKEN || "vx11-local-token";

// Operator Backend URL (default: http://127.0.0.1:8011 in dev, http://operator_backend:8011 in docker)
const DEFAULT_OPERATOR_BASE =
  import.meta.env.VITE_OPERATOR_BASE_URL ||
  import.meta.env.VITE_OPERATOR_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8011";

const normalizedBase = DEFAULT_OPERATOR_BASE.replace(/\/$/, "");

export const OPERATOR_BASE_URL = normalizedBase;

// Legacy settings (kept for compatibility)
export const LINK_BASE_URL = (import.meta.env.VITE_LINK_API_URL as string) || "http://tentaculo_link:8000";

const explicitWs = (import.meta.env.VITE_WS_URL as string) || (import.meta.env.VITE_WS_BASE_URL as string);
export const WS_BASE_URL = explicitWs ? explicitWs.replace(/\/$/, "") : `${normalizedBase.replace(/^http/, "ws")}/ws`;

export const POLL_INTERVAL_MS = 4000;
export const EVENTS_LIMIT = 50;
export const WS_HEARTBEAT_MS = 30_000;

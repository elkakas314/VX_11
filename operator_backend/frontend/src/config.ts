export const TOKEN_HEADER = "X-VX11-Token";
export const TOKEN_VALUE = import.meta.env.VITE_VX11_TOKEN || "vx11-local-token";

// Dentro de Docker se usan los nombres de servicio del compose
export const OPERATOR_BASE_URL = import.meta.env.VITE_OPERATOR_API_URL || "http://operator-backend:8011";
export const LINK_BASE_URL = import.meta.env.VITE_LINK_API_URL || "http://tentaculo_link:8000";

export const POLL_INTERVAL_MS = 4000;
export const EVENTS_LIMIT = 50;

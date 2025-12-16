/**
 * Configuración VX11 para el frontend
 * WebSocket de Tentáculo Link en puerto 8000
 */

export const GATEWAY_PORT = 8000;
export const GATEWAY_URL = `http://localhost:${GATEWAY_PORT}`;
export const WS_URL = `ws://localhost:${GATEWAY_PORT}/ws`;

// URLs de módulos en red Docker (para referencia)
export const MODULES = {
    tentaculo_link: "http://tentaculo-link:8000",
    madre: "http://madre:8001",
    switch: "http://switch:8002",
    hermes: "http://hermes:8003",
    hormiguero: "http://hormiguero:8004",
    manifestator: "http://manifestator:8005",
    mcp: "http://mcp:8006",
    shub: "http://shubniggurath:8007",
    spawner: "http://spawner:8008",
    operator_backend: (import.meta as any).env?.VITE_OPERATOR_BACKEND_URL ?? "http://operator:8011",
};
// Endpoints API principales
export const API_ENDPOINTS = {
    // Health checks
    health: "/health",

    // Events (WebSocket será establecido por el cliente)
    events: "/events",

    // Dashboard data
    dashboard: "/dashboard",
    alerts: "/alerts",
    correlations: "/correlations",
    decisions: "/decisions",
    narratives: "/narratives",
};

// Intervalo de polling para datos en segundos
export const POLLING_INTERVAL = 5000; // 5 segundos

// Timeout para requests en ms
export const REQUEST_TIMEOUT = 8000; // 8 segundos

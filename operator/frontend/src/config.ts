/**
 * Configuration for VX11 Operator Frontend
 * Handles environment variables and API configuration
 */

export const API_CONFIG = {
    // Backend endpoint (fallback chain: env var → localhost → hardcoded)
    // COHERENCIA: All requests go through operator-backend:8011 proxy
    BACKEND_URL: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8011',
    // DEPRECATED: Frontend should NOT access madre directly (use BACKEND_URL instead)
    MADRE_URL: 'http://localhost:8001',  // Only for reference, use backend proxy
    TENTACULO_URL: import.meta.env.VITE_TENTACULO_URL || 'http://localhost:8000',

    // API Timeouts (ms)
    TIMEOUT_HEALTH: 3000,
    TIMEOUT_STATUS: 5000,
    TIMEOUT_CHAT: 30000,
    TIMEOUT_POWER: 10000,
    TIMEOUT_LOGS: 60000,

    // Polling intervals (ms)
    POLL_INTERVAL_STATUS: 2000,
    POLL_INTERVAL_HEALTH: 5000,
    POLL_INTERVAL_FALLBACK: 10000,

    // Feature flags
    ENABLE_MOCK_MODE: import.meta.env.VITE_MOCK_MODE === 'true',
    ENABLE_DEBUG_LOGS: import.meta.env.DEV,

    // Module ports (for fallback routing)
    MODULES_PORTS: {
        madre: 8001,
        switch: 8002,
        hermes: 8003,
        spawner: 8004,
        hormiguero: 8005,
        tentaculo_link: 8000,
        shubniggurath: 8007,
        manifestator: 8010,
        'operator-backend': 8011,
        'operator-frontend': 5173,
        mcp: 8009
    }
}

/**
 * Compile-time endpoint constants (type-safe routing)
 */
export const ENDPOINTS = {
    // Health checks
    HEALTH: '/health',
    MADRE_HEALTH: '/health',

    // Status endpoints
    STATUS: '/api/status',
    VITE_STATUS: '/vx11/status',

    // Chat endpoints
    CHAT: '/api/chat',
    VITE_CHAT: '/vx11/chat',

    // Power control endpoints
    POWER_STATUS: '/madre/power/status',
    POWER_SERVICE_START: (_service: string) => `/madre/power/service/start`,
    POWER_SERVICE_STOP: (_service: string) => `/madre/power/service/stop`,
    POWER_POLICY: '/madre/power/policy/solo_madre/status',

    // Log streaming
    LOGS: '/api/logs',
    VITE_LOGS: '/vx11/logs',

    // Maintenance (rare)
    MAINTENANCE_POST_TASK: '/madre/power/maintenance/post_task'
} as const

export default API_CONFIG

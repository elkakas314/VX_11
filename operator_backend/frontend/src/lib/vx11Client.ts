/**
 * VX11 API Client — Universal wrapper for tentaculo_link (port 8000)
 * 
 * Constraints:
 * - Single entrypoint: http://127.0.0.1:8000 (configurable via env)
 * - Null-safe: all API responses parsed with fallback
 * - Timeouts: 30s default, abort on slow requests
 * - Error handling: never throw, always return {ok: false, errors: [...]}
 */

export interface UnifiedResponse<T = any> {
    ok: boolean;
    request_id?: string;
    route_taken?: string;
    degraded?: boolean;
    provider_used?: string | null;
    model_used?: string | null;
    data?: T;
    errors?: string[];
    timestamp?: string;
}

export interface OperatorObserveService {
    module_name: string;
    status: 'healthy' | 'degraded' | 'down' | 'unknown';
    latency_ms?: number;
    last_check?: string;
}

export interface OperatorObserveResponse {
    ok: boolean;
    timestamp: string;
    degraded: boolean;
    services: OperatorObserveService[];
    provider_used?: string | null;
    model_used?: string | null;
    request_id?: string;
}

export interface OperatorChatRequest {
    message: string;
    context?: Record<string, any>;
    session_id?: string;
}

export interface OperatorChatResponse {
    ok: boolean;
    request_id?: string;
    route_taken?: string;
    degraded?: boolean;
    provider_used?: string | null;
    model_used?: string | null;
    response: string;
    metadata?: Record<string, any>;
    errors?: string[];
}

export interface RoutingEvent {
    id: number;
    route_name: string;
    request_id: string;
    status: string;
    timestamp: string;
    metadata?: Record<string, any>;
}

export interface RoutingEventsResponse {
    ok: boolean;
    events: RoutingEvent[];
    total?: number;
    limit?: number;
}

const getBaseURL = (): string => {
    // Check environment first (Vite exposes env on import.meta.env)
    try {
        if ((import.meta as any)?.env?.VITE_VX11_BASE_URL) {
            return (import.meta as any).env.VITE_VX11_BASE_URL;
        }
    } catch (e) {
        // import.meta may not be available in some runtimes; fall back to default
    }
    // Default to local tentaculo_link
    return 'http://127.0.0.1:8000';
};

const parseJSON = async (res: Response): Promise<any> => {
    try {
        return await res.json();
    } catch (e) {
        return null;
    }
};

export const vx11Client = {
    /**
     * GET /operator/observe — Unified status of all modules
     */
    async getOperatorObserve(): Promise<UnifiedResponse<OperatorObserveService[]>> {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);
        const baseURL = getBaseURL();

        try {
            const res = await fetch(`${baseURL}/operator/observe`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                signal: controller.signal,
            });

            clearTimeout(timeout);

            if (!res.ok) {
                return {
                    ok: false,
                    degraded: true,
                    errors: [`Status ${res.status}`],
                    data: [],
                };
            }

            const json = await parseJSON(res);
            if (!json) {
                return {
                    ok: false,
                    degraded: true,
                    errors: ['Failed to parse JSON'],
                    data: [],
                };
            }

            return {
                ok: true,
                degraded: json.degraded ?? false,
                data: json.data?.services ?? json.services ?? [],
                provider_used: json.provider_used ?? null,
                model_used: json.model_used ?? null,
                request_id: json.request_id,
                timestamp: new Date().toISOString(),
            };
        } catch (e: any) {
            clearTimeout(timeout);
            const message = e.name === 'AbortError' ? 'Timeout (30s)' : String(e);
            return {
                ok: false,
                degraded: true,
                errors: [message],
                data: [],
            };
        }
    },

    /**
     * POST /operator/chat — Send chat message
     */
    async postOperatorChat(
        req: OperatorChatRequest,
    ): Promise<UnifiedResponse<OperatorChatResponse>> {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);
        const baseURL = getBaseURL();

        try {
            const res = await fetch(`${baseURL}/operator/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(req),
                signal: controller.signal,
            });

            clearTimeout(timeout);

            if (!res.ok) {
                return {
                    ok: false,
                    degraded: true,
                    errors: [`Status ${res.status}`],
                };
            }

            const json = await parseJSON(res);
            if (!json) {
                return {
                    ok: false,
                    degraded: true,
                    errors: ['Failed to parse JSON'],
                };
            }

            return {
                ok: true,
                degraded: json.degraded ?? false,
                data: json,
                provider_used: json.provider_used ?? null,
                model_used: json.model_used ?? null,
                request_id: json.request_id,
            };
        } catch (e: any) {
            clearTimeout(timeout);
            const message = e.name === 'AbortError' ? 'Timeout (30s)' : String(e);
            return {
                ok: false,
                degraded: true,
                errors: [message],
            };
        }
    },

    /**
     * GET /hormiguero/report — Routing events from BD
     */
    async getRoutingEvents(limit: number = 50): Promise<RoutingEventsResponse> {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 15000);
        const baseURL = getBaseURL();

        try {
            const res = await fetch(`${baseURL}/hormiguero/report?limit=${limit}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                signal: controller.signal,
            });

            clearTimeout(timeout);

            if (!res.ok) {
                return {
                    ok: false,
                    events: [],
                };
            }

            const json = await parseJSON(res);
            if (!json) {
                return {
                    ok: false,
                    events: [],
                };
            }

            return {
                ok: true,
                events: json.data?.events ?? json.events ?? [],
                total: json.data?.total ?? json.total,
                limit,
            };
        } catch (e: any) {
            clearTimeout(timeout);
            return {
                ok: false,
                events: [],
            };
        }
    },

    /**
     * GET /vx11/status — Aggregate status
     */
    async getVX11Status(): Promise<UnifiedResponse> {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 20000);
        const baseURL = getBaseURL();

        try {
            const res = await fetch(`${baseURL}/vx11/status`, {
                signal: controller.signal,
            });

            clearTimeout(timeout);

            if (!res.ok) {
                return {
                    ok: false,
                    errors: [`Status ${res.status}`],
                };
            }

            const json = await parseJSON(res);
            return {
                ok: true,
                data: json,
            };
        } catch (e: any) {
            clearTimeout(timeout);
            return {
                ok: false,
                errors: [String(e)],
            };
        }
    },

    /**
     * GET /health — Simple health check
     */
    async getHealth(): Promise<{ ok: boolean; status?: string; errors?: string[] }> {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);
        const baseURL = getBaseURL();

        try {
            const res = await fetch(`${baseURL}/health`, {
                signal: controller.signal,
            });

            clearTimeout(timeout);

            if (!res.ok) {
                return {
                    ok: false,
                    errors: [`Status ${res.status}`],
                };
            }

            const json = await parseJSON(res);
            return {
                ok: true,
                status: json?.status,
            };
        } catch (e: any) {
            clearTimeout(timeout);
            return {
                ok: false,
                errors: [String(e)],
            };
        }
    },
};

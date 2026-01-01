/**
 * API Client for VX11 Operator
 * Consumes: tentaculo_link only (via relative URL)
 * No direct calls to backend services
 *
 * API base is configurable (VITE_API_BASE). Defaults:
 * - Dev/Prod: relative to current origin
 */

const TOKEN =
    import.meta.env.VITE_VX11_TOKEN ||
    import.meta.env.VITE_VX11_TENTACULO_TOKEN ||
    'vx11-local-token' // In production: from auth service or config
const TOKEN_HEADER = 'X-VX11-Token'
const RAW_BASE =
    import.meta.env.VITE_API_BASE ||
    import.meta.env.VITE_VX11_API_BASE ||
    import.meta.env.VITE_VX11_API_BASE_URL ||
    ''

export const API_BASE = (RAW_BASE as string).trim()

export const buildApiUrl = (path: string) => {
    const base = API_BASE || ''
    if (base.startsWith('http://') || base.startsWith('https://')) {
        return new URL(path, base).toString()
    }
    if (typeof window !== 'undefined') {
        const origin = window.location.origin
        return new URL(path, `${origin}${base}`).toString()
    }
    return path
}

interface ApiResponse<T> {
    ok: boolean
    data?: T
    error?: string
    status: number
    retryAfterMs?: number
}

class ApiClient {
    private backoffMs = 1000
    private maxBackoffMs = 30000

    async request<T>(
        method: string,
        path: string,
        body?: any,
        options?: { noRetry?: boolean; timeout?: number }
    ): Promise<ApiResponse<T>> {
        const url = buildApiUrl(path)
        const timeout = options?.timeout || 5000

        try {
            const controller = new AbortController()
            const timeoutId = setTimeout(() => controller.abort(), timeout)

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    [TOKEN_HEADER]: TOKEN,
                },
                body: body ? JSON.stringify(body) : undefined,
                signal: controller.signal,
            })

            clearTimeout(timeoutId)

            if (!response.ok) {
                if (response.status === 404 && !options?.noRetry) {
                    if (path.startsWith('/operator/api/v1')) {
                        const legacyPath = path.replace('/operator/api/v1', '/operator/api')
                        return this.request(method, legacyPath, body, {
                            ...options,
                            noRetry: true,
                        })
                    }
                    if (path.startsWith('/operator/api')) {
                        const legacyPath = path.replace('/operator/api', '/operator/api/v1')
                        return this.request(method, legacyPath, body, {
                            ...options,
                            noRetry: true,
                        })
                    }
                }
                let errorDetail = `HTTP ${response.status}`
                try {
                    const errorJson = await response.json()
                    if (errorJson?.status === 'OFF_BY_POLICY') {
                        errorDetail = errorJson.message || 'OFF_BY_POLICY'
                        return {
                            ok: false,
                            data: errorJson,
                            error: errorDetail,
                            status: response.status,
                        }
                    }
                } catch {
                    // ignore JSON parse errors
                }
                return {
                    ok: false,
                    error: errorDetail,
                    status: response.status,
                }
            }

            const data = await response.json()
            this.backoffMs = 1000
            return {
                ok: true,
                data,
                status: response.status,
            }
        } catch (err: any) {
            console.error(`API request failed: ${method} ${path}`, err)
            const retryAfterMs = options?.noRetry
                ? undefined
                : Math.min(this.backoffMs, this.maxBackoffMs)
            if (!options?.noRetry) {
                this.backoffMs = Math.min(this.backoffMs * 2, this.maxBackoffMs)
            }
            return {
                ok: false,
                error: err.message || 'Unknown error',
                status: 0,
                retryAfterMs,
            }
        }
    }

    // Chat endpoint (P0: via /operator/api/chat)
    async chat(message: string, sessionId?: string): Promise<ApiResponse<any>> {
        return this.request('POST', '/operator/api/chat', {
            message,
            session_id: sessionId,
        })
    }

    // Status endpoint (P0: via /operator/api/status)
    async status(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/status')
    }

    // Modules endpoint (P0: via /operator/api/modules)
    async modules(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/modules')
    }

    // Module detail endpoint
    async moduleDetail(name: string): Promise<ApiResponse<any>> {
        return this.request('GET', `/operator/api/modules/${name}`)
    }

    // Events endpoint (P0: via /operator/api/events)
    async events(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/events')
    }

    // Scorecard endpoint (P0: via /operator/api/scorecard)
    async scorecard(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/scorecard')
    }

    // Audit endpoint (P0: via /operator/api/audit)
    async audit(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/audit')
    }

    // Audit detail endpoint
    async auditDetail(id: string): Promise<ApiResponse<any>> {
        return this.request('GET', `/operator/api/audit/${id}`)
    }

    // Download audit endpoint
    async downloadAudit(id: string): Promise<ApiResponse<any>> {
        return this.request('GET', `/operator/api/audit/${id}/download`)
    }

    // Settings endpoint (P0: via /operator/api/settings)
    async settings(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/settings')
    }

    // Update settings endpoint
    async updateSettings(settings: any): Promise<ApiResponse<any>> {
        return this.request('POST', '/operator/api/settings', settings)
    }

    // Topology endpoint (P0: via /operator/api/topology)
    async topology(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/topology')
    }

    // Chat window operations (primary endpoints for Operator UI)
    async chatWindowStatus(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/chat/window/status')
    }

    async chatWindowOpen(services?: string[]): Promise<ApiResponse<any>> {
        return this.request('POST', '/operator/api/chat/window/open', {
            services: services || ['switch', 'hermes'],
        })
    }

    async chatWindowClose(): Promise<ApiResponse<any>> {
        return this.request('POST', '/operator/api/chat/window/close', {})
    }

    // Power state endpoint (legacy, still available)
    async windows(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/window/status')
    }

    // Hormiguero status (optional, may be unavailable)
    async hormigueroStatus(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/hormiguero/status', undefined, {
            timeout: 3000,
        })
    }

    // Hormiguero incidents (optional, for debug mode)
    async hormigueroIncidents(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/hormiguero/incidents?limit=10', undefined, {
            timeout: 3000,
        })
    }

    // Spawner status (read-only)
    async spawnerStatus(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/spawner/status', undefined, { timeout: 5000 })
    }

    // Spawner runs (read-only)
    async spawnerRuns(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/api/spawner/runs', undefined, { timeout: 8000 })
    }

    // Spawner submit (action, Madre-gated)
    async spawnerSubmit(payload: any): Promise<ApiResponse<any>> {
        return this.request('POST', '/operator/api/spawner/submit', payload, { timeout: 12000 })
    }

    // P0 UI checks - verify all endpoints are reachable
    async runP0Checks(): Promise<{
        chat_ask: boolean
        status: boolean
        windows: boolean
        hormiguero_status: boolean
        results: Record<string, any>
    }> {
        const results: Record<string, any> = {}

        const chatResp = await this.chat('ping')
        results.chat_ask = chatResp.ok
        results.chat_ask_error = chatResp.error

        const statusResp = await this.status()
        results.status = statusResp.ok
        results.status_error = statusResp.error

        const windowsResp = await this.windows()
        results.windows = windowsResp.ok
        results.windows_error = windowsResp.error

        const hormigResp = await this.hormigueroStatus()
        results.hormiguero_status = hormigResp.ok
        results.hormiguero_status_error = hormigResp.error

        return {
            chat_ask: results.chat_ask,
            status: results.status,
            windows: results.windows,
            hormiguero_status: results.hormiguero_status,
            results,
        }
    }
}

export const buildAuthHeaders = () => ({
    'Content-Type': 'application/json',
    [TOKEN_HEADER]: TOKEN,
})

export const apiClient = new ApiClient()

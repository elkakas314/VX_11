/**
 * API Client for VX11 Operator
 * Consumes: tentaculo_link:8000 only
 * No direct calls to backend services
 */

const TOKEN = 'vx11-local-token' // In production: from auth service
const BASE_URL = 'http://localhost:8000'

interface ApiResponse<T> {
    ok: boolean
    data?: T
    error?: string
    status: number
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
        const url = `${BASE_URL}${path}`
        const timeout = options?.timeout || 5000

        try {
            const controller = new AbortController()
            const timeoutId = setTimeout(() => controller.abort(), timeout)

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'x-vx11-token': TOKEN,
                },
                body: body ? JSON.stringify(body) : undefined,
                signal: controller.signal,
            })

            clearTimeout(timeoutId)

            if (!response.ok) {
                return {
                    ok: false,
                    error: `HTTP ${response.status}`,
                    status: response.status,
                }
            }

            const data = await response.json()
            return {
                ok: true,
                data,
                status: response.status,
            }
        } catch (err: any) {
            console.error(`API request failed: ${method} ${path}`, err)
            return {
                ok: false,
                error: err.message || 'Unknown error',
                status: 0,
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

    // Power state endpoint (legacy, still available)
    async powerState(): Promise<ApiResponse<any>> {
        return this.request('GET', '/operator/power/state')
    }

    // Hormiguero status (optional, may be unavailable)
    async hormigueroStatus(): Promise<ApiResponse<any>> {
        return this.request('GET', '/hormiguero/status', undefined, { timeout: 3000 })
    }

    // Hormiguero incidents (optional, for debug mode)
    async hormigueroIncidents(): Promise<ApiResponse<any>> {
        return this.request('GET', '/hormiguero/incidents?limit=10', undefined, { timeout: 3000 })
    }

    // P0 UI checks - verify all endpoints are reachable
    async runP0Checks(): Promise<{
        chat_ask: boolean
        status: boolean
        power_state: boolean
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

        const powerResp = await this.powerState()
        results.power_state = powerResp.ok
        results.power_state_error = powerResp.error

        const hormigResp = await this.hormigueroStatus()
        results.hormiguero_status = hormigResp.ok
        results.hormiguero_status_error = hormigResp.error

        return {
            chat_ask: results.chat_ask,
            status: results.status,
            power_state: results.power_state,
            hormiguero_status: results.hormiguero_status,
            results,
        }
    }
}

export const apiClient = new ApiClient()

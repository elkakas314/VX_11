import axios from 'axios'

// COHERENCIA: Frontend uses operator-backend (8011) as proxy, NOT madre directly
// Rationale: Centralized auth, audit trail, session management
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8011'
const TIMEOUT = 5000

class VX11ApiClient {
    private client = axios.create({
        baseURL: API_BASE,
        timeout: TIMEOUT,
        headers: { 'Content-Type': 'application/json' }
    })

    private getAuthHeaders() {
        const token =
            localStorage.getItem('vx11_operator_token') ||
            import.meta.env.VITE_OPERATOR_TOKEN
        const csrf =
            localStorage.getItem('vx11_operator_csrf') ||
            import.meta.env.VITE_OPERATOR_CSRF

        const headers: Record<string, string> = {}
        if (token) headers.Authorization = `Bearer ${token}`
        if (csrf) headers['X-CSRF-Token'] = csrf
        return headers
    }

    private async retry<T>(fn: () => Promise<T>): Promise<T> {
        try {
            return await fn()
        } catch (e) {
            await new Promise(r => setTimeout(r, 1000))
            try {
                return await fn()
            } catch {
                throw e
            }
        }
    }

    async getMadreHealth() {
        return this.retry(() =>
            this.client.get('/health').then(r => r.data).catch(() => ({ status: 'down' }))
        )
    }

    async getStatus() {
        return this.retry(() =>
            this.client
                .get('/api/status', { headers: this.getAuthHeaders() })
                .then(r => r.data)
                .catch((err) => {
                    if (err?.response?.status === 409) {
                        return { status: 'policy', mode: 'low_power' }
                    }
                    throw err
                })
        )
    }

    async getModules() {
        return this.retry(() =>
            this.client
                .get('/api/modules', { headers: this.getAuthHeaders() })
                .then(r => r.data)
                .catch((err) => {
                    if (err?.response?.status === 409) {
                        return { modules: [], policy: 'low_power' }
                    }
                    throw err
                })
        )
    }

    async getPowerStatus() {
        return this.retry(() =>
            this.client
                .get('/api/power/status', { headers: this.getAuthHeaders() })
                .then(r => r.data)
                .catch((err) => {
                    if (err?.response?.status === 409) {
                        return { policy_active: 'solo_madre', policy_enforced: true }
                    }
                    throw err
                })
        )
    }

    async applySoloMadre() {
        return this.retry(() =>
            this.client
                .post('/api/policy/solo_madre/apply', {}, { headers: this.getAuthHeaders() })
                .then(r => r.data)
        )
    }

    async startService(service: string) {
        return this.retry(() =>
            this.client
                .post(`/api/module/${service}/power_up`, {}, { headers: this.getAuthHeaders() })
                .then(r => r.data)
        )
    }

    async stopService(service: string) {
        return this.retry(() =>
            this.client
                .post(`/api/module/${service}/power_down`, {}, { headers: this.getAuthHeaders() })
                .then(r => r.data)
        )
    }

    async get<T>(path: string): Promise<T> {
        return this.retry(() => this.client.get(path).then(r => r.data))
    }

    async post<T>(path: string, data: any): Promise<T> {
        return this.retry(() =>
            this.client
                .post(path, data, { headers: this.getAuthHeaders() })
                .then(r => r.data)
        )
    }
}

export const apiClient = new VX11ApiClient()

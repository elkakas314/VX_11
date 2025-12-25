import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'
const TIMEOUT = 5000

class VX11ApiClient {
    private client = axios.create({
        baseURL: API_BASE,
        timeout: TIMEOUT,
        headers: { 'Content-Type': 'application/json' }
    })

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

    async getPowerStatus() {
        return this.retry(() =>
            this.client.get('/madre/power/status').then(r => r.data).catch(() => ({ policy_active: 'solo_madre' }))
        )
    }

    async applySoloMadre() {
        return this.retry(() => this.client.post('/madre/power/policy/solo_madre/apply').then(r => r.data))
    }

    async startService(service: string) {
        return this.retry(() => this.client.post('/madre/power/service/start', { service }).then(r => r.data))
    }

    async stopService(service: string) {
        return this.retry(() => this.client.post('/madre/power/service/stop', { service }).then(r => r.data))
    }

    async get<T>(path: string): Promise<T> {
        return this.retry(() => this.client.get(path).then(r => r.data))
    }

    async post<T>(path: string, data: any): Promise<T> {
        return this.retry(() => this.client.post(path, data).then(r => r.data))
    }
}

export const apiClient = new VX11ApiClient()

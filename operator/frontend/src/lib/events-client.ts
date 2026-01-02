/**
 * Intelligent Events Client
 * Handles SSE/EventSource with exponential backoff and policy detection
 * 
 * Usage:
 * const client = new IntelligentEventsClient('/operator/api/events', {
 *   onMessage: (data) => console.log('Event:', data),
 *   onOffByPolicy: (reason) => showBanner(reason),
 *   onMaxRetries: () => showError('Connection lost')
 * });
 */

import { getCurrentToken } from '../services/api'

export interface EventsClientOptions {
    onMessage?: (data: any) => void
    onOpen?: () => void
    onError?: (error: any) => void
    onOffByPolicy?: (data: any) => void
    onMaxRetries?: () => void
    maxRetries?: number
    maxDelayMs?: number
}

export class IntelligentEventsClient {
    private url: string
    private options: EventsClientOptions
    private maxRetries: number
    private maxDelayMs: number
    private retryCount: number = 0
    private shouldStop: boolean = false
    private eventSource: EventSource | null = null
    private backoffMs: number = 1000

    constructor(path: string, options: EventsClientOptions = {}) {
        // Build URL from relative path
        this.url = path.startsWith('/') ? path : `/${path}`
        this.options = options
        this.maxRetries = options.maxRetries ?? 10
        this.maxDelayMs = options.maxDelayMs ?? 30000

        this.connect()
    }

    private connect(): void {
        if (this.shouldStop) return

        console.log(`[EventsClient] Connecting to ${this.url} (attempt ${this.retryCount + 1}/${this.maxRetries})`)

        try {
            // Add auth token to URL params for SSE
            const token = getCurrentToken()
            const separator = this.url.includes('?') ? '&' : '?'
            const urlWithToken = token ? `${this.url}${separator}token=${encodeURIComponent(token)}` : this.url

            this.eventSource = new EventSource(urlWithToken)

            this.eventSource.onopen = () => {
                console.log('[EventsClient] Connection opened')
                this.retryCount = 0
                this.backoffMs = 1000
                this.options.onOpen?.()
            }

            this.eventSource.onmessage = (event) => {
                try {
                    // Parse JSON if possible
                    const data = event.data ? JSON.parse(event.data) : event.data
                    this.options.onMessage?.(data)
                } catch (e) {
                    // Keep as raw string if not JSON
                    this.options.onMessage?.(event.data)
                }
            }

            this.eventSource.onerror = async (event) => {
                console.warn('[EventsClient] EventSource error:', event)
                this.eventSource?.close()

                // Check if this is OFF_BY_POLICY (403 policy denial)
                const policyStop = await this.checkOffByPolicy()
                if (policyStop) {
                    this.shouldStop = true
                    return
                }

                // Retry with exponential backoff + jitter
                if (this.retryCount < this.maxRetries) {
                    const jitter = 0.8 + Math.random() * 0.4 // 0.8x to 1.2x
                    const delay = Math.min(this.backoffMs * jitter, this.maxDelayMs)
                    this.retryCount++
                    this.backoffMs = Math.min(this.backoffMs * 2, this.maxDelayMs)

                    console.log(`[EventsClient] Retrying in ${delay.toFixed(0)}ms...`)
                    setTimeout(() => this.connect(), delay)
                } else {
                    console.error('[EventsClient] Max retries exceeded')
                    this.shouldStop = true
                    this.options.onMaxRetries?.()
                }
            }
        } catch (err) {
            console.error('[EventsClient] Connection error:', err)
            this.options.onError?.(err)

            // Retry
            if (this.retryCount < this.maxRetries) {
                const delay = Math.min(this.backoffMs, this.maxDelayMs)
                this.retryCount++
                this.backoffMs = Math.min(this.backoffMs * 2, this.maxDelayMs)
                setTimeout(() => this.connect(), delay)
            } else {
                this.shouldStop = true
                this.options.onMaxRetries?.()
            }
        }
    }

    private async checkOffByPolicy(): Promise<boolean> {
        try {
            const token = getCurrentToken()
            const headers: Record<string, string> = {}
            if (token) {
                headers['X-VX11-Token'] = token
            }

            const response = await fetch(this.url, { headers, method: 'HEAD' })

            if (response.status === 403) {
                // Try to get JSON body for details
                try {
                    const data = await response.json()
                    if (data.status === 'off_by_policy') {
                        console.warn('[EventsClient] OFF_BY_POLICY detected:', data)
                        this.options.onOffByPolicy?.(data)
                        return true
                    }
                } catch {
                    // HEAD response may not have body; just mark as policy
                    console.warn('[EventsClient] 403 Forbidden (likely policy)')
                    this.options.onOffByPolicy?.({ status: 'off_by_policy', reason: '403 Forbidden' })
                    return true
                }
            }
            return false
        } catch (err) {
            console.error('[EventsClient] Policy check error:', err)
            return false
        }
    }

    public close(): void {
        this.shouldStop = true
        this.eventSource?.close()
        console.log('[EventsClient] Connection closed')
    }

    public isConnected(): boolean {
        return this.eventSource?.readyState === EventSource.OPEN
    }

    public getRetryCount(): number {
        return this.retryCount
    }
}

// Export singleton factory for easy integration
let globalClient: IntelligentEventsClient | null = null

export function getEventsClient(
    path: string = '/operator/api/events',
    options?: EventsClientOptions
): IntelligentEventsClient {
    if (globalClient) {
        globalClient.close()
    }
    globalClient = new IntelligentEventsClient(path, options)
    return globalClient
}

export function closeEventsClient(): void {
    if (globalClient) {
        globalClient.close()
        globalClient = null
    }
}

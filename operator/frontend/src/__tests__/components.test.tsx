import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusCard } from '../components/StatusCard'
import { PowerCard } from '../components/PowerCard'
import { ChatPanel } from '../components/ChatPanel'
import { P0ChecksPanel } from '../components/P0ChecksPanel'

// Mock API client
vi.mock('../services/api', () => ({
    apiClient: {
        status: vi.fn(() =>
            Promise.resolve({
                ok: true,
                data: {
                    status: 'ok',
                    degraded: false,
                    circuit_breaker: {
                        state: 'closed',
                        failure_count: 0,
                    },
                    components: {
                        tentaculo: true,
                        madre: true,
                    },
                },
            })
        ),
        powerState: vi.fn(() =>
            Promise.resolve({
                ok: true,
                data: {
                    status: 'ok',
                    power_window: {
                        policy: 'operative_core',
                        window_id: 'window_123',
                        ttl_remaining: 300,
                        running_services: ['madre', 'tentaculo_link'],
                    },
                },
            })
        ),
        chat: vi.fn(() =>
            Promise.resolve({
                ok: true,
                data: {
                    response: 'Pong',
                },
            })
        ),
        runP0Checks: vi.fn(() =>
            Promise.resolve({
                chat_ask: true,
                status: true,
                power_state: true,
                hormiguero_status: false,
                results: {},
            })
        ),
    },
}))

describe('Operator UI Components', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    describe('StatusCard', () => {
        it('renders status card', async () => {
            render(<StatusCard />)
            const header = screen.getByText('Estado Global')
            expect(header).toBeDefined()
        })

        it('displays loading state', () => {
            render(<StatusCard />)
            // Component initializes and fetches
            expect(screen.getByRole('button', { name: /↻|⟳/i })).toBeDefined()
        })
    })

    describe('PowerCard', () => {
        it('renders power card', () => {
            render(<PowerCard />)
            const header = screen.getByText('Power Window')
            expect(header).toBeDefined()
        })
    })

    describe('ChatPanel', () => {
        it('renders chat panel', () => {
            render(<ChatPanel />)
            const header = screen.getByText(/Chat \(Session:/i)
            expect(header).toBeDefined()
        })

        it('has send button', () => {
            render(<ChatPanel />)
            const button = screen.getByRole('button', { name: /→|Send/i })
            expect(button).toBeDefined()
        })
    })

    describe('P0ChecksPanel', () => {
        it('renders P0 checks panel', () => {
            render(<P0ChecksPanel />)
            const button = screen.getByRole('button', { name: /Run P0 Checks/i })
            expect(button).toBeDefined()
        })
    })
})

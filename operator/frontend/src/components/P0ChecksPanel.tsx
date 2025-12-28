import { useState } from 'react'
import { apiClient } from '../services/api'

interface P0Results {
    chat_ask: boolean
    status: boolean
    power_state: boolean
    hormiguero_status: boolean
    results: Record<string, any>
    timestamp?: Date
}

export function P0ChecksPanel() {
    const [results, setResults] = useState<P0Results | null>(null)
    const [loading, setLoading] = useState(false)

    const handleRunChecks = async () => {
        setLoading(true)
        const p0Results = await apiClient.runP0Checks()
        setResults({
            ...p0Results,
            timestamp: new Date(),
        })
        setLoading(false)
    }

    const allPassed =
        results &&
        results.chat_ask &&
        results.status &&
        results.power_state

    const hormiStatus = results?.hormiguero_status ? 'OK' : 'UNAVAILABLE'

    return (
        <div className="card">
            <div className="card-header">
                <h2>P0 UI Checks</h2>
            </div>

            <button
                onClick={handleRunChecks}
                disabled={loading}
                className="btn-primary"
                style={{ width: '100%', marginBottom: '12px' }}
            >
                {loading ? '⟳ Running...' : '▶ Run P0 Checks'}
            </button>

            {results && (
                <>
                    <div className="checks-grid">
                        <div className="check-result">
                            <span style={{ color: results.chat_ask ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                                {results.chat_ask ? '✓' : '✗'}
                            </span>
                            <span>/operator/chat/ask</span>
                        </div>

                        <div className="check-result">
                            <span style={{ color: results.status ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                                {results.status ? '✓' : '✗'}
                            </span>
                            <span>/operator/status</span>
                        </div>

                        <div className="check-result">
                            <span style={{ color: results.power_state ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                                {results.power_state ? '✓' : '✗'}
                            </span>
                            <span>/operator/power/state</span>
                        </div>

                        <div className="check-result">
                            <span
                                style={{ color: results.hormiguero_status ? 'var(--accent-blue)' : 'var(--text-secondary)' }}
                            >
                                {results.hormiguero_status ? '✓' : '◐'}
                            </span>
                            <span>/hormiguero/status (optional)</span>
                        </div>
                    </div>

                    <div
                        className={allPassed ? 'success-box' : 'warning-box'}
                        style={{ marginTop: '12px' }}
                    >
                        {allPassed ? (
                            <>
                                <span>✓</span> All required endpoints reachable
                            </>
                        ) : (
                            <>
                                <span>⚠</span> Some endpoints failed - check connection
                            </>
                        )}
                    </div>

                    {results.timestamp && (
                        <div className="card-footer">
                            <small>Checked: {results.timestamp.toLocaleTimeString()}</small>
                        </div>
                    )}

                    <details style={{ marginTop: '12px' }}>
                        <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)' }}>
                            Raw Results
                        </summary>
                        <pre style={{ marginTop: '8px', fontSize: '0.75em', overflow: 'auto' }}>
                            {JSON.stringify(results.results, null, 2)}
                        </pre>
                    </details>
                </>
            )}
        </div>
    )
}

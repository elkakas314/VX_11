import { useState } from 'react'
import { apiClient } from '../services/api'

interface P0Results {
    chat_ask: boolean
    status: boolean
    windows: boolean
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
        results.windows

    return (
        <div className="card">
            <div className="card-header">
                <h2>P0 UI Checks</h2>
            </div>

            <button
                onClick={handleRunChecks}
                disabled={loading}
                className="btn-primary btn-full-width"
            >
                {loading ? '⟳ Running...' : '▶ Run P0 Checks'}
            </button>

            {results && (
                <>
                    <div className="checks-grid">
                        <div className="check-result">
                            <span className={results.chat_ask ? 'check-pass' : 'check-fail'}>
                                {results.chat_ask ? '✓' : '✗'}
                            </span>
                            <span>/operator/api/chat</span>
                        </div>

                        <div className="check-result">
                            <span className={results.status ? 'check-pass' : 'check-fail'}>
                                {results.status ? '✓' : '✗'}
                            </span>
                            <span>/operator/api/status</span>
                        </div>

                        <div className="check-result">
                            <span className={results.windows ? 'check-pass' : 'check-fail'}>
                                {results.windows ? '✓' : '✗'}
                            </span>
                            <span>/operator/api/window/status</span>
                        </div>

                        <div className="check-result">
                            <span className={results.hormiguero_status ? 'check-optional-pass' : 'check-optional-fail'}>
                                {results.hormiguero_status ? '✓' : '◐'}
                            </span>
                            <span>/operator/api/hormiguero/status (optional)</span>
                        </div>
                    </div>

                    <div
                        className={allPassed ? 'success-box result-margin' : 'warning-box result-margin'}
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

                    <details className="details-margin">
                        <summary className="details-summary">
                            Raw Results
                        </summary>
                        <pre className="details-pre">
                            {JSON.stringify(results.results, null, 2)}
                        </pre>
                    </details>
                </>
            )}
        </div>
    )
}

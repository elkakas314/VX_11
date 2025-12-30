import { useState } from 'react'
import { apiClient } from '../services/api'

interface CoDevRequest {
    purpose: 'plan' | 'patch' | 'review' | 'risk_assessment'
    prompt: string
}

interface CoDevResponse {
    status: 'ok' | 'error'
    request_id?: string
    reasoning_content?: string
    response?: string
    tokens_used?: number
    reasoning_tokens?: number
    error_msg?: string
    elapsed_ms?: number
}

export function CoDevView() {
    const [purpose, setPurpose] = useState<CoDevRequest['purpose']>('plan')
    const [prompt, setPrompt] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [response, setResponse] = useState<CoDevResponse | null>(null)
    const [expanded, setExpanded] = useState(false)

    async function handleExecute() {
        if (!prompt.trim()) {
            setError('Please enter a prompt')
            return
        }

        setLoading(true)
        setError(null)
        setResponse(null)

        try {
            const resp = await apiClient.request('POST', '/operator/api/assist/deepseek_r1', {
                purpose,
                prompt,
                temperature: 1.0,
                max_tokens: 2000,
            })

            if (resp.ok && resp.data) {
                setResponse(resp.data as CoDevResponse)
            } else {
                throw new Error(resp.error || 'Co-Dev request failed')
            }
        } catch (err: any) {
            setError(err.message || 'Failed to execute co-dev request')
        } finally {
            setLoading(false)
        }
    }

    const purposeLabels = {
        plan: '📋 Plan (architecture + steps)',
        patch: '🔧 Patch (code fix)',
        review: '👀 Review (quality feedback)',
        risk_assessment: '⚠️ Risk (security analysis)',
    }

    return (
        <div className="codev-view">
            <div className="codev-header">
                <h3>
                    <span className="codev-icon">🧠</span>
                    Co-Dev (R1)
                </h3>
                <button
                    className="btn-sm btn-collapse"
                    onClick={() => setExpanded(!expanded)}
                    title={expanded ? 'Collapse' : 'Expand'}
                >
                    {expanded ? '▼' : '▶'}
                </button>
            </div>

            {expanded && (
                <div className="codev-content">
                    <div className="codev-warning">
                        ⚠️ Uses DeepSeek R1 API credits · Rate limit: 10/hour
                    </div>

                    <div className="codev-controls">
                        <div className="control-group">
                            <label htmlFor="purpose-select">Purpose:</label>
                            <select
                                id="purpose-select"
                                value={purpose}
                                onChange={(e) =>
                                    setPurpose(e.target.value as CoDevRequest['purpose'])
                                }
                                disabled={loading}
                                className="codev-select"
                            >
                                <option value="plan">Plan</option>
                                <option value="patch">Patch</option>
                                <option value="review">Review</option>
                                <option value="risk_assessment">Risk Assessment</option>
                            </select>
                            <span className="purpose-desc">{purposeLabels[purpose]}</span>
                        </div>

                        <div className="control-group full-width">
                            <label htmlFor="prompt-input">Prompt:</label>
                            <textarea
                                id="prompt-input"
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                disabled={loading}
                                placeholder={`Describe what you need (${purpose})`}
                                className="codev-textarea"
                                rows={4}
                            />
                            <span className="char-count">
                                {prompt.length} / 4000 chars
                            </span>
                        </div>

                        <div className="codev-actions">
                            <button
                                onClick={handleExecute}
                                disabled={loading || prompt.length === 0}
                                className="btn-primary btn-full"
                                title="Execute R1 request (may take 30s+)"
                            >
                                {loading ? '⟳ Executing...' : '▶ Execute R1'}
                            </button>
                        </div>
                    </div>

                    {error && <div className="error-banner">{error}</div>}

                    {response && (
                        <div className="codev-result">
                            <div className="result-header">
                                <span className="result-status">
                                    {response.status === 'ok' ? '✓ Success' : '✗ Error'}
                                </span>
                                <span className="result-meta">
                                    {response.tokens_used && (
                                        <>
                                            {response.tokens_used} tokens
                                            {response.reasoning_tokens && (
                                                <>
                                                    {' '}
                                                    ({response.reasoning_tokens} reasoning)
                                                </>
                                            )}
                                        </>
                                    )}
                                    {response.elapsed_ms && (
                                        <> · {response.elapsed_ms}ms</>
                                    )}
                                </span>
                            </div>

                            {response.status === 'ok' && (
                                <>
                                    {response.reasoning_content && (
                                        <div className="result-section">
                                            <h4>Reasoning</h4>
                                            <div className="result-content reasoning">
                                                {response.reasoning_content}
                                            </div>
                                        </div>
                                    )}

                                    {response.response && (
                                        <div className="result-section">
                                            <h4>Response</h4>
                                            <div className="result-content">
                                                {response.response}
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}

                            {response.status === 'error' && (
                                <div className="error-banner">
                                    {response.error_msg || 'Unknown error'}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

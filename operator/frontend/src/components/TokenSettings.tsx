import { useState, useEffect } from 'react'
import { getCurrentToken, setTokenLocally } from '../services/api'

/**
 * TokenSettings Component
 * 
 * Allows user to configure VX11_TOKEN at runtime (not build-time).
 * Token is stored in localStorage and used for all API requests.
 * 
 * Invariant: Token is NEVER hardcoded in bundle.
 */
export function TokenSettings() {
    const [token, setToken] = useState('')
    const [isEditing, setIsEditing] = useState(false)
    const [savedMessage, setSavedMessage] = useState('')

    useEffect(() => {
        // Load current token on mount
        const current = getCurrentToken()
        setToken(current)
    }, [])

    const handleSave = () => {
        if (!token.trim()) {
            setSavedMessage('Token cannot be empty')
            return
        }
        setTokenLocally(token)
        setSavedMessage('Token saved successfully')
        setIsEditing(false)
        setTimeout(() => setSavedMessage(''), 3000)
    }

    const handleClear = () => {
        setToken('')
        setTokenLocally('')
        setSavedMessage('Token cleared')
        setTimeout(() => setSavedMessage(''), 2000)
    }

    return (
        <div className="token-settings">
            <h3>🔐 Token Configuration</h3>
            <p className="text-xs text-gray-500">
                Configure X-VX11-Token for API authentication.
                Token is stored locally in browser (not in code).
            </p>

            {!isEditing ? (
                <div className="token-display">
                    <div className="token-value">
                        {token ? (
                            <>
                                <code>{token.substring(0, 10)}...{token.substring(token.length - 5)}</code>
                                <span className="text-xs text-green-400 ml-2">✓ Configured</span>
                            </>
                        ) : (
                            <span className="text-xs text-yellow-400">⚠️ Not configured</span>
                        )}
                    </div>
                    <button
                        onClick={() => setIsEditing(true)}
                        className="btn-secondary btn-sm"
                        title="Edit token"
                    >
                        Edit
                    </button>
                </div>
            ) : (
                <div className="token-edit">
                    <input
                        type="password"
                        placeholder="Enter X-VX11-Token (e.g., vx11-test-token)"
                        value={token}
                        onChange={(e) => setToken(e.target.value)}
                        className="input-field"
                    />
                    <div className="token-actions">
                        <button onClick={handleSave} className="btn-primary btn-sm">
                            Save
                        </button>
                        <button onClick={() => setIsEditing(false)} className="btn-secondary btn-sm">
                            Cancel
                        </button>
                        <button onClick={handleClear} className="btn-danger btn-sm">
                            Clear
                        </button>
                    </div>
                </div>
            )}

            {savedMessage && (
                <div className="message-banner text-sm">
                    {savedMessage}
                </div>
            )}

            <style>{`
                .token-settings {
                    padding: 1rem;
                    background: rgba(30, 30, 50, 0.5);
                    border-radius: 8px;
                    border: 1px solid rgba(100, 100, 150, 0.3);
                }
                .token-settings h3 {
                    margin: 0 0 0.5rem 0;
                    font-size: 0.9rem;
                    color: #aaa;
                }
                .token-settings p {
                    margin: 0 0 1rem 0;
                }
                .token-display {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    margin-bottom: 0.5rem;
                }
                .token-value {
                    flex: 1;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.5rem;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 0.85rem;
                }
                .token-value code {
                    color: #0f0;
                }
                .token-edit {
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                }
                .input-field {
                    padding: 0.5rem;
                    background: rgba(0, 0, 0, 0.5);
                    border: 1px solid rgba(100, 100, 150, 0.5);
                    color: #fff;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 0.85rem;
                }
                .token-actions {
                    display: flex;
                    gap: 0.5rem;
                }
                .btn-sm {
                    padding: 0.4rem 0.8rem;
                    font-size: 0.75rem;
                }
                .message-banner {
                    margin-top: 0.5rem;
                    padding: 0.4rem;
                    background: rgba(0, 150, 0, 0.2);
                    border-left: 2px solid #0f0;
                    color: #0f0;
                }
            `}</style>
        </div>
    )
}

import { useState } from 'react'
import { getCurrentToken, setTokenLocally } from '../services/api'

/**
 * TokenRequiredBanner
 * Shows when no token is configured, with inline token input CTA
 */
export function TokenRequiredBanner() {
    const [token, setToken] = useState('')
    const [showInput, setShowInput] = useState(false)
    const [saved, setSaved] = useState(false)

    const handleSave = () => {
        if (token.trim()) {
            setTokenLocally(token)
            setSaved(true)
            setTimeout(() => {
                setSaved(false)
                setShowInput(false)
                setToken('')
                // Trigger reload of App (parent should detect token change)
                window.location.reload()
            }, 1500)
        }
    }

    return (
        <div className="token-required-banner">
            <div className="token-banner-content">
                <strong>🔐 Token Required</strong>
                <p className="token-banner-description">
                    Configure X-VX11-Token to enable API access
                </p>
            </div>

            {!showInput ? (
                <button
                    onClick={() => setShowInput(true)}
                    className="token-banner-button token-banner-button-primary"
                >
                    Set Token
                </button>
            ) : (
                <div className="token-banner-input-group">
                    <input
                        type="password"
                        placeholder="Enter token"
                        value={token}
                        onChange={(e) => setToken(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                        className="token-banner-input"
                        autoFocus
                    />
                    <button
                        onClick={handleSave}
                        disabled={!token.trim()}
                        className="token-banner-button token-banner-button-save"
                    >
                        {saved ? '✓' : 'Save'}
                    </button>
                </div>
            )}
        </div>
    )
}

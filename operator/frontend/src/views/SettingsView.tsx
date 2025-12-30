import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface SettingsData {
    appearance?: {
        theme: string
        language: string
    }
    chat?: {
        model: string
        temperature: number
    }
    security?: {
        enable_api_logs: boolean
        enable_debug_mode: boolean
    }
    notifications?: {
        enable_events: boolean
        events_level: string
    }
}

export function SettingsView() {
    const [settings, setSettings] = useState<SettingsData>({
        appearance: { theme: 'dark', language: 'en' },
        chat: { model: 'deepseek-r1', temperature: 0.7 },
        security: { enable_api_logs: false, enable_debug_mode: false },
        notifications: { enable_events: true, events_level: 'info' },
    })
    const [loading, setLoading] = useState(true)
    const [saved, setSaved] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [readOnly, setReadOnly] = useState(true)
    const [policy, setPolicy] = useState<string>('solo_madre')

    useEffect(() => {
        loadSettings()
    }, [])

    async function loadSettings() {
        setLoading(true)
        setError(null)

        try {
            if (apiClient.settings) {
                const resp = await apiClient.settings()
                if (resp.ok && resp.data) {
                    const data = resp.data
                    if (data.settings) {
                        setSettings(data.settings)
                    } else {
                        setSettings(data)
                    }
                    setReadOnly(Boolean(data.read_only))
                    setPolicy(data.policy || 'solo_madre')
                } else if (resp.error) {
                    setError(resp.error)
                }
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load settings')
        } finally {
            setLoading(false)
        }
    }

    async function handleSave() {
        setError(null)

        try {
            if (apiClient.updateSettings) {
                const resp = await apiClient.updateSettings(settings)
                if (resp.ok) {
                    setSaved(true)
                    setTimeout(() => setSaved(false), 2000)
                } else if (resp.data?.status === 'OFF_BY_POLICY') {
                    setReadOnly(true)
                    setPolicy(resp.data?.recommended_action || 'solo_madre')
                } else {
                    throw new Error(resp.error || 'Save failed')
                }
            }
        } catch (err: any) {
            setError(err.message || 'Failed to save settings')
        }
    }

    const handleChange = (section: keyof SettingsData, key: string, value: any) => {
        setSettings((prev) => ({
            ...prev,
            [section]: {
                ...prev[section],
                [key]: value,
            },
        }))
    }

    if (loading) {
        return <div className="view-loading">⟳ Loading settings...</div>
    }

    return (
        <div className="settings-view">
            <h2>Settings</h2>

            {error && <div className="error-banner">{error}</div>}
            {readOnly && (
                <div className="info-banner">
                    Read-only in <strong>{policy}</strong> mode. Ask Madre to open an operator window.
                </div>
            )}
            {saved && <div className="success-banner">✓ Settings saved</div>}

            <div className="settings-panel">
                {/* Appearance */}
                <div className="settings-section">
                    <h3>Appearance</h3>
                    <label className="setting-item">
                        <span className="label-text">Theme</span>
                        <select
                            value={settings.appearance?.theme || 'dark'}
                            onChange={(e) => handleChange('appearance', 'theme', e.target.value)}
                            disabled={readOnly}
                        >
                            <option value="dark">Dark</option>
                            <option value="light">Light</option>
                            <option value="auto">Auto</option>
                        </select>
                    </label>

                    <label className="setting-item">
                        <span className="label-text">Language</span>
                        <select
                            value={settings.appearance?.language || 'en'}
                            onChange={(e) => handleChange('appearance', 'language', e.target.value)}
                            disabled={readOnly}
                        >
                            <option value="en">English</option>
                            <option value="es">Español</option>
                        </select>
                    </label>
                </div>

                {/* Chat Settings */}
                <div className="settings-section">
                    <h3>Chat</h3>
                    <label className="setting-item">
                        <span className="label-text">Model</span>
                        <select
                            value={settings.chat?.model || 'deepseek-r1'}
                            onChange={(e) => handleChange('chat', 'model', e.target.value)}
                            disabled={readOnly}
                        >
                            <option value="deepseek-r1">DeepSeek R1</option>
                            <option value="openai-gpt4">OpenAI GPT-4</option>
                            <option value="local">Local</option>
                        </select>
                    </label>

                    <label className="setting-item">
                        <span className="label-text">Temperature</span>
                        <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.1"
                            value={settings.chat?.temperature || 0.7}
                            onChange={(e) =>
                                handleChange('chat', 'temperature', parseFloat(e.target.value))
                            }
                            disabled={readOnly}
                        />
                    </label>
                </div>

                {/* Security */}
                <div className="settings-section">
                    <h3>Security</h3>
                    <label className="setting-item checkbox">
                        <input
                            type="checkbox"
                            checked={settings.security?.enable_api_logs || false}
                            onChange={(e) =>
                                handleChange('security', 'enable_api_logs', e.target.checked)
                            }
                            disabled={readOnly}
                        />
                        <span className="label-text">Enable API Logs</span>
                    </label>

                    <label className="setting-item checkbox">
                        <input
                            type="checkbox"
                            checked={settings.security?.enable_debug_mode || false}
                            onChange={(e) =>
                                handleChange('security', 'enable_debug_mode', e.target.checked)
                            }
                            disabled={readOnly}
                        />
                        <span className="label-text">Enable Debug Mode</span>
                    </label>
                </div>

                {/* Notifications */}
                <div className="settings-section">
                    <h3>Notifications</h3>
                    <label className="setting-item checkbox">
                        <input
                            type="checkbox"
                            checked={settings.notifications?.enable_events || false}
                            onChange={(e) =>
                                handleChange('notifications', 'enable_events', e.target.checked)
                            }
                            disabled={readOnly}
                        />
                        <span className="label-text">Enable Event Notifications</span>
                    </label>

                    <label className="setting-item">
                        <span className="label-text">Event Level</span>
                        <select
                            value={settings.notifications?.events_level || 'info'}
                            onChange={(e) =>
                                handleChange('notifications', 'events_level', e.target.value)
                            }
                            disabled={readOnly}
                        >
                            <option value="debug">Debug</option>
                            <option value="info">Info</option>
                            <option value="warning">Warning</option>
                            <option value="error">Error</option>
                        </select>
                    </label>
                </div>
            </div>

            <div className="settings-actions">
                <button onClick={handleSave} className="btn-primary" disabled={readOnly}>
                    💾 Save Settings
                </button>
            </div>
        </div>
    )
}

import React, { useState, useEffect } from "react";

interface OperatorSettings {
    theme: "dark" | "light";
    poll_interval: number;
    redaction_level: "low" | "medium" | "high";
    default_tab: string;
    telemetry_enabled: boolean;
    [key: string]: any;
}

export function SettingsTab() {
    const [settings, setSettings] = useState<OperatorSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [unsavedChanges, setUnsavedChanges] = useState(false);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setError(null);
            const res = await fetch("http://localhost:8000/api/settings");
            if (res.ok) {
                const data = await res.json();
                setSettings(data.data || data);
            } else {
                throw new Error(`HTTP ${res.status}`);
            }
            setLoading(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load settings");
            setLoading(false);
        }
    };

    const handleSettingChange = (key: keyof OperatorSettings, value: any) => {
        if (settings) {
            setSettings({ ...settings, [key]: value });
            setUnsavedChanges(true);
        }
    };

    const saveSettings = async () => {
        try {
            setError(null);
            const res = await fetch("http://localhost:8000/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings),
            });

            if (res.ok) {
                const data = await res.json();
                if (data.ok) {
                    setUnsavedChanges(false);
                    alert("Settings saved successfully");
                } else {
                    throw new Error(data.detail || "Failed to save");
                }
            } else {
                throw new Error(`HTTP ${res.status}`);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save settings");
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-slate-400">Loading settings...</div>
            </div>
        );
    }

    if (error && !settings) {
        return (
            <div className="bg-red-900/30 border border-red-700 rounded p-4 m-4">
                <div className="text-red-200">Error: {error}</div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6 max-w-2xl">
            {/* Header */}
            <div>
                <h2 className="text-3xl font-bold mb-2">Operator Settings</h2>
                <p className="text-slate-400">Configure UI behavior and preferences</p>
            </div>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded p-4">
                    <div className="text-red-200 text-sm">{error}</div>
                </div>
            )}

            {settings && (
                <div className="space-y-6">
                    {/* Theme Setting */}
                    <div className="bg-slate-800 rounded border border-slate-700 p-4">
                        <label className="block text-sm font-bold text-slate-300 mb-2">Theme</label>
                        <div className="flex gap-3">
                            {["dark", "light"].map((theme) => (
                                <button
                                    key={theme}
                                    onClick={() => handleSettingChange("theme", theme as "dark" | "light")}
                                    className={`px-4 py-2 rounded border transition-all capitalize ${settings.theme === theme
                                            ? "bg-blue-900 border-blue-600 text-blue-100"
                                            : "bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600"
                                        }`}
                                >
                                    {theme}
                                </button>
                            ))}
                        </div>
                        <p className="text-xs text-slate-500 mt-2">Recommended: Dark (for 24/7 monitoring)</p>
                    </div>

                    {/* Poll Interval Setting */}
                    <div className="bg-slate-800 rounded border border-slate-700 p-4">
                        <label htmlFor="poll_interval" className="block text-sm font-bold text-slate-300 mb-2">
                            Poll Interval (seconds): {settings.poll_interval}
                        </label>
                        <input
                            id="poll_interval"
                            type="range"
                            min="1"
                            max="60"
                            value={settings.poll_interval}
                            onChange={(e) => handleSettingChange("poll_interval", parseInt(e.target.value))}
                            className="w-full"
                            title="Poll interval in seconds"
                            placeholder="Poll interval in seconds"
                            aria-label="Poll interval in seconds"
                        />
                        <p className="text-xs text-slate-500 mt-2">
                            How often to refresh metrics (1-60 seconds). Lower = more frequent, higher = less network load.
                        </p>
                    </div>

                    {/* Redaction Level Setting */}
                    <div className="bg-slate-800 rounded border border-slate-700 p-4">
                        <label className="block text-sm font-bold text-slate-300 mb-2">Redaction Level</label>
                        <div className="flex gap-3 flex-wrap">
                            {["low", "medium", "high"].map((level) => (
                                <button
                                    key={level}
                                    onClick={() => handleSettingChange("redaction_level", level as "low" | "medium" | "high")}
                                    className={`px-4 py-2 rounded border transition-all capitalize ${settings.redaction_level === level
                                            ? "bg-blue-900 border-blue-600 text-blue-100"
                                            : "bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600"
                                        }`}
                                >
                                    {level}
                                </button>
                            ))}
                        </div>
                        <p className="text-xs text-slate-500 mt-2">
                            Low: show all data | Medium: redact sensitive values | High: minimal disclosure
                        </p>
                    </div>

                    {/* Default Tab Setting */}
                    <div className="bg-slate-800 rounded border border-slate-700 p-4">
                        <label className="block text-sm font-bold text-slate-300 mb-2">Default Tab on Login</label>
                        <select
                            value={settings.default_tab}
                            onChange={(e) => handleSettingChange("default_tab", e.target.value)}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                            title="Default tab on login"
                            aria-label="Default tab on login"
                        >
                            <option value="overview">Overview</option>
                            <option value="topology">Topology</option>
                            <option value="metrics">Metrics</option>
                            <option value="audit">Audit</option>
                            <option value="settings">Settings</option>
                        </select>
                        <p className="text-xs text-slate-500 mt-2">Which tab should appear first?</p>
                    </div>

                    {/* Telemetry Setting */}
                    <div className="bg-slate-800 rounded border border-slate-700 p-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={settings.telemetry_enabled}
                                onChange={(e) => handleSettingChange("telemetry_enabled", e.target.checked)}
                                className="w-4 h-4 rounded bg-slate-900 border-slate-600"
                            />
                            <span className="text-sm font-bold text-slate-300">Enable Telemetry</span>
                        </label>
                        <p className="text-xs text-slate-500 mt-2">
                            Send anonymous usage data to improve operator experience (e.g., tab preferences, error rates)
                        </p>
                    </div>

                    {/* Info Section */}
                    <div className="bg-blue-900/20 border border-blue-700 rounded p-4">
                        <h3 className="text-sm font-bold text-blue-200 mb-2">ℹ️ About Operator Settings</h3>
                        <ul className="text-xs text-blue-200 space-y-1 list-disc list-inside">
                            <li>Settings are stored locally in this session (ephemeral)</li>
                            <li>To persist settings, use environment variables or config files</li>
                            <li>Theme changes apply immediately</li>
                            <li>Poll interval affects all data refresh rates</li>
                        </ul>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-4 border-t border-slate-700">
                        <button
                            onClick={saveSettings}
                            disabled={!unsavedChanges}
                            className={`px-4 py-2 rounded border font-mono text-sm transition-all ${unsavedChanges
                                    ? "bg-green-900 border-green-700 text-green-200 hover:bg-green-800"
                                    : "bg-slate-700 border-slate-600 text-slate-500 cursor-not-allowed"
                                }`}
                        >
                            💾 Save Settings
                        </button>
                        <button
                            onClick={loadSettings}
                            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded border border-slate-600 text-slate-300 font-mono text-sm"
                        >
                            ↻ Reload
                        </button>
                    </div>

                    {unsavedChanges && (
                        <div className="bg-yellow-900/20 border border-yellow-700 rounded p-3 text-yellow-200 text-sm">
                            ⚠️ You have unsaved changes. Click "Save Settings" to persist them for this session.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

import React, { useState } from 'react';
import './ControlPanel.css';

interface ControlPanelProps {
    selectedModule?: string;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({ selectedModule }) => {
    const [activeTab, setActiveTab] = useState<'audit' | 'modules' | 'explorer' | 'settings'>('audit');
    const [settings, setSettings] = useState({ theme: 'dark', auto_refresh_interval: 5000 });

    const handlePowerAction = async (action: 'power_up' | 'power_down' | 'restart') => {
        if (!selectedModule) return;
        try {
            const res = await fetch(`/api/module/${selectedModule}/${action}`, { method: 'POST', body: '{}' });
            const data = await res.json();
            console.log(`Module ${selectedModule} ${action}:`, data);
        } catch (err) {
            console.error('Error:', err);
        }
    };

    const handleSettingsSave = async () => {
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings),
            });
            const data = await res.json();
            console.log('Settings saved:', data);
        } catch (err) {
            console.error('Error:', err);
        }
    };

    return (
        <div className="cp-container">
            <div className="cp-tabs">
                {['audit', 'modules', 'explorer', 'settings'].map((tab) => (
                    <button
                        key={tab}
                        className={`cp-tab ${activeTab === tab ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab as typeof activeTab)}
                    >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                ))}
            </div>

            <div className="cp-content">
                {activeTab === 'audit' && (
                    <div>
                        <h3>Audit Jobs</h3>
                        <button
                            className="cp-button"
                            onClick={() => {
                                fetch('/api/audit', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ audit_type: 'structure', scope: 'full' }),
                                });
                            }}
                        >
                            Start Audit
                        </button>
                    </div>
                )}

                {activeTab === 'modules' && (
                    <div>
                        <h3>Module Control</h3>
                        {selectedModule ? (
                            <>
                                <p>Selected: {selectedModule}</p>
                                <button className="cp-button" onClick={() => handlePowerAction('power_up')}>
                                    Power Up
                                </button>
                                <button className="cp-button" onClick={() => handlePowerAction('power_down')}>
                                    Power Down
                                </button>
                                <button className="cp-button" onClick={() => handlePowerAction('restart')}>
                                    Restart
                                </button>
                            </>
                        ) : (
                            <p>Select a module from the dashboard</p>
                        )}
                    </div>
                )}

                {activeTab === 'explorer' && (
                    <div>
                        <h3>Database Explorer</h3>
                        <p>Browse and query the VX11 database</p>
                        <a
                            href="/api/explorer/db?table=modules&limit=100"
                            target="_blank"
                            rel="noreferrer"
                            className="cp-link"
                        >
                            View Modules Table
                        </a>
                    </div>
                )}

                {activeTab === 'settings' && (
                    <div>
                        <h3>User Settings</h3>
                        <label className="cp-label">
                            Theme:
                            <select
                                value={settings.theme}
                                onChange={(e) => setSettings({ ...settings, theme: e.target.value as 'dark' | 'light' })}
                                className="cp-input"
                            >
                                <option value="dark">Dark</option>
                                <option value="light">Light</option>
                            </select>
                        </label>
                        <label className="cp-label">
                            Auto-refresh interval (ms):
                            <input
                                type="number"
                                min="1000"
                                value={settings.auto_refresh_interval}
                                onChange={(e) => setSettings({ ...settings, auto_refresh_interval: parseInt(e.target.value) })}
                                className="cp-input"
                            />
                        </label>
                        <button className="cp-button" onClick={handleSettingsSave}>
                            Save Settings
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

import React, { useState } from 'react';

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
        <div style={styles.container}>
            <div style={styles.tabs}>
                {['audit', 'modules', 'explorer', 'settings'].map((tab) => (
                    <button
                        key={tab}
                        style={{
                            ...styles.tab,
                            backgroundColor: activeTab === tab ? '#4ade80' : '#333',
                            color: activeTab === tab ? '#000' : '#e0e0e0',
                        }}
                        onClick={() => setActiveTab(tab as typeof activeTab)}
                    >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                ))}
            </div>

            <div style={styles.content}>
                {activeTab === 'audit' && (
                    <div>
                        <h3>Audit Jobs</h3>
                        <button
                            style={styles.button}
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
                                <button style={styles.button} onClick={() => handlePowerAction('power_up')}>
                                    Power Up
                                </button>
                                <button style={styles.button} onClick={() => handlePowerAction('power_down')}>
                                    Power Down
                                </button>
                                <button style={styles.button} onClick={() => handlePowerAction('restart')}>
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
                            style={styles.link}
                        >
                            View Modules Table
                        </a>
                    </div>
                )}

                {activeTab === 'settings' && (
                    <div>
                        <h3>User Settings</h3>
                        <label style={styles.label}>
                            Theme:
                            <select
                                value={settings.theme}
                                onChange={(e) => setSettings({ ...settings, theme: e.target.value as 'dark' | 'light' })}
                                style={styles.input}
                            >
                                <option value="dark">Dark</option>
                                <option value="light">Light</option>
                            </select>
                        </label>
                        <label style={styles.label}>
                            Auto-refresh interval (ms):
                            <input
                                type="number"
                                min="1000"
                                value={settings.auto_refresh_interval}
                                onChange={(e) => setSettings({ ...settings, auto_refresh_interval: parseInt(e.target.value) })}
                                style={styles.input}
                            />
                        </label>
                        <button style={styles.button} onClick={handleSettingsSave}>
                            Save Settings
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

const styles = {
    container: {
        padding: '16px',
        backgroundColor: '#1a1a1a',
        color: '#e0e0e0',
        height: '100%',
        display: 'flex',
        flexDirection: 'column' as const,
        overflowY: 'auto' as const,
    },
    tabs: {
        display: 'flex',
        gap: '8px',
        marginBottom: '16px',
        borderBottom: '1px solid #333',
        paddingBottom: '8px',
    },
    tab: {
        padding: '8px 12px',
        borderRadius: '4px',
        border: 'none',
        cursor: 'pointer',
        fontSize: '12px',
        fontWeight: 'bold',
    },
    content: {
        flex: 1,
        overflowY: 'auto' as const,
    },
    button: {
        display: 'block',
        padding: '8px 12px',
        marginTop: '8px',
        backgroundColor: '#4ade80',
        color: '#000',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        fontWeight: 'bold',
        fontSize: '12px',
    },
    label: {
        display: 'block',
        marginBottom: '12px',
    },
    input: {
        display: 'block',
        width: '100%',
        padding: '8px',
        marginTop: '4px',
        backgroundColor: '#2a2a2a',
        color: '#e0e0e0',
        border: '1px solid #444',
        borderRadius: '4px',
    },
    link: {
        color: '#4ade80',
        textDecoration: 'none',
        display: 'block',
        marginTop: '8px',
    },
};

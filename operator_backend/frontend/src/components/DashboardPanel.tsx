import React, { useState, useEffect } from 'react';

interface Module {
    name: string;
    status: 'up' | 'down' | 'degraded';
    healthy: boolean;
    last_check: string;
}

interface DashboardPanelProps {
    onModuleSelect?: (moduleName: string) => void;
}

export const DashboardPanel: React.FC<DashboardPanelProps> = ({ onModuleSelect }) => {
    const [modules, setModules] = useState<Module[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchModules = async () => {
            try {
                const res = await fetch('/api/status/modules');
                const data = await res.json();
                if (data.ok) {
                    setModules(data.data.modules);
                }
            } catch (err) {
                console.error('Error fetching modules:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchModules();
        const interval = setInterval(fetchModules, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'up':
                return '#4ade80'; // green
            case 'down':
                return '#f87171'; // red
            case 'degraded':
                return '#facc15'; // yellow
            default:
                return '#d1d5db'; // gray
        }
    };

    return (
        <div style={styles.container}>
            <h2 style={styles.title}>Module Status</h2>
            {loading ? (
                <p style={styles.text}>Loading...</p>
            ) : (
                <div style={styles.grid}>
                    {modules.map((module) => (
                        <div
                            key={module.name}
                            style={{
                                ...styles.card,
                                borderLeftColor: getStatusColor(module.status),
                                cursor: 'pointer',
                            }}
                            onClick={() => onModuleSelect?.(module.name)}
                        >
                            <div style={styles.cardHeader}>
                                <h3 style={styles.moduleName}>{module.name}</h3>
                                <div
                                    style={{
                                        ...styles.statusBadge,
                                        backgroundColor: getStatusColor(module.status),
                                    }}
                                >
                                    {module.status}
                                </div>
                            </div>
                            <p style={styles.healthText}>Health: {module.healthy ? '✅' : '❌'}</p>
                            <p style={styles.timeText}>{new Date(module.last_check).toLocaleTimeString()}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const styles = {
    container: {
        padding: '16px',
        backgroundColor: '#1a1a1a',
        color: '#e0e0e0',
        height: '100%',
        overflowY: 'auto' as const,
    },
    title: {
        fontSize: '16px',
        fontWeight: 'bold',
        marginBottom: '12px',
        color: '#ffffff',
    },
    grid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '12px',
    },
    card: {
        backgroundColor: '#2a2a2a',
        borderRadius: '8px',
        borderLeft: '4px solid',
        padding: '12px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
    },
    cardHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '8px',
    },
    moduleName: {
        fontSize: '14px',
        fontWeight: 'bold',
        margin: 0,
    },
    statusBadge: {
        fontSize: '10px',
        padding: '2px 6px',
        borderRadius: '4px',
        color: '#000',
        fontWeight: 'bold',
    },
    text: {
        color: '#aaa',
    },
    healthText: {
        fontSize: '12px',
        margin: '4px 0',
    },
    timeText: {
        fontSize: '10px',
        color: '#888',
        margin: '4px 0 0 0',
    },
};

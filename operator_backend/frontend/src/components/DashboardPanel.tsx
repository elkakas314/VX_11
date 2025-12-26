import React, { useState, useEffect } from 'react';
import './DashboardPanel.css';

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

    return (
        <div className="dashboard-container">
            <h2 className="dashboard-title">Module Status</h2>
            {loading ? (
                <p className="text">Loading...</p>
            ) : (
                <div className="grid">
                    {modules.map((module) => (
                        <div
                            key={module.name}
                            className={`card ${module.status}`}
                            onClick={() => onModuleSelect?.(module.name)}
                        >
                            <div className="card-header">
                                <h3 className="module-name">{module.name}</h3>
                                <div className={`status-badge ${module.status}`}>
                                    {module.status}
                                </div>
                            </div>
                            <p className="health-text">Health: {module.healthy ? '✅' : '❌'}</p>
                            <p className="time-text">{new Date(module.last_check).toLocaleTimeString()}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

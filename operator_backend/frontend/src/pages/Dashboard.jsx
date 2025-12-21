import React, { useEffect, useState } from 'react';
import { operatorApi } from '../api/operatorClient';
import './Dashboard.css';

export const Dashboard = () => {
    const [overview, setOverview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchOverview = async () => {
            try {
                setLoading(true);
                const res = await operatorApi.getVx11Overview();
                setOverview(res.data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchOverview();
    }, []);

    if (loading) return <div className="loading">Loading...</div>;
    if (error) return <div className="error">Error: {error}</div>;
    if (overview?.status === 'service_offline') {
        return <div className="error">Backend offline</div>;
    }

    return (
        <div className="dashboard">
            <h2>VX11 System Overview</h2>
            <div className="overview-summary">
                <p>Status: <span className={overview?.status === 'ok' ? 'status-ok' : 'status-error'}>
                    {overview?.status?.toUpperCase()}
                </span></p>
                <p>Healthy: {overview?.healthy_modules} / {overview?.total_modules}</p>
            </div>

            <div className="modules-grid">
                {overview?.modules && Object.entries(overview.modules).map(([name, data]) => (
                    <div key={name} className="module-card">
                        <h3>{name}</h3>
                        <p>Status: <span className="status-ok">{data.status?.toUpperCase()}</span></p>
                        {data.version && <p>Version: {data.version}</p>}
                    </div>
                ))}
            </div>
        </div>
    );
};

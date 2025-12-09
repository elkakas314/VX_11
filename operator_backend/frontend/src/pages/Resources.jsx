import React, { useEffect, useState } from 'react';
import { operatorApi } from '../api/operatorClient';
import './Resources.jsx';

export const Resources = () => {
    const [resources, setResources] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetch = async () => {
            try {
                const res = await operatorApi.getResources();
                setResources(res.data);
            } catch (err) {
                console.error('Failed to fetch resources:', err);
            } finally {
                setLoading(false);
            }
        };
        fetch();
    }, []);

    if (loading) return <div>Loading...</div>;

    return (
        <div className="resources">
            <h2>Available Resources</h2>

            {resources?.cli_tools && (
                <div className="resource-section">
                    <h3>CLI Tools</h3>
                    <div className="resource-list">
                        {resources.cli_tools.map((tool, idx) => (
                            <div key={idx} className="resource-item">
                                <strong>{tool.name}</strong>
                                <span className={tool.available ? 'status-ok' : 'status-error'}>
                                    {tool.available ? '✓ Available' : '✗ Unavailable'}
                                </span>
                                {tool.version && <span className="version">v{tool.version}</span>}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {resources?.local_models && (
                <div className="resource-section">
                    <h3>Local Models</h3>
                    <div className="resource-list">
                        {resources.local_models.map((model, idx) => (
                            <div key={idx} className="resource-item">
                                <strong>{model.name}</strong>
                                <span className={model.available ? 'status-ok' : 'status-error'}>
                                    {model.available ? '✓' : '✗'} {model.size_mb}MB
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {resources?.available_tokens !== undefined && (
                <div className="resource-section">
                    <h3>Token Budget</h3>
                    <p>{resources.available_tokens} / {resources.max_tokens} tokens available</p>
                </div>
            )}
        </div>
    );
};

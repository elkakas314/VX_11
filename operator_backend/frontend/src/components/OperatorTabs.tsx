import React, { useState, useEffect } from 'react';
import './OperatorTabs.css';

type Tab = 'overview' | 'chat' | 'events' | 'routing';

export const OperatorTabs: React.FC<{ selectedModule?: string }> = ({
    selectedModule,
}) => {
    const [activeTab, setActiveTab] = useState<Tab>('overview');
    const [observeData, setObserveData] = useState<any>(null);
    const [observeFullResponse, setObserveFullResponse] = useState<any>(null);
    const [routingData, setRoutingData] = useState<any[]>([]);
    const [providersData, setProvidersData] = useState<any[]>([]);
    const [spawnsData, setSpawnsData] = useState<any[]>([]);

    // Fetch agregado status
    useEffect(() => {
        const fetchObserve = async () => {
            try {
                const resp = await fetch('/operator/observe');
                const data = await resp.json();
                setObserveData(data?.data?.services);
                setObserveFullResponse(data); // Store full response for provider/model tracing
            } catch (e) {
                console.error('Error fetching /operator/observe:', e);
            }
        };
        fetchObserve();
        const interval = setInterval(fetchObserve, 30000); // Refresh cada 30s
        return () => clearInterval(interval);
    }, []);

    // Fetch BD routing
    useEffect(() => {
        if (activeTab !== 'routing') return;
        const fetchRouting = async () => {
            try {
                const resp = await fetch('/api/db/routing-events?limit=50');
                const data = await resp.json();
                setRoutingData(data?.data?.events || []);
            } catch (e) {
                console.error('Error fetching routing:', e);
            }
        };
        fetchRouting();
    }, [activeTab]);

    // Fetch BD providers
    useEffect(() => {
        if (activeTab !== 'routing') return;
        const fetchProviders = async () => {
            try {
                const resp = await fetch('/api/db/cli-providers?limit=50');
                const data = await resp.json();
                setProvidersData(data?.data?.providers || []);
            } catch (e) {
                console.error('Error fetching providers:', e);
            }
        };
        fetchProviders();
    }, [activeTab]);

    // Fetch BD spawns
    useEffect(() => {
        if (activeTab !== 'routing') return;
        const fetchSpawns = async () => {
            try {
                const resp = await fetch('/api/db/spawns?limit=50');
                const data = await resp.json();
                setSpawnsData(data?.data?.spawns || []);
            } catch (e) {
                console.error('Error fetching spawns:', e);
            }
        };
        fetchSpawns();
    }, [activeTab]);

    const renderTabButton = (tab: Tab, label: string) => (
        <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`ot-tab-btn ${activeTab === tab ? 'ot-tab-btn--active' : ''}`}
        >
            {label}
        </button>
    );

    return (
        <div className="ot-tab-container">
            {/* Tab Buttons */}
            <div className="ot-tab-buttons">
                {renderTabButton('overview', 'Overview')}
                {renderTabButton('chat', 'Chat')}
                {renderTabButton('events', 'Events')}
                {renderTabButton('routing', 'Routing/DB')}
            </div>

            {/* Tab Content */}
            <div className="ot-tab-content">
                {activeTab === 'overview' && (
                    <OverviewTab observeData={observeData} observeFullResponse={observeFullResponse} />
                )}
                {activeTab === 'chat' && <ChatTab selectedModule={selectedModule} />}
                {activeTab === 'events' && <EventsTab />}
                {activeTab === 'routing' && (
                    <RoutingDbTab
                        routingData={routingData}
                        providersData={providersData}
                        spawnsData={spawnsData}
                    />
                )}
            </div>
        </div>
    );
};

// ============================================================================
// TAB: OVERVIEW
// ============================================================================
const OverviewTab: React.FC<{ observeData?: any; observeFullResponse?: any }> = ({ 
    observeData,
    observeFullResponse, 
}) => {
    if (!observeData) {
        return <div className="ot-loading">Loading overview...</div>;
    }

    return (
        <div>
            <h2 className="ot-heading">
                Module Status
            </h2>
            
            {/* DeepSeek R1 Tracing Info */}
            {observeFullResponse?.provider_used && (
                <div className="ot-trace-info">
                    <strong>Tracing:</strong>
                    <br />
                    <span className="ot-provider-badge">{observeFullResponse.provider_used}</span>
                    {observeFullResponse.model_used && (
                        <span className="ot-model-badge">{observeFullResponse.model_used}</span>
                    )}
                    <br />
                    <small>Request ID: {observeFullResponse.request_id?.substring(0, 8)}</small>
                </div>
            )}
            
            <div className="ot-grid-overview">
                {Object.entries(observeData).map(([name, status]: any) => (
                    <div key={name} className="ot-card">
                        <div className="ot-card-title">{name}</div>
                        <div
                            className={`ot-card-status ${status?.status === 'ok' ? 'ot-status-up' : 'ot-status-down'}`}
                        >
                            {status?.status === 'ok' ? '✓' : '✗'}
                        </div>
                        <div className="ot-card-meta">
                            {status?.status || 'unknown'}
                            {status?.latency_ms && ` | ${status.latency_ms}ms`}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

// ============================================================================
// TAB: CHAT (placeholder)
// ============================================================================
const ChatTab: React.FC<{ selectedModule?: string }> = ({
    selectedModule,
}) => {
    return (
        <div>
            <h2 className="ot-heading">
                Chat Console
            </h2>
            <p className="ot-muted">
                Chat interface goes here.
                {selectedModule && ` (Module: ${selectedModule})`}
            </p>
            <p className="ot-small">
                [Placeholder para TAB Chat - integrar ChatPanel aquí]
            </p>
        </div>
    );
};

// ============================================================================
// TAB: EVENTS (placeholder)
// ============================================================================
const EventsTab: React.FC = () => {
    return (
        <div>
            <h2 className="ot-heading">
                Events Stream
            </h2>
            <p className="ot-muted">
                Real-time events from /api/events (SSE).
            </p>
            <p className="ot-small">
                [Placeholder para TAB Events - integrar SSE + filtros]
            </p>
        </div>
    );
};

// ============================================================================
// TAB: ROUTING/DB
// ============================================================================
const RoutingDbTab: React.FC<{
    routingData: any[];
    providersData: any[];
    spawnsData: any[];
}> = ({ routingData, providersData, spawnsData }) => {
    const [subtab, setSubtab] = useState<'routing' | 'providers' | 'spawns'>(
        'routing'
    );

    return (
        <div>
            <h2 className="ot-heading ot-heading--small">
                Routing / DB
            </h2>

            {/* Subtab selector */}
            <div className="ot-subtab-selector">
                {(['routing', 'providers', 'spawns'] as const).map((st) => (
                    <button
                        key={st}
                        onClick={() => setSubtab(st)}
                        className={`ot-tab-btn ${subtab === st ? 'ot-tab-btn--active' : ''}`}
                    >
                        {st.charAt(0).toUpperCase() + st.slice(1)}
                    </button>
                ))}
            </div>

            {/* Tables */}
            {subtab === 'routing' && (
                <table className="ot-table">
                    <thead>
                        <tr>
                            <th className="ot-th">ID</th>
                            <th className="ot-th">Route</th>
                            <th className="ot-th">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {routingData.map((row, idx) => (
                            <tr key={idx}>
                                <td className="ot-td">{row.id || '-'}</td>
                                <td className="ot-td">{row.route || '-'}</td>
                                <td className="ot-td">{row.status || '-'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

            {subtab === 'providers' && (
                <table className="ot-table">
                    <thead>
                        <tr>
                            <th className="ot-th">ID</th>
                            <th className="ot-th">Provider</th>
                            <th className="ot-th">Model</th>
                        </tr>
                    </thead>
                    <tbody>
                        {providersData.map((row, idx) => (
                            <tr key={idx}>
                                <td className="ot-td">{row.id || '-'}</td>
                                <td className="ot-td">{row.provider || '-'}</td>
                                <td className="ot-td">{row.model || '-'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

            {subtab === 'spawns' && (
                <table className="ot-table">
                    <thead>
                        <tr>
                            <th className="ot-th">ID</th>
                            <th className="ot-th">Spawn</th>
                            <th className="ot-th">Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        {spawnsData.map((row, idx) => (
                            <tr key={idx}>
                                <td className="ot-td">{row.id || '-'}</td>
                                <td className="ot-td">{row.spawn || '-'}</td>
                                <td className="ot-td">{row.type || '-'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

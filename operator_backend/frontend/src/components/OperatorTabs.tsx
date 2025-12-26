import React, { useState, useEffect } from 'react';
import './OperatorTabs.css';
import { vx11Client } from '../lib/vx11Client';

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
    const [degraded, setDegraded] = useState(false);

    // Fetch agregado status (using vx11Client)
    useEffect(() => {
        const fetchObserve = async () => {
            const result = await vx11Client.getOperatorObserve();
            setDegraded(!result.ok || result.degraded || false);
            setObserveData(result.data || []);
            setObserveFullResponse(result);
        };
        fetchObserve();
        const interval = setInterval(fetchObserve, 5000); // Refresh cada 5s (was 30s)
        return () => clearInterval(interval);
    }, []);

    // Fetch routing events (using vx11Client)
    useEffect(() => {
        if (activeTab !== 'routing') return;
        const fetchRouting = async () => {
            const result = await vx11Client.getRoutingEvents(50);
            setRoutingData(result.events || []);
        };
        fetchRouting();
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
const OverviewTab: React.FC<{ observeData?: any; observeFullResponse?: any; degraded?: boolean }> = ({
    observeData,
    observeFullResponse,
    degraded,
}) => {
    if (!observeData || observeData.length === 0) {
        return (
            <div className="ot-loading">
                {degraded ? 'Degraded Mode: Unable to fetch services' : 'Loading overview...'}
            </div>
        );
    }

    const traceData = observeFullResponse?.data?.trace;
    const providerUsed = observeFullResponse?.provider_used ?? null;
    const modelUsed = observeFullResponse?.model_used ?? null;
    const requestId = observeFullResponse?.request_id;

    return (
        <div>
            <h2 className="ot-heading">
                Module Status
            </h2>

            {/* Tracing Info (null-safe) */}
            {traceData ? (
                <div className="ot-trace-info">
                    <strong>Last Route (Real Tracing):</strong>
                    <br />
                    <span className="ot-provider-badge">{traceData.provider_name}</span>
                    <br />
                    <small>
                        Trace ID: {traceData.trace_id?.substring(0, 8) ?? '—'} |
                        Type: {traceData.route_type ?? '—'} |
                        at {new Date(traceData.timestamp).toLocaleTimeString()}
                    </small>
                </div>
            ) : (providerUsed || modelUsed) ? (
                <div className="ot-trace-info">
                    <strong>Request Info:</strong>
                    <br />
                    {providerUsed && <span className="ot-provider-badge">{providerUsed}</span>}
                    {modelUsed && <span className="ot-model-badge">{modelUsed}</span>}
                    <br />
                    <small>Request ID: {requestId?.substring(0, 8) ?? '—'}</small>
                </div>
            ) : (
                <div className="ot-trace-info">
                    <small className="ot-muted">No tracing data available</small>
                </div>
            )}

            <div className="ot-grid-overview">
                {(Array.isArray(observeData) ? observeData : Object.entries(observeData).map(([name, status]) => ({ module_name: name, ...status }))).map((svc: any, idx: number) => (
                    <div key={svc.module_name || idx} className="ot-card">
                        <div className="ot-card-title">{svc.module_name || 'Unknown'}</div>
                        <div
                            className={`ot-card-status ${svc?.status === 'healthy' ? 'ot-status-up' : 'ot-status-down'}`}
                        >
                            {svc?.status === 'healthy' ? '✓' : '✗'}
                        </div>
                        <div className="ot-card-meta">
                            {svc?.status || 'unknown'}
                            {svc?.latency_ms && ` | ${svcdiv >
                                <div

                                    // ============================================================================
                                    const ChatTab:React.FC<{ selectedModule?: string; degraded?: boolean }> = ({
                                selectedModule,
                                degraded,
}) => {
    const [message, setMessage] = useState('');
                            const [sending, setSending] = useState(false);
                            const [responses, setResponses] = useState<any[]>([]);

    const handleSend = async () => {
        if (!message.trim()) return;
                            setSending(true);
                            const result = await vx11Client.postOperatorChat({message});
                            setSending(false);

        setResponses((prev) => [
                            ...prev,
                            {
                                ok: result.ok,
                            request_id: result.request_id,
                            route_taken: result.route_taken,
                            provider_used: result.provider_used ?? '—',
                            model_used: result.model_used ?? '—',
                            response: result.data?.response ?? (result.errors?.join('\n') || 'No response'),
            },
                            ]);
                            setMessage('');
    };

                            return (
                            <div style={{ padding: '1rem' }}>
                                <h2 className="ot-heading">Chat Console</h2>
                                {degraded && <div className="ot-muted">⚠️ Degraded: responses may be slow</div>}
                                {selectedModule && <div className="ot-small">Module: {selectedModule}</div>}

                                <div style={{ marginTop: '1rem', maxHeight: '200px', overflowY: 'auto', border: '1px solid #444', borderRadius: '4px', padding: '0.5rem', backgroundColor: '#1a1a1a' }}>
                                    {responses.map((r, idx) => (
                                        <div key={idx} style={{ marginBottom: '0.5rem', fontSize: '12px', color: r.ok ? '#0f0' : '#f00' }}>
                                            <div>{r.response}</div>
                                            <div style={{ color: '#888', marginTop: '4px' }}>
                                                ID: {r.request_id?.substring(0, 8)} | {r.provider_used} / {r.model_used}
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <textarea
                                    value={message}
                                    onChange={(e) => setMessage(e.target.value)}
                                    placeholder="Type a message..."
                                    style={{
                                        width: '100%',
                                        marginTop: '0.5rem',
                                        padding: '0.5rem',
                                        degraded?: boolean;
                                    } > = ({routingData, degraded}) => {
    const [subtab, setSubtab] = useState<'routing'>('routing');

                                return (
                                <div>
                                    <h2 className="ot-heading ot-heading--small">Routing Events</h2>
                                    {degraded && <div className="ot-muted">⚠️ Degraded: data may be incomplete</div>}

                                    {routingData.length === 0 ? (
                                        <div className="ot-muted">No routing events available</div>
                                    ) : (
                                        <table className="ot-table">
                                            <thead>
                                                <tr>
                                                    <th className="ot-th">ID</th>
                                                    <th className="ot-th">Route</th>
                                                    <th className="ot-th">Request ID</th>
                                                    <th className="ot-th">Status</th>
                                                    <th className="ot-th">Timestamp</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {routingData.map((row, idx) => (
                                                    <tr key={idx}>
                                                        <td className="ot-td" style={{ fontSize: '11px' }}>{row.id ?? idx}</td>
                                                        <td className="ot-td">{row.route_name ?? '-'}</td>
                                                        <td className="ot-td" style={{ fontSize: '10px' }}>{row.request_id?.substring(0, 8) ?? '-'}</td>
                                                        <td className="ot-td">{row.status ?? '-'}</td>
                                                        <td className="ot-td" style={{ fontSize: '10px' }}>{row.timestamp ??=============
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
}> = ({routingData, providersData, spawnsData}) => {
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

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
    const [degraded, setDegraded] = useState(false);

    // Fetch aggregated status every 5s (using vx11Client)
    useEffect(() => {
        const fetchObserve = async () => {
            const result = await vx11Client.getOperatorObserve();
            setDegraded(!result.ok || result.degraded || false);
            setObserveData(result.data || []);
            setObserveFullResponse(result);
        };
        fetchObserve();
        const interval = setInterval(fetchObserve, 5000);
        return () => clearInterval(interval);
    }, []);

    // Fetch routing events when tab is active (using vx11Client)
    useEffect(() => {
        if (activeTab !== 'routing') return;
        const fetchRouting = async () => {
            const result = await vx11Client.getRoutingEvents(50);
            setRoutingData(result.events || []);
        };
        fetchRouting();
        const interval = setInterval(fetchRouting, 10000);
        return () => clearInterval(interval);
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
                    <OverviewTab
                        observeData={observeData}
                        observeFullResponse={observeFullResponse}
                        degraded={degraded}
                    />
                )}
                {activeTab === 'chat' && (
                    <ChatTab selectedModule={selectedModule} degraded={degraded} />
                )}
                {activeTab === 'events' && <EventsTab degraded={degraded} />}
                {activeTab === 'routing' && (
                    <RoutingDbTab routingData={routingData} degraded={degraded} />
                )}
            </div>
        </div>
    );
};

// ============================================================================
// TAB: OVERVIEW
// ============================================================================
const OverviewTab: React.FC<{
    observeData?: any;
    observeFullResponse?: any;
    degraded?: boolean;
}> = ({
    observeData,
    observeFullResponse,
    degraded,
}) => {
        if (!observeData || observeData.length === 0) {
            return (
                <div className="ot-loading">
                    {degraded ? '⚠️ Degraded Mode: Unable to fetch services' : 'Loading overview...'}
                </div>
            );
        }

        const traceData = observeFullResponse?.data?.trace;
        const providerUsed = observeFullResponse?.provider_used ?? null;
        const modelUsed = observeFullResponse?.model_used ?? null;
        const requestId = observeFullResponse?.request_id ?? null;

        return (
            <div>
                <h2 className="ot-heading">Module Status</h2>

                {/* Tracing Info (null-safe) */}
                {traceData ? (
                    <div className="ot-trace-info">
                        <strong>Last Route (Real Tracing):</strong>
                        <br />
                        <span className="ot-provider-badge">{traceData.provider_name ?? '—'}</span>
                        <br />
                        <small>
                            Trace ID: {traceData.trace_id?.substring(0, 8) ?? '—'} |
                            Type: {traceData.route_type ?? '—'} |
                            at {traceData.timestamp
                                ? new Date(traceData.timestamp).toLocaleTimeString()
                                : '—'}
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

                {/* Service Cards */}
                <div className="ot-grid-overview">
                    {(Array.isArray(observeData)
                        ? observeData
                        : Object.entries(observeData).map(([name, status]) => ({
                            module_name: name,
                            ...(status && typeof status === 'object' ? status : { status })
                        }))
                    ).map((svc: any, idx: number) => (
                        <div key={svc.module_name || idx} className="ot-card">
                            <div className="ot-card-title">{svc.module_name ?? 'Unknown'}</div>
                            <div
                                className={`ot-card-status ${svc?.status === 'healthy'
                                        ? 'ot-status-up'
                                        : 'ot-status-down'
                                    }`}
                            >
                                {svc?.status === 'healthy' ? '✓' : '✗'}
                            </div>
                            <div className="ot-card-meta">
                                {svc?.status ?? 'unknown'}
                                {svc?.latency_ms
                                    ? ` | ${svc.latency_ms}ms`
                                    : ''}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

// ============================================================================
// TAB: CHAT
// ============================================================================
const ChatTab: React.FC<{
    selectedModule?: string;
    degraded?: boolean;
}> = ({
    selectedModule,
    degraded,
}) => {
        const [message, setMessage] = useState('');
        const [sending, setSending] = useState(false);
        const [responses, setResponses] = useState<any[]>([]);

        const handleSend = async () => {
            if (!message.trim()) return;
            setSending(true);
            const result = await vx11Client.postOperatorChat({ message });
            setSending(false);

            setResponses((prev) => [
                ...prev,
                {
                    ok: result.ok,
                    request_id: result.request_id ?? '—',
                    route_taken: result.route_taken ?? '—',
                    provider_used: result.provider_used ?? '—',
                    model_used: result.model_used ?? '—',
                    response: result.data?.response ?? (result.errors?.join('\n') || 'No response'),
                },
            ]);
            setMessage('');
        };

        const handleKeyPress = (e: React.KeyboardEvent) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        };

        return (
            <div className="ot-chat-container">
                <h2 className="ot-heading">Chat Console</h2>
                {degraded && <div className="ot-muted">⚠️ Degraded: responses may be slow</div>}
                {selectedModule && (
                    <div className="ot-small">
                        Module: <strong>{selectedModule}</strong>
                    </div>
                )}

                {/* Response History */}
                <div className="ot-response-history">
                    {responses.length === 0 ? (
                        <div className="ot-muted ot-response-empty">
                            No responses yet
                        </div>
                    ) : (
                        responses.map((r, idx) => (
                            <div
                                key={idx}
                                className={`ot-response-item ${r.ok ? 'ot-response-item--ok' : 'ot-response-item--error'}`}
                            >
                                <div className="ot-response-content">{r.response}</div>
                                <div className="ot-response-meta">
                                    ID: {r.request_id?.substring(0, 8) ?? '—'} |
                                    {r.provider_used} / {r.model_used}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Input Area */}
                <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type a message... (Enter to send, Shift+Enter for newline)"
                    className="ot-textarea"
                    disabled={sending}
                />
                <button
                    onClick={handleSend}
                    disabled={sending}
                    className="ot-button"
                >
                    {sending ? 'Sending...' : 'Send'}
                </button>
            </div>
        );
    };

// ============================================================================
// TAB: EVENTS
// ============================================================================
const EventsTab: React.FC<{ degraded?: boolean }> = ({ degraded }) => {
    const [events, setEvents] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchEvents = async () => {
            setLoading(true);
            const result = await vx11Client.getRoutingEvents(20);
            setEvents(result.events || []);
            setLoading(false);
        };
        fetchEvents();
        const interval = setInterval(fetchEvents, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="ot-events-container">
            <h2 className="ot-heading">Events Stream</h2>
            {degraded && <div className="ot-muted">⚠️ Degraded: events may be delayed</div>}
            <p className="ot-muted ot-events-note">
                Real-time events from /hormiguero/report (polling every 10s)
            </p>

            {loading ? (
                <div className="ot-loading">Loading events...</div>
            ) : events.length === 0 ? (
                <div className="ot-muted">No events available</div>
            ) : (
                <table className="ot-table">
                    <thead>
                        <tr>
                            <th className="ot-th">ID</th>
                            <th className="ot-th">Route Name</th>
                            <th className="ot-th">Request ID</th>
                            <th className="ot-th">Status</th>
                            <th className="ot-th">Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        {events.map((row, idx) => (
                            <tr key={idx}>
                                <td className="ot-td ot-table-cell--small">
                                    {row.id ?? idx}
                                </td>
                                <td className="ot-td">{row.route_name ?? '—'}</td>
                                <td className="ot-td ot-table-cell--xs">
                                    {row.request_id?.substring(0, 8) ?? '—'}
                                </td>
                                <td className="ot-td">{row.status ?? '—'}</td>
                                <td className="ot-td ot-table-cell--xs">
                                    {row.timestamp
                                        ? new Date(row.timestamp).toLocaleTimeString()
                                        : '—'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

// ============================================================================
// TAB: ROUTING/DB
// ============================================================================
const RoutingDbTab: React.FC<{
    routingData: any[];
    degraded?: boolean;
}> = ({ routingData, degraded }) => {
    return (
        <div className="ot-routing-container">
            <h2 className="ot-heading">Routing Events (DB)</h2>
            {degraded && <div className="ot-muted">⚠️ Degraded: data may be incomplete</div>}

            {routingData.length === 0 ? (
                <div className="ot-muted">No routing events available</div>
            ) : (
                <table className="ot-table">
                    <thead>
                        <tr>
                            <th className="ot-th">ID</th>
                            <th className="ot-th">Route Name</th>
                            <th className="ot-th">Request ID</th>
                            <th className="ot-th">Status</th>
                            <th className="ot-th">Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        {routingData.map((row, idx) => (
                            <tr key={idx}>
                                <td className="ot-td ot-table-cell--small">
                                    {row.id ?? idx}
                                </td>
                                <td className="ot-td">{row.route_name ?? '—'}</td>
                                <td className="ot-td ot-table-cell--xs">
                                    {row.request_id?.substring(0, 8) ?? '—'}
                                </td>
                                <td className="ot-td">{row.status ?? '—'}</td>
                                <td className="ot-td ot-table-cell--xs">
                                    {row.timestamp
                                        ? new Date(row.timestamp).toLocaleTimeString()
                                        : '—'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

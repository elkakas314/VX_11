import React, { useState, useEffect } from 'react';
import './OperatorTabs.css';

type Tab = 'overview' | 'chat' | 'events' | 'routing';

const styles: { [key: string]: React.CSSProperties } = {
    tabContainer: {
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
    } as React.CSSProperties,
    tabButtons: {
        display: 'flex',
        gap: '8px',
        padding: '12px',
        backgroundColor: '#0a0a0a',
        borderBottom: '1px solid #333',
    } as React.CSSProperties,
    tabBtn: {
        padding: '8px 16px',
        backgroundColor: '#1a1a1a',
        border: '1px solid #444',
        color: '#e0e0e0',
        cursor: 'pointer',
        borderRadius: '4px',
        fontSize: '13px',
        transition: 'all 0.2s',
    } as React.CSSProperties,
    tabBtnActive: {
        backgroundColor: '#4ade80',
        color: '#000',
        borderColor: '#4ade80',
    } as React.CSSProperties,
    tabContent: {
        flex: 1,
        overflow: 'auto',
        padding: '16px',
    } as React.CSSProperties,
    table: {
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: '12px',
        color: '#e0e0e0',
    } as React.CSSProperties,
    th: {
        textAlign: 'left',
        padding: '8px',
        borderBottom: '1px solid #444',
        backgroundColor: '#1a1a1a',
        fontWeight: 'bold',
    } as React.CSSProperties,
    td: {
        padding: '8px',
        borderBottom: '1px solid #222',
    } as React.CSSProperties,
    statusUp: {
        color: '#4ade80',
    } as React.CSSProperties,
    statusDown: {
        color: '#ef4444',
    } as React.CSSProperties,
    gridOverview: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '12px',
    } as React.CSSProperties,
    card: {
        backgroundColor: '#1a1a1a',
        border: '1px solid #333',
        padding: '12px',
        borderRadius: '4px',
        minHeight: '100px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
    } as React.CSSProperties,
    cardTitle: {
        fontSize: '14px',
        fontWeight: 'bold',
        marginBottom: '8px',
    } as React.CSSProperties,
    cardStatus: {
        fontSize: '24px',
        fontWeight: 'bold',
        marginBottom: '4px',
    } as React.CSSProperties,
    cardMeta: {
        fontSize: '11px',
        color: '#888',
    } as React.CSSProperties,
};

export const OperatorTabs: React.FC<{ selectedModule?: string }> = ({
    selectedModule,
}) => {
    const [activeTab, setActiveTab] = useState<Tab>('overview');
    const [observeData, setObserveData] = useState<any>(null);
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
            style={{
                ...styles.tabBtn,
                ...(activeTab === tab ? styles.tabBtnActive : {}),
            }}
        >
            {label}
        </button>
    );

    return (
        <div style={styles.tabContainer}>
            {/* Tab Buttons */}
            <div style={styles.tabButtons}>
                {renderTabButton('overview', 'Overview')}
                {renderTabButton('chat', 'Chat')}
                {renderTabButton('events', 'Events')}
                {renderTabButton('routing', 'Routing/DB')}
            </div>

            {/* Tab Content */}
            <div style={styles.tabContent}>
                {activeTab === 'overview' && (
                    <OverviewTab observeData={observeData} />
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
const OverviewTab: React.FC<{ observeData?: any }> = ({ observeData }) => {
    if (!observeData) {
        return <div style={{ color: '#888' }}>Loading overview...</div>;
    }

    return (
        <div>
            <h2 className="ot-heading">
                Module Status
            </h2>
            <div style={styles.gridOverview}>
                {Object.entries(observeData).map(([name, status]: any) => (
                    <div key={name} style={styles.card}>
                        <div style={styles.cardTitle}>{name}</div>
                        <div
                            style={{
                                ...styles.cardStatus,
                                color:
                                    status?.status === 'ok' ? '#4ade80' : '#ef4444',
                            }}
                        >
                            {status?.status === 'ok' ? '✓' : '✗'}
                        </div>
                        <div style={styles.cardMeta}>
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
            <p style={{ color: '#888' }}>
                Chat interface goes here.
                {selectedModule && ` (Module: ${selectedModule})`}
            </p>
            <p style={{ fontSize: '12px', color: '#666' }}>
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
            <p style={{ color: '#888' }}>
                Real-time events from /api/events (SSE).
            </p>
            <p style={{ fontSize: '12px', color: '#666' }}>
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
            <div style={{ marginBottom: '12px', display: 'flex', gap: '8px' }}>
                {(['routing', 'providers', 'spawns'] as const).map((st) => (
                    <button
                        key={st}
                        onClick={() => setSubtab(st)}
                        style={{
                            ...styles.tabBtn,
                            ...(subtab === st ? styles.tabBtnActive : {}),
                        }}
                    >
                        {st.charAt(0).toUpperCase() + st.slice(1)}
                    </button>
                ))}
            </div>

            {/* Tables */}
            {subtab === 'routing' && (
                <table style={styles.table}>
                    <thead>
                        <tr>
                            <th style={styles.th}>ID</th>
                            <th style={styles.th}>Route</th>
                            <th style={styles.th}>Status</th>
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
                <table style={styles.table}>
                    <thead>
                        <tr>
                            <th style={styles.th}>ID</th>
                            <th style={styles.th}>Provider</th>
                            <th style={styles.th}>Model</th>
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
                <table style={styles.table}>
                    <thead>
                        <tr>
                            <th style={styles.th}>ID</th>
                            <th style={styles.th}>Spawn</th>
                            <th style={styles.th}>Type</th>
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

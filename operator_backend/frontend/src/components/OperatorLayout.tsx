import React, { useState } from 'react';
import { DashboardPanel } from './DashboardPanel';
import { ChatPanel } from './ChatPanel';
import { ControlPanel } from './ControlPanel';

export const OperatorLayout: React.FC = () => {
    const [selectedModule, setSelectedModule] = useState<string | undefined>();
    const [theme, setTheme] = useState<'dark' | 'light'>('dark');

    return (
        <div
            style={{
                ...styles.container,
                backgroundColor: theme === 'dark' ? '#1a1a1a' : '#f5f5f5',
                color: theme === 'dark' ? '#e0e0e0' : '#333',
            }}
        >
            {/* Header */}
            <div
                style={{
                    ...styles.header,
                    backgroundColor: theme === 'dark' ? '#0a0a0a' : '#e0e0e0',
                    borderColor: theme === 'dark' ? '#333' : '#ccc',
                }}
            >
                <h1 style={styles.title}>VX11 Operator Visor</h1>
                <div style={styles.headerControls}>
                    <span style={styles.badge}>PHASE D Complete</span>
                    <button
                        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                        style={styles.themeButton}
                    >
                        {theme === 'dark' ? '☀️' : '🌙'}
                    </button>
                </div>
            </div>

            {/* Main Grid Layout */}
            <div style={styles.mainGrid}>
                {/* Left Panel: Dashboard */}
                <div style={styles.leftPanel}>
                    <DashboardPanel onModuleSelect={setSelectedModule} />
                </div>

                {/* Center Panel: Chat/Events */}
                <div style={styles.centerPanel}>
                    <ChatPanel autoRefresh={true} />
                </div>

                {/* Right Panel: Controls */}
                <div style={styles.rightPanel}>
                    <ControlPanel selectedModule={selectedModule} />
                </div>
            </div>
        </div>
    );
};

const styles = {
    container: {
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column' as const,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    },
    header: {
        padding: '12px 16px',
        borderBottom: '1px solid',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    title: {
        margin: 0,
        fontSize: '18px',
        fontWeight: 'bold',
    },
    headerControls: {
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
    },
    badge: {
        backgroundColor: '#4ade80',
        color: '#000',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 'bold',
    },
    themeButton: {
        fontSize: '16px',
        backgroundColor: 'transparent',
        border: 'none',
        cursor: 'pointer',
    },
    mainGrid: {
        flex: 1,
        display: 'grid',
        gridTemplateColumns: '250px 1fr 300px',
        gap: 0,
        overflow: 'hidden',
    },
    leftPanel: {
        borderRight: '1px solid #333',
        overflow: 'hidden',
    },
    centerPanel: {
        borderRight: '1px solid #333',
        overflow: 'hidden',
    },
    rightPanel: {
        overflow: 'hidden',
    },
};

// Responsive media query handler (for mobile)
if (typeof window !== 'undefined' && window.matchMedia('(max-width: 768px)').matches) {
    styles.mainGrid = {
        ...styles.mainGrid,
        gridTemplateColumns: '1fr',
        gridTemplateRows: 'auto 1fr auto',
    };
}

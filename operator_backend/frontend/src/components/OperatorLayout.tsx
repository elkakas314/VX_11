import React, { useState } from 'react';
import { DashboardPanel } from './DashboardPanel';
import { ChatPanel } from './ChatPanel';
import { ControlPanel } from './ControlPanel';
import './OperatorLayout.css';

export const OperatorLayout: React.FC = () => {
    const [selectedModule, setSelectedModule] = useState<string | undefined>();
    const [theme, setTheme] = useState<'dark' | 'light'>('dark');

    return (
        <div className={`operator-layout ${theme}`}>
            {/* Header */}
            <header className="ol-header">
                <h1 className="ol-title">VX11 Operator Visor</h1>
                <div className="ol-header-controls">
                    <span className="ol-badge">PHASE D Complete</span>
                    <button
                        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                        className="ol-theme-button"
                    >
                        {theme === 'dark' ? '☀️' : '🌙'}
                    </button>
                </div>
                c            </header>

            {/* Main Grid Layout */}
            <div className="ol-main-grid">
                {/* Left Panel: Dashboard */}
                <aside className="ol-left-panel">
                    <DashboardPanel onModuleSelect={setSelectedModule} />
                </aside>

                {/* Center Panel: Chat/Events */}
                <main className="ol-center-panel">
                    <ChatPanel events={[]} />
                </main>

                {/* Right Panel: Controls */}
                <aside className="ol-right-panel">
                    <ControlPanel selectedModule={selectedModule} />
                </aside>
            </div>
        </div>
    );
};

import React from 'react';
import './Layout.css';

export const Layout = ({ children }) => {
    return (
        <div className="layout">
            <header className="layout-header">
                <h1>VX11 Operator v7</h1>
                <nav className="nav">
                    <a href="/">Dashboard</a>
                    <a href="/chat">Chat</a>
                    <a href="/shub">Shub</a>
                    <a href="/resources">Resources</a>
                    <a href="/browser">Browser</a>
                </nav>
            </header>
            <main className="layout-main">
                {children}
            </main>
        </div>
    );
};

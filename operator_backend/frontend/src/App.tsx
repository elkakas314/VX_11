import { OPERATOR_BASE_URL } from "./config";
import React, { useState, useEffect } from "react";
import { initializeAuth, clearAuth, verifyToken } from "./api/canonical";
import { LoginPage } from "./components/LoginPage";
import { DashboardTab } from "./components/DashboardTab";
import { ChatTab } from "./components/ChatTab";
import { MapTab } from "./components/MapTab";
import { ModulesTab } from "./components/ModulesTab";
import { JobsTab } from "./components/JobsTab";
import { EventsTab } from "./components/EventsTab";
import { AuditTab } from "./components/AuditTab";
import { OverviewTab } from "./components/OverviewTab";
import { TopologyTab } from "./components/TopologyTab";
import { MetricsTab } from "./components/MetricsTab";
import { AuditRunsTab } from "./components/AuditRunsTab";
import { SettingsTab } from "./components/SettingsTab";
import { TabName } from "./types/canonical";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState<TabName>("overview");
  const [verifying, setVerifying] = useState(true);
  const [username, setUsername] = useState<string | null>(null);
  const [showLeftPanel, setShowLeftPanel] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [madreHealth, setMadreHealth] = useState<{ status: string; healthy: boolean } | null>(null);
  const [backendHealth, setBackendHealth] = useState<{ status: string; healthy: boolean } | null>(null);

  // Initialize auth on mount
  useEffect(() => {
    initializeAuth();
    verifyStoredToken();
    // Poll health every 5s
    const healthInterval = setInterval(() => {
      pollHealth();
    }, 5000);
    return () => clearInterval(healthInterval);
  }, []);

  const verifyStoredToken = async () => {
    const result = await verifyToken();
    if (!("error" in result) && result.valid) {
      setUsername(result.user_id || "User");
      setIsLoggedIn(true);
    }
    setVerifying(false);
  };

  const pollHealth = async () => {
    // Check health via tentaculo_link (single entrypoint 8000)
    // Proxied endpoints: madre, backend health accessible through 8000 only
    try {
      const r = await fetch(`${OPERATOR_BASE_URL}/health`, { method: "GET" });
      if (r.ok) setMadreHealth({ status: "ok", healthy: true });
      else setMadreHealth({ status: "error", healthy: false });
    } catch {
      setMadreHealth({ status: "offline", healthy: false });
    }
    // Backend health also goes through tentaculo (8000)
    try {
      const r = await fetch(`${OPERATOR_BASE_URL}/operator/observe`, { method: "GET" });
      if (r.ok) setBackendHealth({ status: "ok", healthy: true });
      else setBackendHealth({ status: "error", healthy: false });
    } catch {
      setBackendHealth({ status: "offline", healthy: false });
    }
  };

  const handleLogout = () => {
    clearAuth();
    setIsLoggedIn(false);
    setUsername(null);
    setActiveTab("overview");
  };

  const tabs: { id: TabName; label: string; icon: string }[] = [
    { id: "overview", label: "Overview", icon: "📊" },
    { id: "chat", label: "Chat", icon: "💬" },
    { id: "topology", label: "Topology", icon: "🗺️" },
    { id: "hormiguero", label: "Hormiguero", icon: "🐜" },
    { id: "jobs", label: "Jobs", icon: "⚡" },
    { id: "audit", label: "Audit", icon: "📋" },
    { id: "explorer", label: "Explorer", icon: "🔍" },
    { id: "settings", label: "Settings", icon: "⚙️" },
  ];

  // Show login if not authenticated
  if (!isLoggedIn && !verifying) {
    return <LoginPage onLoginSuccess={() => setIsLoggedIn(true)} />;
  }

  // Loading state
  if (verifying) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Initializing...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-white">
      {/* Top Bar */}
      <div className="bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">VX11 Operator</h1>
          <span className="text-slate-400 text-sm">Canonical Control Panel</span>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-300">{username}</span>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded font-medium transition-colors text-sm"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main 3-Panel Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT PANEL: Sessions & Modules Sidebar */}
        <aside className={`
          w-64 bg-slate-800 border-r border-slate-700 overflow-y-auto flex-shrink-0
          ${showLeftPanel ? "block" : "hidden"} md:block
        `}>
          <div className="p-4">
            <h2 className="text-lg font-bold mb-4 text-blue-400">Sessions</h2>
            <div className="space-y-2 text-sm text-slate-300">
              <div className="p-2 bg-slate-700 rounded hover:bg-slate-600 cursor-pointer">Session 1</div>
              <div className="p-2 bg-slate-700 rounded hover:bg-slate-600 cursor-pointer">Session 2</div>
            </div>

            <h2 className="text-lg font-bold my-4 text-green-400">Modules</h2>
            <div className="space-y-1 text-sm">
              <div className="p-2 bg-slate-700 rounded">📡 Madre</div>
              <div className="p-2 bg-slate-700 rounded">🔗 Tentáculo</div>
              <div className="p-2 bg-slate-700 rounded">⚙️ Switch</div>
            </div>
          </div>
        </aside>

        {/* CENTER PANEL: Tabs + Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab Navigation */}
          <nav className="bg-slate-800 border-b border-slate-700 overflow-x-auto flex-shrink-0">
            <div className="flex gap-1 px-4 py-0">
              {/* Mobile collapse button */}
              <button
                onClick={() => setShowLeftPanel(!showLeftPanel)}
                className="md:hidden px-2 py-3 text-slate-400 hover:text-white hover:bg-slate-700 border-b-2 border-transparent"
                title="Toggle sidebar"
              >
                ☰
              </button>

              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-3 font-medium transition-colors border-b-2 whitespace-nowrap text-sm ${activeTab === tab.id
                    ? "border-blue-500 text-white bg-slate-700/50"
                    : "border-transparent text-slate-400 hover:text-white hover:bg-slate-700/30"
                    }`}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>
          </nav>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto p-6">
            <div className="max-w-full">
              {activeTab === "overview" && <OverviewTab />}
              {activeTab === "chat" && <ChatTab />}
              {activeTab === "topology" && <TopologyTab />}
              {activeTab === "hormiguero" && <ModulesTab />}
              {activeTab === "jobs" && <JobsTab />}
              {activeTab === "audit" && <AuditRunsTab />}
              {activeTab === "explorer" && <MapTab />}
              {activeTab === "settings" && <SettingsTab />}
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: Health Status & Logs */}
        <aside className={`
          w-72 bg-slate-800 border-l border-slate-700 overflow-y-auto flex-shrink-0
          ${showRightPanel ? "block" : "hidden"} lg:block
        `}>
          <div className="p-4 border-b border-slate-700">
            <h2 className="text-lg font-bold mb-3 text-amber-400">System Health</h2>

            {/* Madre Status (via tentaculo_link:8000) */}
            <div className="mb-4 p-3 bg-slate-700 rounded">
              <div className="flex items-center gap-2 mb-1">
                <span className={`inline-block w-3 h-3 rounded-full ${madreHealth?.healthy ? "bg-green-500" : "bg-red-500"}`}></span>
                <span className="font-bold text-sm">Core (via 8000)</span>
              </div>
              <div className="text-xs text-slate-400">
                {madreHealth?.status === "ok" ? "✓ Running" : "✗ Offline"}
              </div>
            </div>

            {/* Backend Status */}
            <div className="p-3 bg-slate-700 rounded">
              <div className="flex items-center gap-2 mb-1">
                <span className={`inline-block w-3 h-3 rounded-full ${backendHealth?.healthy ? "bg-green-500" : "bg-red-500"}`}></span>
                <span className="font-bold text-sm">Operator (via 8000)</span>
              </div>
              <div className="text-xs text-slate-400">
                {backendHealth?.status === "ok" ? "✓ Running" : "✗ Offline"}
              </div>
            </div>
          </div>

          {/* Recent Logs */}
          <div className="p-4">
            <h3 className="text-sm font-bold mb-3 text-slate-300">Recent Events</h3>
            <div className="space-y-2 text-xs text-slate-400">
              <div className="p-2 bg-slate-700 rounded border-l-2 border-blue-500">
                📨 Message sent
              </div>
              <div className="p-2 bg-slate-700 rounded border-l-2 border-green-500">
                ✓ Session created
              </div>
              <div className="p-2 bg-slate-700 rounded border-l-2 border-yellow-500">
                ⚠️ Mode: Degraded
              </div>
            </div>
          </div>

          {/* Collapse button (mobile) */}
          <button
            onClick={() => setShowRightPanel(!showRightPanel)}
            className="lg:hidden w-full p-3 text-slate-400 hover:text-white text-sm border-t border-slate-700"
          >
            {showRightPanel ? "Hide Status" : "Show Status"}
          </button>
        </aside>
      </div>
    </div>
  );
}

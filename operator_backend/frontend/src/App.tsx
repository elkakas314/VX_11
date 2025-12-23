import React, { useState, useEffect } from "react";
import { initializeAuth, clearAuth, verifyToken } from "./api/canonical";
import { LoginPage } from "./components/LoginPage";
import { DashboardTab } from "./components/DashboardTab";
import { ChatTab } from "./components/ChatTab";
import { ModulesTab } from "./components/ModulesTab";
import { JobsTab } from "./components/JobsTab";
import { EventsTab } from "./components/EventsTab";
import { AuditTab } from "./components/AuditTab";
import { TabName } from "./types/canonical";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState<TabName>("dashboard");
  const [verifying, setVerifying] = useState(true);
  const [username, setUsername] = useState<string | null>(null);

  // Initialize auth on mount
  useEffect(() => {
    initializeAuth();
    verifyStoredToken();
  }, []);

  const verifyStoredToken = async () => {
    const result = await verifyToken();
    if (!("error" in result) && result.valid) {
      setUsername(result.user_id || "User");
      setIsLoggedIn(true);
    }
    setVerifying(false);
  };

  const handleLogout = () => {
    clearAuth();
    setIsLoggedIn(false);
    setUsername(null);
    setActiveTab("dashboard");
  };

  const tabs: { id: TabName; label: string; icon: string }[] = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "chat", label: "Chat", icon: "💬" },
    { id: "modules", label: "Modules", icon: "🧩" },
    { id: "jobs", label: "Jobs", icon: "⚙️" },
    { id: "events", label: "Events", icon: "📢" },
    { id: "audit", label: "Audit", icon: "📋" },
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
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Top Bar */}
      <div className="bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
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

      {/* Tabs Navigation */}
      <div className="bg-slate-800 border-b border-slate-700 overflow-x-auto">
        <div className="flex gap-1 px-6 py-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 font-medium transition-colors border-b-2 whitespace-nowrap ${activeTab === tab.id
                  ? "border-blue-500 text-white bg-slate-700/50"
                  : "border-transparent text-slate-400 hover:text-white hover:bg-slate-700/30"
                }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6">
        <div className="max-w-7xl mx-auto">
          {activeTab === "dashboard" && <DashboardTab />}
          {activeTab === "chat" && <ChatTab />}
          {activeTab === "modules" && <ModulesTab />}
          {activeTab === "jobs" && <JobsTab />}
          {activeTab === "events" && <EventsTab />}
          {activeTab === "audit" && <AuditTab />}
        </div>
      </div>
    </div>
  );
}

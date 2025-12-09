import React, { useEffect, useMemo, useState } from "react";
import { fetchJSON, fetchSystemStatus, fetchUiEvents, sendChat, validateManifest, wsConnect } from "./services/api";
import { Dashboard } from "./components/Dashboard";
import { ChatPanel } from "./components/ChatPanel";
import { ShubPanel } from "./components/ShubPanel";
import { StatusBar } from "./components/StatusBar";
import { MiniStatusPanel } from "./components/MiniStatusPanel";
import { MadrePanel } from "./components/MadrePanel";
import { SpawnerPanel } from "./components/SpawnerPanel";
import { SwitchQueuePanel } from "./components/SwitchQueuePanel";
import { HermesPanel } from "./components/HermesPanel";
import { MCPPanel } from "./components/MCPPanel";
import { HormigueroPanel } from "./components/HormigueroPanel";
import { MiniMapPanel } from "./components/MiniMapPanel";
import { LogsPanel } from "./components/LogsPanel";
import { POLL_INTERVAL_MS, EVENTS_LIMIT } from "./config";

type EventMessage = { channel?: string; type?: string; payload?: any; source?: string };

export default function App() {
  const [status, setStatus] = useState<any>({});
  const [events, setEvents] = useState<EventMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    const poll = () => fetchSystemStatus().then(setStatus).catch(() => { });
    poll();
    const statusInterval = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(statusInterval);
  }, []);

  useEffect(() => {
    const pollEvents = () =>
      fetchUiEvents()
        .then((res) => setEvents(res.events || []))
        .catch(() => { });
    pollEvents();
    const eventsInterval = setInterval(pollEvents, POLL_INTERVAL_MS);
    const socket = wsConnect(
      (msg) => {
        try {
          const data = JSON.parse(msg.data);
          setEvents((prev) => [data, ...prev].slice(0, EVENTS_LIMIT));
        } catch {
          setEvents((prev) => [{ channel: "raw", payload: msg.data }, ...prev].slice(0, EVENTS_LIMIT));
        }
      },
      () => setConnected(true),
      () => setConnected(false)
    );
    return () => {
      clearInterval(eventsInterval);
      socket?.close();
    };
  }, []);

  const healthSummary = useMemo(() => status?.modules || {}, [status]);

  const handleManifestValidate = async (manifest: string) => {
    const res = await validateManifest(manifest);
    alert(JSON.stringify(res, null, 2));
  };

  const handleSendChat = async (message: string, mode: string, metadata?: any) => {
    return sendChat(message, mode, metadata || {});
  };

  return (
    <div className="page">
      <StatusBar connected={connected} modules={healthSummary} />
      <div style={{ display: "flex", gap: "10px", padding: "10px", background: "#f5f5f5", borderBottom: "1px solid #ddd" }}>
        <button
          onClick={() => setActiveTab("overview")}
          style={{
            padding: "5px 10px",
            background: activeTab === "overview" ? "#2196F3" : "#ccc",
            color: "white",
            border: "none",
            borderRadius: "3px",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          Vista General
        </button>
        <button
          onClick={() => setActiveTab("modules")}
          style={{
            padding: "5px 10px",
            background: activeTab === "modules" ? "#2196F3" : "#ccc",
            color: "white",
            border: "none",
            borderRadius: "3px",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          Módulos VX11
        </button>
        <button
          onClick={() => setActiveTab("chat")}
          style={{
            padding: "5px 10px",
            background: activeTab === "chat" ? "#2196F3" : "#ccc",
            color: "white",
            border: "none",
            borderRadius: "3px",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          Chat + Shub
        </button>
      </div>

      <div className="layout">
        {activeTab === "overview" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", padding: "10px", width: "100%", maxHeight: "calc(100vh - 200px)", overflow: "auto" }}>
            <Dashboard status={status} events={events} onValidateManifest={handleManifestValidate} />
            <MiniMapPanel status={status} />
            <LogsPanel />
            <MiniStatusPanel status={status} />
          </div>
        )}

        {activeTab === "modules" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", padding: "10px", width: "100%", maxHeight: "calc(100vh - 200px)", overflow: "auto" }}>
            <MadrePanel />
            <SpawnerPanel />
            <SwitchQueuePanel />
            <HermesPanel />
            <MCPPanel />
            <HormigueroPanel />
          </div>
        )}

        {activeTab === "chat" && (
          <div className="panels" style={{ width: "100%", display: "flex", gap: "10px", padding: "10px" }}>
            <ChatPanel onSend={handleSendChat} events={events} />
            <ShubPanel />
          </div>
        )}
      </div>
    </div>
  );
}

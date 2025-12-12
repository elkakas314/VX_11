import React, { useMemo, useState } from "react";
import { sendChat } from "./services/api";
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
import { DeepSeekHelper } from "./components/DeepSeekHelper";
import { ShortcutsPanel } from "./components/ShortcutsPanel";
import { SimpleApp } from "./simple/SimpleApp";
import { useOperatorStreams } from "./hooks/useOperatorStreams";
import { MiniMapPanel } from "./components/MiniMapPanel";
import { EventsTimelinePanel } from "./components/EventsTimelinePanel";
import { LogsPanel } from "./components/LogsPanel";
import { ManifestatorPanel } from "./components/ManifestatorPanel";
import { BrowserPanel } from "./components/BrowserPanel";
import { HormigueroMapPanel } from "./components/HormigueroMapPanel";
import { SelfOverviewPanel } from "./components/SelfOverviewPanel";
import { useOperatorStore } from "./store/operatorStore";

// === SIMPLE MODE SUPPORT ===
// Activa modo simple con env var o URL param ?simple=1
const SIMPLE_MODE =
  import.meta.env.VITE_OPERATOR_SIMPLE_MODE === "true" ||
  new URLSearchParams(window.location.search).get("simple") === "1";

type EventMessage = { channel?: string; type?: string; payload?: any; source?: string; data?: any; module?: string; level?: string; timestamp?: string };

export default function App() {
  const { status, events, connected, statusError, eventsError, bridgeHealth } = useOperatorStreams();
  const activeTab = useOperatorStore((state) => state.ui.activeTab);
  const setActiveTab = useOperatorStore((state) => state.ui.setActiveTab);
  const profiles = [
    { name: "VX11 Default", channel: "tentacular", intent: "default", mode: "tentacular" },
    { name: "Auditor VX11", channel: "ot", intent: "analysis", mode: "analitico" },
    { name: "DeepSeek Helper", channel: "tentacular", intent: "deepseek-helper", mode: "analitico" },
    { name: "Ingeniero de sonido (Shub)", channel: "dsp", intent: "operator", mode: "tentacular", extra: { channel: "dsp", mode: "shub" } },
  ];
  const [activeProfile, setActiveProfile] = useState(profiles[0]);

  const healthSummary = useMemo(() => status?.modules || {}, [status]);

  const handleSendChat = async (message: string, mode: string, metadata?: any) => {
    return sendChat(message, mode, metadata || {});
  };

  // Simple mode: renderizar solo Chat + StatusBar (desde simple/SimpleApp.tsx)
  if (SIMPLE_MODE) {
    return <SimpleApp />;
  }

  const renderPlaceholder = (title: string, children?: React.ReactNode) => (
    <div className="card">
      <div className="card-header">
        <h3 style={{ margin: 0 }}>{title}</h3>
      </div>
      <div style={{ fontSize: "13px", color: "#9fb4cc" }}>{children || "Placeholder conectado a system/status."}</div>
    </div>
  );

  return (
    <div className="page">
      <StatusBar connected={connected} modules={healthSummary} />
      <div style={{ display: "flex", alignItems: "center", gap: "8px", margin: "8px 0" }}>
        <span style={{ fontSize: "12px", color: "#9fb4cc" }}>Perfil:</span>
        <select
          value={activeProfile.name}
          onChange={(e) => {
            const found = profiles.find((p) => p.name === e.target.value);
            if (found) setActiveProfile(found);
          }}
          style={{ padding: "6px", borderRadius: "6px", background: "#0f1722", color: "#e3ecf5", border: "1px solid #1f2f45" }}
        >
          {profiles.map((p) => (
            <option key={p.name} value={p.name}>{p.name}</option>
          ))}
        </select>
      </div>
      <div className="tab-bar">
        {[
          ["dashboard", "Dashboard", statusError],
          ["chat", "Chat", null],
          ["hermes", "Hermes", null],
          ["browser", "Browser", null],
          ["manifestator", "Manifestator", null],
          ["hormiguero", "Hormiguero", statusError],
          ["shub", "Shub", null],
          ["logs", "Logs", eventsError],
        ].map(([key, label, errorFlag]) => (
          <button key={key} className={`tab-btn ${activeTab === key ? "active" : ""}`} onClick={() => setActiveTab(key)}>
            {label}
            {errorFlag && <span className="tab-badge-error" title={String(errorFlag)}>•</span>}
          </button>
        ))}
        <div className="bridge-badge" title="Web Bridge DeepSeek/Gemini">
          <span
            className={`status-dot ${bridgeHealth?.ok && bridgeHealth?.playwright && bridgeHealth?.chromium ? "live" : bridgeHealth?.playwright ? "warn" : "error"}`}
          />
          Web Bridge
        </div>
      </div>

      <div className="tab-content">
        {activeTab === "dashboard" && (
          <div className="tentacular-layout">
            <div className="column column-left">
              <HormigueroMapPanel status={status} events={events as EventMessage[]} />
              <MiniMapPanel status={status} />
              <MiniStatusPanel status={status} />
              <SwitchQueuePanel />
              <MadrePanel />
              <SpawnerPanel />
            </div>

            <div className="column column-center">
              <ChatPanel onSend={handleSendChat} events={events as EventMessage[]} profile={activeProfile as any} activeTab={activeTab} bridgeHealth={bridgeHealth as any} />
              <div className="card nested-panels">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <ShortcutsPanel onSend={handleSendChat} />
                  <DeepSeekHelper onSend={handleSendChat} />
                </div>
                <div style={{ marginTop: "10px" }}>
                  <ShubPanel />
                </div>
              </div>
            </div>

            <div className="column column-right">
              <SelfOverviewPanel />
              <EventsTimelinePanel events={events} />
              <HormigueroPanel />
              <HermesPanel />
              <MCPPanel />
              <LogsPanel />
            </div>
          </div>
        )}

        {activeTab === "chat" && (
          <div className="panels chat-tab">
            <div style={{ flex: 2, minWidth: 0 }}>
              <ChatPanel onSend={handleSendChat} events={events as EventMessage[]} profile={activeProfile as any} activeTab={activeTab} bridgeHealth={bridgeHealth as any} />
            </div>
            <div className="column column-right">
              <EventsTimelinePanel events={events} />
              <LogsPanel />
            </div>
          </div>
        )}

        {activeTab === "manifestator" && (
          <div className="panels">
            <ManifestatorPanel status={status} events={events as EventMessage[]} />
            <MiniStatusPanel status={status} />
          </div>
        )}

        {activeTab === "hormiguero" && (
          <div className="panels">
            <HormigueroMapPanel status={status} events={events as EventMessage[]} />
            <HormigueroPanel status={status} events={events as EventMessage[]} />
            {renderPlaceholder("Incidentes activos", <>Incidentes: {status?.hormiguero?.count ?? 0}</>)}
          </div>
        )}

        {activeTab === "hermes" && (
          <div className="panels">
            <HermesPanel />
            {renderPlaceholder("Switch / Hermes", <>Modelo activo: {status?.switch?.last_choice?.engine || status?.switch?.active_model || "n/a"}</>)}
          </div>
        )}

        {activeTab === "browser" && (
          <div className="panels">
            <BrowserPanel />
            <EventsTimelinePanel events={events} />
          </div>
        )}

        {activeTab === "shub" && (
          <div className="panels">
            <ShubPanel />
            {renderPlaceholder("Shub sesiones", <>Sesiones: {status?.shub?.sessions ?? 0}</>)}
          </div>
        )}

        {activeTab === "logs" && (
          <div className="panels">
            <EventsTimelinePanel events={events} />
            <LogsPanel events={events as EventMessage[]} />
          </div>
        )}
      </div>
    </div>
  );
}

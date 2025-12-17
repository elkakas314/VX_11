import { useMemo, useState } from "react";
import type { CanonicalEvent } from "../../types/canonical-events";
import { ChatView } from "../chat/ChatView";
import { DashboardView } from "./DashboardView";

type Props = {
  alerts: CanonicalEvent[];
  correlations: CanonicalEvent[];
  snapshots: CanonicalEvent[];
  decisions: CanonicalEvent[];
  tensions: CanonicalEvent[];
  narratives: CanonicalEvent[];
  isConnected: boolean;
};

type TabId =
  | "dashboard"
  | "chat"
  | "forensics"
  | "decisions"
  | "narrative"
  | "status"
  | "correlations";

type Tab = { id: TabId; label: string; icon: string };

const TABS: Tab[] = [
  { id: "dashboard", label: "Dashboard", icon: "📊" },
  { id: "chat", label: "Chat", icon: "💬" },
  { id: "forensics", label: "Forensic", icon: "📸" },
  { id: "decisions", label: "Decisions", icon: "🧠" },
  { id: "narrative", label: "Narrative", icon: "🎙️" },
  { id: "correlations", label: "Correlations", icon: "🔗" },
  { id: "status", label: "Status", icon: "⚡" },
];

export function TabsView(props: Props) {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");

  const totalEvents = useMemo(() => {
    return (
      props.alerts.length +
      props.correlations.length +
      props.snapshots.length +
      props.decisions.length +
      props.tensions.length +
      props.narratives.length
    );
  }, [
    props.alerts.length,
    props.correlations.length,
    props.snapshots.length,
    props.decisions.length,
    props.tensions.length,
    props.narratives.length,
  ]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-gray-800/60 bg-gradient-to-r from-gray-950 to-gray-900 px-4 py-3 backdrop-blur-sm overflow-x-auto">
        {TABS.map((tab) => {
          const active = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={[
                "shrink-0 rounded-md border px-3 py-1.5 text-xs transition",
                active
                  ? "border-indigo-800/70 bg-indigo-950/40 text-indigo-100"
                  : "border-transparent bg-transparent text-gray-400 hover:bg-gray-900/40 hover:text-gray-200",
              ].join(" ")}
            >
              <span className="mr-1">{tab.icon}</span>
              {tab.label}
            </button>
          );
        })}

        <div className="ml-auto hidden items-center gap-2 text-[11px] text-gray-500 lg:flex">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              props.isConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
            }`}
          />
          <span className="font-mono">{totalEvents} eventos</span>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {activeTab === "dashboard" && (
          <div className="h-full overflow-y-auto p-6">
            <DashboardView {...props} />
          </div>
        )}

        {activeTab === "chat" && <ChatView />}

        {activeTab === "forensics" && (
          <TabShell
            title="Forensic"
            subtitle="Snapshots forenses — el abismo archiva sin prisa."
            items={props.snapshots}
          />
        )}

        {activeTab === "decisions" && (
          <TabShell
            title="Decisions"
            subtitle="Madre explica; Operator registra."
            items={props.decisions}
          />
        )}

        {activeTab === "narrative" && (
          <TabShell
            title="Narrative"
            subtitle="Shub narra; Operator escucha."
            items={props.narratives}
          />
        )}

        {activeTab === "correlations" && (
          <TabShell
            title="Correlations"
            subtitle="El grafo late cuando hay señales."
            items={props.correlations}
          />
        )}

        {activeTab === "status" && (
          <div className="h-full overflow-y-auto p-6">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <StatCard
                label="Conexión Backend"
                value={props.isConnected ? "Conectado" : "Desconectado"}
                color={props.isConnected ? "emerald" : "amber"}
              />
              <StatCard label="Eventos Totales" value={String(totalEvents)} color="indigo" />
              <StatCard label="VX11" value="Operator" color="pink" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function TabShell({ title, subtitle, items }: { title: string; subtitle: string; items: CanonicalEvent[] }) {
  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-4">
        <div className="text-sm font-semibold text-gray-100 tracking-wide">{title}</div>
        <div className="mt-1 text-xs text-gray-500">{subtitle}</div>
      </div>
      <div className="rounded-lg border border-gray-800/60 bg-gradient-to-b from-gray-900/40 to-gray-950/40 p-4 min-h-[16rem]">
        {items.length === 0 ? (
          <div className="h-full flex items-center justify-center text-center">
            <div className="text-gray-700">
              <div className="text-3xl opacity-20 mb-2 animate-pulse">◇◆◇</div>
              <p className="text-xs text-gray-600">Los tentáculos aguardan señales…</p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {items.slice(0, 24).map((evt, i) => (
              <div
                key={i}
                className="rounded border border-gray-800/60 bg-gray-900/30 px-3 py-2 text-xs text-gray-300"
              >
                <div className="text-[10px] text-gray-500 font-mono">
                  {(evt as any)?.type ?? "unknown"}
                </div>
                <div className="mt-1 text-gray-400 line-clamp-2">
                  {safeJsonPreview(evt)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "emerald" | "amber" | "indigo" | "pink";
}) {
  const colorMap: Record<typeof color, string> = {
    emerald: "text-emerald-400 border-emerald-900/50",
    amber: "text-amber-400 border-amber-900/50",
    indigo: "text-indigo-400 border-indigo-900/50",
    pink: "text-pink-400 border-pink-900/50",
  };

  return (
    <div className={`rounded-lg border ${colorMap[color]} bg-gray-900/40 p-4`}>
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`mt-2 text-lg font-semibold ${colorMap[color].split(" ")[0]}`}>
        {value}
      </div>
    </div>
  );
}

function safeJsonPreview(value: unknown): string {
  try {
    const s = JSON.stringify(value);
    return s.length > 200 ? `${s.slice(0, 200)}…` : s;
  } catch {
    return "{\"type\":\"unknown\"}";
  }
}


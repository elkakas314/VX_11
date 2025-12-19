import React from "react";

type Props = {
  connected: boolean;
  modules: Record<string, any>;
};

export function StatusBar({ connected, modules }: Props) {
  const okCount = Object.values(modules || {}).filter((m: any) => m.status === "ok" || m.ok).length;
  const total = Object.keys(modules || {}).length;
  return (
    <header className="statusbar">
      <div>Operator ▸ Tentáculo Link {connected ? "🟢" : "⚪"}</div>
      <div>
        Health: {okCount}/{total}
      </div>
    </header>
  );
}

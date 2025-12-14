import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

const bootHTML = `
  <div style="
    position: fixed;
    inset: 0;
    background: linear-gradient(135deg, #030712 0%, #0a0e14 100%);
    color: #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: system-ui, -apple-system, sans-serif;
    z-index: 9999;
  ">
    <div style="text-align:center;padding:16px;max-width:640px;">
      <div style="font-size:28px;margin-bottom:8px;color:#8b5cf6;">◆</div>
      <div style="font-size:18px;margin-bottom:6px;">VX11 Operator booting…</div>
      <div style="font-size:12px;opacity:.7;">El abismo observa</div>
    </div>
  </div>
`;

function ensureRootElement(): HTMLElement {
  const existing = document.getElementById("root");
  if (existing instanceof HTMLElement) return existing;
  const created = document.createElement("div");
  created.id = "root";
  created.style.width = "100%";
  created.style.height = "100%";
  document.body.appendChild(created);
  return created;
}

function renderFatal(error: unknown): void {
  const root = ensureRootElement();
  const stack =
    error instanceof Error ? error.stack || error.message : String(error);
  const details = (import.meta as any).env?.DEV ? stack : "Inicialización fallida";
  root.innerHTML = `
    <div style="
      position: fixed;
      inset: 0;
      background: #030712;
      color: #fca5a5;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      z-index: 9999;
      padding: 24px;
    ">
      <div style="max-width: 860px; width: 100%;">
        <div style="font-size: 14px; color: #e5e7eb; margin-bottom: 10px;">◇ VX11 Operator</div>
        <div style="font-size: 12px; opacity: .8; margin-bottom: 12px;">El render no puede caer en blanco.</div>
        <pre style="white-space: pre-wrap; background: #0b1220; border: 1px solid rgba(148,163,184,.2); padding: 12px; border-radius: 10px; color: #fecaca; overflow:auto; max-height: 55vh;">${escapeHTML(
          details,
        )}</pre>
      </div>
    </div>
  `;
}

function escapeHTML(value: string): string {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

const rootElement = ensureRootElement();
rootElement.innerHTML = bootHTML;

try {
  createRoot(rootElement).render(<App />);
} catch (error) {
  renderFatal(error);
}

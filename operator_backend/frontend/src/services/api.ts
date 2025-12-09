import { OPERATOR_BASE_URL, TOKEN_HEADER, TOKEN_VALUE, LINK_BASE_URL } from "../config";

const API_BASE = OPERATOR_BASE_URL;
const AUTH_HEADERS: HeadersInit = { [TOKEN_HEADER]: TOKEN_VALUE };

export async function fetchSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/operator/system/status`, { headers: AUTH_HEADERS });
    return res.json();
  } catch (e) {
    return { error: "system_unavailable" };
  }
}

export async function validateManifest(content: string) {
  const res = await fetch(`${API_BASE}/manifest/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...AUTH_HEADERS },
    body: JSON.stringify({ manifest: content }),
  });
  return res.json();
}

export async function fetchJSON(path: string, opts: RequestInit = {}) {
  const headers = { ...(opts.headers || {}), ...AUTH_HEADERS } as HeadersInit;
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  return res.json();
}

export function wsConnect(onMessage: (ev: MessageEvent) => void, onOpen?: () => void, onClose?: () => void) {
  const url = API_BASE.replace(/^http/, "ws");
  const socket = new WebSocket(`${url}/ws`);
  socket.onopen = onOpen || null;
  socket.onmessage = onMessage;
  socket.onclose = onClose || null;
  return socket;
}

// Madre - Orchestration Plans
export async function fetchMadrePlans() {
  return fetchJSON("/operator/madre/plans");
}

export async function fetchMadrePlan(id: string) {
  return fetchJSON(`/operator/madre/plans/${id}`);
}

export async function createMadrePlan(payload: any) {
  return fetchJSON("/operator/madre/plans", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// Spawner - Hijas Management
export async function fetchSpawns() {
  return fetchJSON("/operator/spawner/spawns");
}

export async function fetchSpawn(id: string) {
  return fetchJSON(`/operator/spawner/spawns/${id}`);
}

export async function killSpawn(id: string) {
  return fetchJSON(`/operator/spawner/spawns/${id}/kill`, { method: "POST" });
}

// Switch - Queue Management
export async function fetchSwitchQueue() {
  return fetchJSON("/operator/switch/queue");
}

export async function setSwitchDefaultModel(model: string) {
  return fetchJSON("/operator/switch/models/default", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model }),
  });
}

export async function preloadModel(model: string) {
  return fetchJSON("/operator/switch/models/preload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model }),
  });
}

export async function fetchSwitchModels() {
  return fetchJSON("/operator/switch/models");
}

// Hermes - Model Registry
export async function fetchHermesModels() {
  return fetchJSON("/operator/hermes/models");
}

export async function fetchHermesCLI() {
  return fetchJSON("/operator/hermes/cli");
}

// MCP - Sandbox Audit
export async function fetchMCPAuditLogs() {
  return fetchJSON("/operator/mcp/audit");
}

export async function fetchMCPSandboxExec() {
  return fetchJSON("/operator/mcp/sandbox");
}

export async function fetchMCPViolations() {
  return fetchJSON("/operator/mcp/violations");
}

// Hormiguero - Queen Tasks
export async function fetchHormigueroQueenTasks() {
  return fetchJSON("/operator/hormiguero/queen_tasks");
}

export async function fetchHormigueroEvents() {
  return fetchJSON("/operator/hormiguero/events");
}

// UI helpers
export async function fetchUiEvents() {
  const res = await fetch(`${API_BASE}/ui/events`, { headers: AUTH_HEADERS });
  return res.json();
}

export async function fetchLinkStatus() {
  const res = await fetch(`${LINK_BASE_URL}/vx11/health-aggregate`, { headers: AUTH_HEADERS });
  return res.json();
}

export async function sendChat(message: string, mode: string, metadata: Record<string, any> = {}) {
  const body = { message, provider_hint: mode, metadata };
  try {
    const res = await fetch(`${API_BASE}/operator/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...AUTH_HEADERS },
      body: JSON.stringify(body),
    });
    return res.json();
  } catch (e) {
    return { error: "chat_unreachable" };
  }
}

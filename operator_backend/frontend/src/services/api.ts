import { OPERATOR_BASE_URL, TOKEN_HEADER, TOKEN_VALUE, LINK_BASE_URL, WS_BASE_URL } from "../config";

const API_BASE = OPERATOR_BASE_URL;
const CHAT_ENDPOINT = `${OPERATOR_BASE_URL}/operator/chat`;
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
  return fetchJSON("/operator/manifestator/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

export async function fetchJSON(path: string, opts: RequestInit = {}) {
  const headers = { ...(opts.headers || {}), ...AUTH_HEADERS } as HeadersInit;
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  const data = await res.json();
  if (!res.ok) {
    return { ok: false, status: res.status, error: data?.error || data?.message || "request_failed" };
  }
  return data;
}

export function wsConnect(onMessage: (ev: MessageEvent) => void, onOpen?: () => void, onClose?: () => void) {
  const socket = new WebSocket(WS_BASE_URL || API_BASE.replace(/^http/, "ws") + "/ws");
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

// CLI Hub
export async function fetchCliProviders() {
  return fetchJSON("/operator/cli/providers");
}

export async function testCliProvider(providerId: string, sample?: string) {
  return fetchJSON("/operator/cli/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider_id: providerId, sample }),
  });
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

export async function postIntent(payload: any) {
  return fetchJSON("/operator/intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchLinkStatus() {
  const res = await fetch(`${LINK_BASE_URL}/vx11/health-aggregate`, { headers: AUTH_HEADERS });
  return res.json();
}

export async function sendChat(message: string, mode: string, metadata: Record<string, any> = {}) {
  const body = {
    session_id: metadata.session_id,
    message,
    metadata: { provider_hint: mode, ...metadata },
  };
  try {
    const res = await fetch(CHAT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...AUTH_HEADERS },
      body: JSON.stringify(body),
    });
    return res.json();
  } catch (e) {
    return { error: "chat_unreachable" };
  }
}

// Browser Agent
export async function createBrowserTask(url: string) {
  return fetchJSON("/operator/browser/task", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
}

export async function fetchBrowserTask(taskId: string) {
  return fetchJSON(`/operator/browser/task/${taskId}`);
}

export async function fetchSession(sessionId: string) {
  return fetchJSON(`/operator/session/${sessionId}`);
}

export async function sendSwitchFeedback(engine: string, success: boolean, latency_ms?: number, tokens_used?: number, error_msg?: string) {
  return fetchJSON("/operator/switch/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      engine,
      success,
      latency_ms: latency_ms ?? 0,
      tokens_used: tokens_used ?? 0,
      error_msg: error_msg || (success ? undefined : "user_marked_as_not_useful"),
    }),
  });
}
// ============ PHASE 6: INTEGRATION APIs ============

export async function patchPlan(content: string) {
  return fetchJSON("/operator/manifestator/patchplan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

export async function applyPatch(content: string, patches: any[]) {
  return fetchJSON("/operator/manifestator/apply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, patches }),
  });
}

export async function scanHormiguero() {
  return fetchJSON("/operator/hormiguero/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function cleanHormiguero() {
  return fetchJSON("/operator/hormiguero/clean", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function requestPlan(intent: string, metadata?: Record<string, any>) {
  return fetchJSON("/operator/madre/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intent, metadata: metadata || {} }),
  });
}

export async function executePlan(planId: string) {
  return fetchJSON("/operator/madre/plan/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan_id: planId }),
  });
}

export async function runSpawner(task: string, metadata?: Record<string, any>) {
  return fetchJSON("/operator/spawner/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task, metadata: metadata || {} }),
  });
}

export async function fetchSelfOverview() {
  return fetchJSON("/operator/self/overview");
}

export async function callDeepseekWeb(prompt: string) {
  return fetchJSON("/operator/bridge/deepseek_web", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
}

export async function callGeminiWeb(prompt: string) {
  return fetchJSON("/operator/bridge/gemini_web", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
}

export async function shubControl(action: string, target?: string) {
  return fetchJSON("/operator/shub/control", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, target }),
  });
}

export async function fetchBridgeHealth() {
  return fetchJSON("/operator/bridge/health");
}

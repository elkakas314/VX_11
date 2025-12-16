import type { ChatMessage, ChatRole } from "../types/chat";

export type ChatApiStatus =
  | { kind: "connected"; url: string }
  | { kind: "unauthorized"; url?: string; message: string }
  | { kind: "not_found" }
  | { kind: "unavailable"; message: string };

const DEFAULT_CHAT_URL = "http://localhost:8000/chat";

function envString(key: string): string | undefined {
  const value = (import.meta as any).env?.[key];
  return typeof value === "string" && value.trim().length ? value.trim() : undefined;
}

function buildCandidates(): string[] {
  const fromEnv = envString("VITE_VX11_CHAT_URL");
  if (fromEnv) return [fromEnv];

  const base = DEFAULT_CHAT_URL.replace(/\/chat\/?$/, "");
  return [`${base}/chat`, `${base}/operator/chat`, `${base}/v1/chat`];
}

function tokenHeader(): Record<string, string> {
  const token = envString("VITE_VX11_TOKEN");
  return token ? { "X-VX11-Token": token } : {};
}

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    globalThis.clearTimeout(timeoutId);
  }
}

export async function probeChatApi(): Promise<ChatApiStatus> {
  const candidates = buildCandidates();
  for (const url of candidates) {
    try {
      const res = await fetchWithTimeout(
        url,
        { method: "OPTIONS", headers: { ...tokenHeader() } },
        1500,
      );
      if (res.ok) return { kind: "connected", url };
      if (res.status === 401) {
        return { kind: "unauthorized", url, message: "Token inválido o faltante" };
      }
      if (res.status === 404) continue;
    } catch (e) {
      const message = e instanceof Error ? e.message : "No disponible";
      return { kind: "unavailable", message };
    }
  }
  return { kind: "not_found" };
}

export async function sendChat(
  apiUrl: string,
  messages: Array<{ role: ChatRole; content: string }>,
): Promise<string> {
  const res = await fetchWithTimeout(
    apiUrl,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...tokenHeader(),
      },
      body: JSON.stringify({ messages }),
    },
    12000,
  );

  if (res.status === 401) {
    throw new Error("Unauthorized: token inválido o faltante");
  }
  if (res.status === 404) {
    throw new Error("Chat endpoint not found");
  }
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  const data: unknown = await res.json().catch(() => ({}));
  const payload = data as Record<string, unknown>;
  const text =
    (typeof payload.response === "string" && payload.response) ||
    (typeof payload.message === "string" && payload.message);
  if (text) return text;

  const lastAssistant = [...messages]
    .reverse()
    .find((m) => m.role === "assistant")?.content;
  return lastAssistant ?? "…";
}

export function toChatPayload(messages: ChatMessage[]): Array<{
  role: ChatRole;
  content: string;
}> {
  return messages.map((m) => ({ role: m.role, content: m.content }));
}

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { probeChatApi, sendChat, toChatPayload, type ChatApiStatus } from "../../services/chat-api";
import type { ChatMessage } from "../../types/chat";

export type ChatMode = "backend" | "local";

export type UseChatReturn = {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  mode: ChatMode;
  backendStatus: ChatApiStatus;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
};

const STORAGE_KEY = "vx11_chat_messages";

function nowId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function safeLoadMessages(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((m) => m && typeof m === "object")
      .map((m) => m as ChatMessage)
      .filter(
        (m) =>
          (m.role === "user" || m.role === "assistant") &&
          typeof m.content === "string",
      )
      .slice(-200);
  } catch {
    return [];
  }
}

function safePersistMessages(messages: ChatMessage[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-200)));
  } catch {
    // ignore
  }
}

function localResponse(input: string): string {
  const trimmed = input.trim();
  if (!trimmed) return "…";
  const head = trimmed.length > 240 ? `${trimmed.slice(0, 240)}…` : trimmed;
  return [
    "◇ Modo local (sin backend)",
    "",
    "El Operator escucha y refleja:",
    "",
    head,
    "",
    "Configura `VITE_VX11_CHAT_URL` y `VITE_VX11_TOKEN` para hablar con el corazón.",
  ].join("\n");
}

async function typeInto(
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>,
  messageId: string,
  fullText: string,
) {
  const stepMs = 12;
  const chunk = 3;
  let index = 0;

  return await new Promise<void>((resolve) => {
    const timer = globalThis.setInterval(() => {
      index = Math.min(fullText.length, index + chunk);
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, content: fullText.slice(0, index) } : m)),
      );
      if (index >= fullText.length) {
        globalThis.clearInterval(timer);
        resolve();
      }
    }, stepMs);
  });
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>(() => safeLoadMessages());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<ChatApiStatus>({ kind: "unavailable", message: "…" });
  const activeApiUrlRef = useRef<string | null>(null);

  useEffect(() => {
    safePersistMessages(messages);
  }, [messages]);

  useEffect(() => {
    let cancelled = false;
    probeChatApi()
      .then((status) => {
        if (cancelled) return;
        setBackendStatus(status);
        activeApiUrlRef.current = status.kind === "connected" ? status.url : null;
      })
      .catch(() => {
        if (cancelled) return;
        setBackendStatus({ kind: "unavailable", message: "No disponible" });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const mode: ChatMode = useMemo(() => {
    return backendStatus.kind === "connected" ? "backend" : "local";
  }, [backendStatus.kind]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    safePersistMessages([]);
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || isLoading) return;

      setIsLoading(true);
      setError(null);

      const userMessage: ChatMessage = {
        id: nowId("user"),
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMessage]);

      const assistantId = nowId("assistant");
      const assistantShell: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantShell]);

      try {
        let responseText: string;
        const apiUrl = activeApiUrlRef.current;

        if (apiUrl) {
          responseText = await sendChat(apiUrl, toChatPayload([...messages, userMessage]));
        } else {
          responseText = localResponse(trimmed);
        }

        await typeInto(setMessages, assistantId, responseText);
      } catch (e) {
        const message = e instanceof Error ? e.message : "Error desconocido";
        setError(message);
        const fallback = localResponse(trimmed);
        await typeInto(setMessages, assistantId, `◇ ${message}\n\n${fallback}`);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, messages],
  );

  return {
    messages,
    isLoading,
    error,
    mode,
    backendStatus,
    sendMessage,
    clearMessages,
  };
}

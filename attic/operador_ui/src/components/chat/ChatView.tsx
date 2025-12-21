import { useEffect, useRef, useState } from "react";
import { useChat } from "../../hooks/useChat";

export function ChatView() {
  const { messages, isLoading, error, sendMessage, mode } = useChat();
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  const isBackend = mode === "backend";

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-800/60 bg-gradient-to-r from-gray-950 to-gray-900 px-6 py-4 backdrop-blur-sm">
        <div>
          <div className="text-sm font-semibold text-gray-100 tracking-wide">
            💬 Chat VX11
          </div>
          <div className="mt-1 text-xs text-gray-500">
            {isBackend ? (
              <span className="text-emerald-400">◆ Backend conectado</span>
            ) : (
              <span className="text-amber-400">○ Modo local (sin backend)</span>
            )}
          </div>
        </div>
        <div className="text-xs text-gray-500">Operator no actúa; observa.</div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center">
            <div className="max-w-md rounded-xl border border-gray-800/60 bg-gradient-to-b from-gray-900/50 to-gray-950 px-6 py-8">
              <div className="text-3xl text-indigo-300/50">◆</div>
              <div className="mt-3 text-sm font-semibold text-gray-200">
                El abismo escucha
              </div>
              <div className="mt-2 text-xs text-gray-500">
                {isBackend
                  ? "Escribe para enviar; Enter envía, Shift+Enter agrega línea."
                  : "Backend apagado: el chat opera en modo local y persiste en este navegador."}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[44rem] whitespace-pre-wrap break-words rounded-lg border px-4 py-3 text-sm leading-relaxed shadow-sm ${
                    msg.role === "user"
                      ? "border-indigo-800/60 bg-indigo-950/40 text-indigo-100"
                      : "border-gray-800/60 bg-gray-900/40 text-gray-100"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="rounded-lg border border-gray-800/60 bg-gray-900/40 px-4 py-3 text-sm text-gray-300">
                  <span className="inline-flex gap-1">
                    <span className="animate-pulse">●</span>
                    <span className="animate-pulse [animation-delay:120ms]">
                      ●
                    </span>
                    <span className="animate-pulse [animation-delay:240ms]">
                      ●
                    </span>
                  </span>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
        )}
      </div>

      {error && (
        <div className="mx-6 mb-3 rounded border border-red-900/60 bg-red-950/30 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      <div className="border-t border-gray-800/60 bg-gradient-to-r from-gray-950 to-gray-900 px-6 py-4">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={
            isBackend
              ? "Escribe… (Enter envía, Shift+Enter salto)"
              : "Escribe… (modo local, Enter envía)"
          }
          className="w-full resize-none rounded-lg border border-gray-800/70 bg-gray-900/40 px-4 py-3 text-sm text-gray-100 placeholder:text-gray-600 focus:border-indigo-700/70 focus:outline-none focus:ring-2 focus:ring-indigo-500/10 disabled:opacity-60"
          rows={2}
          disabled={isLoading}
          onKeyDown={async (e) => {
            if (e.key !== "Enter" || e.shiftKey) return;
            e.preventDefault();
            const toSend = draft.trim();
            if (!toSend) return;
            setDraft("");
            await sendMessage(toSend);
          }}
        />
        <div className="mt-2 text-[11px] text-gray-500">
          {isBackend
            ? "Conectado: el corazón responde si el endpoint existe."
            : "Fallback local activo: no depende del backend."}
        </div>
      </div>
    </div>
  );
}


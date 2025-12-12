import React, { useEffect, useState } from "react";
import { callDeepseekWeb, callGeminiWeb, fetchBridgeHealth, fetchBrowserTask } from "../services/api";
import type { BridgeHealth } from "../types/api";

type Props = {
  defaultProvider?: "deepseek" | "gemini";
};

export function BridgePanel({ defaultProvider = "deepseek" }: Props) {
  const [provider, setProvider] = useState<"deepseek" | "gemini">(defaultProvider);
  const [prompt, setPrompt] = useState("");
  const [health, setHealth] = useState<BridgeHealth | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [taskId, setTaskId] = useState<string | null>(null);

  useEffect(() => {
    fetchBridgeHealth().then(setHealth).catch(() => setHealth({ ok: false }));
  }, []);

  useEffect(() => {
    if (!taskId) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const res = await fetchBrowserTask(taskId);
        if (cancelled) return;
        setResult(res);
        if (res?.status && res.status !== "completed" && res.status !== "error") {
          setTimeout(poll, 1500);
        }
      } catch {
        /* ignore */
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [taskId]);

  const send = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setResult(null);
    setTaskId(null);
    try {
      const resp = provider === "deepseek" ? await callDeepseekWeb(prompt) : await callGeminiWeb(prompt);
      setResult(resp);
      if (resp?.task_id) {
        setTaskId(resp.task_id);
      }
    } catch (e: any) {
      setResult({ ok: false, error: e?.message || "bridge error" });
    } finally {
      setLoading(false);
    }
  };

  const disabled = !health?.ok || loading || !prompt.trim();

  return (
    <div className="card">
      <div className="card-header" style={{ justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>Bridge DeepSeek/Gemini</h3>
        <div style={{ color: health?.ok ? "#22c55e" : "#ef4444", fontSize: 12 }}>
          Health: {health?.ok ? "OK" : "OFF"}
          {health?.error ? ` · ${health.error}` : ""}
        </div>
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
        <select value={provider} onChange={(e) => setProvider(e.target.value as any)} style={{ padding: 6, borderRadius: 8 }}>
          <option value="deepseek">DeepSeek Web</option>
          <option value="gemini">Gemini Web</option>
        </select>
        <button className="chip" onClick={send} disabled={disabled}>
          {loading ? "Enviando..." : "Generar"}
        </button>
      </div>
      <textarea
        rows={3}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Escribe el prompt para el puente web…"
        style={{ width: "100%", borderRadius: 10, padding: 10, border: "1px solid #1f2f45", background: "#0f172a", color: "#e5e7eb" }}
      />
      {result && (
        <div style={{ marginTop: 10, fontSize: 12, color: result.ok ? "#cbd5e1" : "#fca5a5", border: "1px solid #1f2f45", borderRadius: 10, padding: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <strong style={{ color: "#e5e7eb" }}>{result.provider || provider}</strong>
            <span>{result.duration_ms ? `${result.duration_ms} ms` : ""}</span>
          </div>
          <div>{result.text || result.error || result.status}</div>
        </div>
      )}
    </div>
  );
}

import React, { Suspense, useCallback, useMemo, useState } from "react";
import { validateManifest, patchPlan, applyPatch } from "../../services/api";
import type { ManifestValidationResult, PatchPlanResult } from "../../types/api";

const MonacoEditor = React.lazy(() => import("@monaco-editor/react"));

type Props = {
  defaultValue?: string;
};

export function ManifestEditor({ defaultValue = "" }: Props) {
  const [content, setContent] = useState(defaultValue);
  const [loading, setLoading] = useState<"validate" | "patch" | "apply" | null>(null);
  const [result, setResult] = useState<ManifestValidationResult | PatchPlanResult | null>(null);

  const onValidate = useCallback(async () => {
    setLoading("validate");
    try {
      const res = await validateManifest(content);
      setResult(res);
    } catch (e: any) {
      setResult({ ok: false, errors: [e?.message || "Error en validación"] });
    } finally {
      setLoading(null);
    }
  }, [content]);

  const onPatch = useCallback(async () => {
    setLoading("patch");
    try {
      const res = await patchPlan(content);
      setResult(res);
    } catch (e: any) {
      setResult({ ok: false, error: e?.message || "Error en patch plan" });
    } finally {
      setLoading(null);
    }
  }, [content]);

  const onApply = useCallback(async () => {
    setLoading("apply");
    try {
      const patches = (result as any)?.data || [];
      const res = await applyPatch(content, patches);
      setResult(res);
    } catch (e: any) {
      setResult({ ok: false, error: e?.message || "Error aplicando patch" });
    } finally {
      setLoading(null);
    }
  }, [content, result]);

  const markers = useMemo(() => {
    const errors = (result as ManifestValidationResult)?.errors || [];
    return errors.map((err, idx) => ({
      severity: 8,
      message: err,
      startLineNumber: idx + 1,
      startColumn: 1,
      endLineNumber: idx + 1,
      endColumn: 80,
    }));
  }, [result]);

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
        <button className="chip" disabled={loading !== null} onClick={onValidate}>
          {loading === "validate" ? "Validando..." : "Validate"}
        </button>
        <button className="chip" disabled={loading !== null} onClick={onPatch}>
          {loading === "patch" ? "Generando patch..." : "Patch plan"}
        </button>
        <button className="chip" disabled={loading !== null || !(result as any)?.data} onClick={onApply}>
          {loading === "apply" ? "Aplicando..." : "Apply plan"}
        </button>
      </div>
      <Suspense fallback={<div style={{ color: "#9fb4cc", fontSize: 12 }}>Cargando editor...</div>}>
        <MonacoEditor
          height="280px"
          defaultLanguage="yaml"
          value={content}
          onChange={(val) => setContent(val || "")}
          theme="vs-dark"
          options={{ fontSize: 13, minimap: { enabled: false } }}
          onValidate={(ms) => {
            // fallback markers if backend not used
            if (!markers.length && ms.length) {
              setResult({ ok: ms.length === 0, errors: ms.map((m) => m.message) });
            }
          }}
        />
      </Suspense>
      {result && (
        <div style={{ marginTop: 8, padding: 8, border: "1px solid #1f2f45", borderRadius: 8, background: result.ok ? "#102821" : "#2a1a1a" }}>
          <div style={{ color: result.ok ? "#22c55e" : "#ef4444", fontWeight: 700 }}>{result.ok ? "Valid manifest" : "Errors found"}</div>
          {result.summary && <div style={{ color: "#9fb4cc" }}>{result.summary}</div>}
          {(result as ManifestValidationResult).errors?.length ? (
            <ul style={{ color: "#ef4444", fontSize: 12 }}>
              {(result as ManifestValidationResult).errors?.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          ) : null}
          {Array.isArray((result as PatchPlanResult).data) && (result as PatchPlanResult).data?.length ? (
            <div style={{ color: "#e5e7eb", fontSize: 12, marginTop: 6 }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>Patch plan</div>
              <ul>
                {(result as PatchPlanResult).data?.slice(0, 8).map((p: any, idx: number) => (
                  <li key={idx}>{p?.summary || p?.action || JSON.stringify(p).slice(0, 80)}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

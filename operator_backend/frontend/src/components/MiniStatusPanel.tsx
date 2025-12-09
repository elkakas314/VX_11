import React from "react";

type Props = {
  status: any;
};

export function MiniStatusPanel({ status }: Props) {
  const modules = status?.modules || {};
  const feromonas = modules?.hormiguero?.status?.feromonas || {};
  const mutationInterval = modules?.hormiguero?.status?.mutation_interval;
  const score = status?.modules?.switch?.status?.scoring;
  const error = status?.error;

  return (
    <div className="card">
      <div className="card-header">
        <h3>Estado VX11</h3>
      </div>
      <div className="card-body">
        {error && <div style={{ color: "red" }}>Sistema no disponible</div>}
        <div>Versión: {status?.version || "N/A"}</div>
        <div>Feromonas: {JSON.stringify(feromonas)}</div>
        <div>Mutation interval: {mutationInterval ?? "N/A"}s</div>
        <div>Chat score: {score ? JSON.stringify(score) : "N/A"}</div>
      </div>
    </div>
  );
}

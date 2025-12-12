export const statusColor = (state?: string) => {
  const normalized = (state || "").toLowerCase();
  if (normalized === "ok" || normalized === "healthy") return "#22c55e";
  if (normalized === "degraded" || normalized === "warn" || normalized === "warning") return "#f59e0b";
  if (normalized === "down" || normalized === "error") return "#ef4444";
  return "#6b7280";
};

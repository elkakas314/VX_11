/**
 * Incidents Table Panel
 * Displays filterable list of incidents with action buttons
 */

import React, { useState } from "react";
import { Incident, SeverityLevel, IncidentStatus } from "../../types/hormiguero";

interface IncidentsTableProps {
  incidents: Incident[];
  selected_id?: number | null;
  onSelect?: (id: number) => void;
  onDispatch?: (id: number) => void;
  is_loading?: boolean;
}

export const IncidentsTable: React.FC<IncidentsTableProps> = ({
  incidents,
  selected_id,
  onSelect,
  onDispatch,
  is_loading,
}) => {
  const [filter_severity, setFilterSeverity] = useState<SeverityLevel | "all">("all");
  const [filter_status, setFilterStatus] = useState<IncidentStatus | "all">("all");

  const filtered = incidents.filter((inc) => {
    if (filter_severity !== "all" && inc.severity !== filter_severity) return false;
    if (filter_status !== "all" && inc.status !== filter_status) return false;
    return true;
  });

  const severityColors = {
    info: "text-gray-600",
    warning: "text-yellow-600",
    error: "text-orange-600",
    critical: "text-red-600",
  };

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold">Incidents ({filtered.length})</h3>
        <div className="flex gap-2">
          <select
            value={filter_severity}
            onChange={(e) => setFilterSeverity(e.target.value as any)}
            className="px-2 py-1 border rounded text-sm"
          >
            <option value="all">All Severity</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
            <option value="critical">Critical</option>
          </select>
          <select
            value={filter_status}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="px-2 py-1 border rounded text-sm"
          >
            <option value="all">All Status</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      {is_loading && <div className="text-center py-4 text-gray-500">Loading...</div>}

      {!is_loading && filtered.length === 0 && (
        <div className="text-center py-4 text-gray-500">No incidents</div>
      )}

      {!is_loading && filtered.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="px-3 py-2 text-left">ID</th>
                <th className="px-3 py-2 text-left">Type</th>
                <th className="px-3 py-2 text-left">Severity</th>
                <th className="px-3 py-2 text-left">Location</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-left">Detected</th>
                <th className="px-3 py-2 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((inc) => (
                <tr
                  key={inc.id}
                  className={`border-b cursor-pointer hover:bg-blue-50 ${
                    selected_id === inc.id ? "bg-blue-100" : ""
                  }`}
                  onClick={() => onSelect?.(inc.id)}
                >
                  <td className="px-3 py-2 font-mono text-xs">{inc.id}</td>
                  <td className="px-3 py-2">{inc.incident_type}</td>
                  <td className={`px-3 py-2 font-bold ${severityColors[inc.severity]}`}>
                    {inc.severity.toUpperCase()}
                  </td>
                  <td className="px-3 py-2 text-gray-600">{inc.location}</td>
                  <td className="px-3 py-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        inc.status === "open"
                          ? "bg-red-100 text-red-700"
                          : inc.status === "acknowledged"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-green-100 text-green-700"
                      }`}
                    >
                      {inc.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-500">
                    {new Date(inc.detected_at).toLocaleTimeString()}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {inc.status === "open" && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDispatch?.(inc.id);
                        }}
                        className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
                        disabled={is_loading}
                      >
                        Decide
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

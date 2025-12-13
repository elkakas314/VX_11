/**
 * Ants Panel
 * Shows all ants with their current status, CPU/RAM usage, last scan time
 */

import React from "react";
import { Ant, AntRole, AntStatus } from "../../types/hormiguero";

interface AntsListProps {
  ants: Ant[];
  selected_id?: string | null;
  onSelect?: (id: string) => void;
}

export const AntsList: React.FC<AntsListProps> = ({ ants, selected_id, onSelect }) => {
  const statusIcon = {
    idle: "⏸️",
    scanning: "🔍",
    reporting: "📢",
  };

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <h3 className="text-lg font-bold mb-4">Ants ({ants.length})</h3>

      {ants.length === 0 && <div className="text-gray-500 text-sm">No ants active</div>}

      {ants.length > 0 && (
        <div className="space-y-2">
          {ants.map((ant) => (
            <div
              key={ant.id}
              onClick={() => onSelect?.(ant.id)}
              className={`p-3 border rounded cursor-pointer hover:bg-blue-50 ${
                selected_id === ant.id ? "bg-blue-100 border-blue-500" : "border-gray-200"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-semibold text-sm flex items-center gap-2">
                    {statusIcon[ant.status as keyof typeof statusIcon]}
                    {ant.role.replace("scanner_", "").toUpperCase()}
                  </div>
                  <div className="text-xs text-gray-600 font-mono mt-1">{ant.id}</div>
                </div>
                <div className="text-right text-xs">
                  <div className="font-mono">
                    {ant.cpu_percent.toFixed(1)}% CPU
                    <br />
                    {ant.ram_percent.toFixed(1)}% RAM
                  </div>
                </div>
              </div>

              {ant.last_scan_at && (
                <div className="text-xs text-gray-500 mt-2">
                  Last scan: {new Date(ant.last_scan_at).toLocaleTimeString()}
                </div>
              )}

              <div className="mt-2 flex items-center gap-2">
                <span
                  className={`px-2 py-1 rounded text-xs font-semibold ${
                    ant.status === "scanning"
                      ? "bg-yellow-100 text-yellow-700"
                      : ant.status === "reporting"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-700"
                  }`}
                >
                  {ant.status}
                </span>
                <span className="text-xs text-gray-500">
                  Mutation level: {ant.mutation_level}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

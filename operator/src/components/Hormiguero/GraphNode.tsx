/**
 * Graph Node Component (Queen or Ant)
 * Used in React Flow canvas for Hormiguero visualization
 */

import React from "react";
import { Handle, Position } from "reactflow";
import { Ant, AntRole, AntStatus } from "../../types/hormiguero";

interface GraphNodeProps {
  data: {
    label: string;
    entity?: Ant;
    role?: AntRole;
    status?: AntStatus;
    incident_count?: number;
  };
}

export const GraphNodeComponent: React.FC<GraphNodeProps> = ({ data }) => {
  const isQueen = data.role === AntRole.SCANNER_DRIFT || data.label.includes("Queen");
  const statusColor =
    data.status === AntStatus.SCANNING
      ? "border-yellow-400"
      : data.status === AntStatus.REPORTING
        ? "border-blue-400"
        : "border-gray-400";

  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 ${statusColor} bg-white shadow-md text-center min-w-[120px]`}
    >
      <Handle type="target" position={Position.Top} />

      {isQueen && <div className="text-lg font-bold text-red-600">👑 REINA</div>}
      {!isQueen && <div className="text-sm font-semibold text-blue-600">🐜 {data.label}</div>}

      {data.entity && (
        <>
          <div className="text-xs text-gray-600 mt-1">
            {data.entity.cpu_percent.toFixed(1)}% CPU
          </div>
          {data.incident_count !== undefined && (
            <div className="text-xs font-bold text-red-500 mt-1">
              {data.incident_count} incident(s)
            </div>
          )}
        </>
      )}

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

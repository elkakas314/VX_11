/**
 * Main Hormiguero Dashboard
 * Integrates Graph, Incidents, and Ants panels with real-time updates
 * Reference: docs/VX11_HORMIGUERO_v7_COMPLETION.md
 */
 
/** @jsxRuntime classic */
import React from "react";
import { useHormiguero } from "../../hooks/useHormiguero";
import { HormiguerGraph } from "./Graph";
import { IncidentsTable } from "./IncidentsTable";
import { AntsList } from "./AntsList";
import type { HormiguerUIState } from "../../types/hormiguero";

// Use the shared HormiguerUIState type to ensure all required fields are present
type NodeId = string | null;

export const HormigueroDashboard = () => {
    const { state, actions } = useHormiguero();

    const open_count = state.incidents.filter((i) => i.status === "open").length;
    const critical_count = state.incidents.filter((i) => i.severity === "critical").length;

    return (
        <div className="w-full h-full flex flex-col bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b p-4 shadow-sm">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-red-600">👑 HORMIGUERO</h1>
                        <p className="text-sm text-gray-600">
                            Queen-led parallelization with{" "}
                            <span className="font-semibold">{state.ants.length} active ants</span>
                        </p>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="text-center">
                            <div className="text-3xl font-bold text-orange-600">{open_count}</div>
                            <div className="text-xs text-gray-600">Open Incidents</div>
                        </div>

                        {critical_count > 0 && (
                            <div className="text-center">
                                <div className="text-3xl font-bold text-red-600">{critical_count}</div>
                                <div className="text-xs text-gray-600">Critical</div>
                            </div>
                        )}

                        <button
                            onClick={() => actions.triggerScan()}
                            disabled={state.is_scanning}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400"
                        >
                            {state.is_scanning ? "Scanning..." : "🔍 Scan Now"}
                        </button>
                    </div>
                </div>

                {state.error && (
                    <div className="mt-3 p-3 bg-red-100 text-red-700 rounded text-sm flex justify-between items-center">
                        <span>{state.error}</span>
                        <button
                            onClick={() => actions.clearError()}
                            className="text-red-700 hover:text-red-900 font-bold"
                        >
                            ✕
                        </button>
                    </div>
                )}
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto p-6">
                <div className="grid grid-cols-12 gap-6 auto-rows-max">
                    {/* Graph (full width, auto height) */}
                    <div className="col-span-12 bg-white border rounded-lg shadow-sm overflow-hidden" style={{ height: "500px" }}>
                        <div className="p-4 border-b bg-gray-50">
                            <h2 className="font-bold">System Topology</h2>
                        </div>
                        <HormiguerGraph
                            state={state}
                            onNodeClick={(nodeId: NodeId) => {
                                if (nodeId === "queen") {
                                    actions.selectAnt(null);
                                } else {
                                    actions.selectAnt(nodeId);
                                }
                            }}
                        />
                    </div>

                    {/* Incidents Table (8 columns) */}
                    <div className="col-span-8">
                        <IncidentsTable
                            incidents={state.incidents}
                            selected_id={state.selected_incident_id}
                            onSelect={(id) => actions.selectIncident(id)}
                            onDispatch={(id) => actions.dispatchDecision(id)}
                            is_loading={state.is_scanning}
                        />
                    </div>

                    {/* Ants List (4 columns) */}
                    <div className="col-span-4">
                        <AntsList
                            ants={state.ants}
                            selected_id={state.selected_ant_id}
                            onSelect={(id) => actions.selectAnt(id)}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

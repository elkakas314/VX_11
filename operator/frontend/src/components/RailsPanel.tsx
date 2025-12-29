/**
 * RailsPanel - Manifestator lanes visualization
 * operator/frontend/src/components/RailsPanel.tsx
 */

import React, { useEffect, useState } from 'react'
import { useRailsStore, RailsLane, Rail } from '../stores'
import { apiClient } from '../services/api'

export const RailsPanel: React.FC = () => {
    const { lanes, setLanes, rails, setRails, expandedLanes, toggleLaneExpanded, loading, setLoading } =
        useRailsStore()
    const [error, setError] = useState<string | null>(null)

    // Fetch lanes and rails
    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
                setError(null)

                // Fetch lanes
                const lanesResp = await apiClient.request<{ lanes?: RailsLane[] }>(
                    'GET',
                    '/operator/api/rails/lanes'
                )
                if (!lanesResp.ok || !lanesResp.data) throw new Error(lanesResp.error || 'Failed to fetch lanes')
                setLanes(lanesResp.data.lanes || [])

                // Fetch rails
                const railsResp = await apiClient.request<{ rails?: Rail[] }>(
                    'GET',
                    '/operator/api/rails'
                )
                if (!railsResp.ok || !railsResp.data) throw new Error(railsResp.error || 'Failed to fetch rails')
                setRails(railsResp.data.rails || [])
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error')
            } finally {
                setLoading(false)
            }
        }

        fetchData()
    }, [setLanes, setRails, setLoading])

    const stageOrder = { detect: 0, plan: 1, validate: 2, apply: 3 }
    const sortedLanes = [...lanes].sort((a, b) => (stageOrder[a.stage as keyof typeof stageOrder] || 999) - (stageOrder[b.stage as keyof typeof stageOrder] || 999))

    const stageBgColor: Record<string, string> = {
        detect: 'bg-blue-900',
        plan: 'bg-purple-900',
        validate: 'bg-orange-900',
        apply: 'bg-green-900',
    }

    const severityColor: Record<string, string> = {
        critical: 'text-red-400 font-bold',
        error: 'text-orange-400',
        warn: 'text-yellow-400',
        info: 'text-blue-400',
    }

    return (
        <div className="flex flex-col h-full bg-slate-950 text-slate-100 rounded-lg border border-slate-700">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-700 bg-slate-900">
                <h3 className="text-lg font-semibold">🚂 Rails & Lanes (Manifestator)</h3>
                <p className="text-xs text-slate-400 mt-1">Drift detection pipeline: detect → plan → validate → apply</p>
            </div>

            {/* Error */}
            {error && (
                <div className="px-4 py-2 bg-red-900 text-red-100 text-sm">{error}</div>
            )}

            {/* Lanes Pipeline */}
            <div className="flex-1 overflow-auto p-4">
                {loading ? (
                    <div className="text-center text-slate-400">Loading lanes...</div>
                ) : sortedLanes.length === 0 ? (
                    <div className="text-center text-slate-400">No lanes available</div>
                ) : (
                    <div className="flex gap-4 pb-4">
                        {sortedLanes.map((lane: RailsLane) => (
                            <div
                                key={lane.lane_id}
                                className={`flex-1 min-w-48 ${stageBgColor[lane.stage]} rounded-lg border border-slate-600 overflow-hidden flex flex-col`}
                            >
                                {/* Stage Header */}
                                <div className="px-3 py-2 bg-black bg-opacity-30 border-b border-slate-600">
                                    <div className="font-bold text-sm uppercase">{lane.stage}</div>
                                    <div className="text-xs text-slate-300 mt-1">{lane.name}</div>
                                </div>

                                {/* Content */}
                                <div className="flex-1 p-3 flex flex-col">
                                    <p className="text-xs text-slate-300 mb-2">{lane.description}</p>

                                    {/* Checks */}
                                    {lane.checks && lane.checks.length > 0 && (
                                        <div className="mt-2">
                                            <div className="text-xs font-semibold text-slate-200 mb-1">Checks:</div>
                                            <div className="space-y-1">
                                                {lane.checks.map((check) => (
                                                    <div key={check.check_id} className="text-xs bg-black bg-opacity-40 px-2 py-1 rounded">
                                                        <span className="font-mono">{check.name}</span>
                                                        <span className="text-slate-400 ml-1">({check.timeout_seconds}s)</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Toggle Expand */}
                                    <button
                                        onClick={() => toggleLaneExpanded(lane.lane_id)}
                                        className="mt-auto text-xs text-blue-300 hover:text-blue-200 pt-2 border-t border-slate-600"
                                    >
                                        {expandedLanes.has(lane.lane_id) ? '▼ Hide' : '▶ Show'} Details
                                    </button>
                                </div>

                                {/* Expanded Details */}
                                {expandedLanes.has(lane.lane_id) && (
                                    <div className="px-3 py-2 bg-black bg-opacity-50 border-t border-slate-600 max-h-32 overflow-y-auto">
                                        <div className="text-xs text-slate-300">
                                            <div className="font-mono">
                                                Lane ID: <span className="text-slate-400">{lane.lane_id}</span>
                                            </div>
                                            <div className="font-mono mt-1">
                                                Created: <span className="text-slate-400">{new Date(lane.created_at).toLocaleString()}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Rails Summary */}
            {rails.length > 0 && (
                <div className="px-4 py-3 border-t border-slate-700 bg-slate-900 max-h-48 overflow-y-auto">
                    <div className="text-xs font-semibold text-slate-200 mb-2">Active Rails ({rails.length}):</div>
                    <div className="space-y-1">
                        {rails
                            .filter((r: Rail) => r.active)
                            .slice(0, 5)
                            .map((rail: Rail) => (
                                <div key={rail.rail_id} className="text-xs flex justify-between items-center">
                                    <span className="text-slate-300">{rail.name}</span>
                                    <span className={`${severityColor[rail.severity_on_violation]} font-mono`}>
                                        {rail.severity_on_violation}
                                    </span>
                                </div>
                            ))}
                    </div>
                    {rails.length > 5 && <div className="text-xs text-slate-500 mt-2">+{rails.length - 5} more...</div>}
                </div>
            )}
        </div>
    )
}

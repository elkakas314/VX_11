/**
 * MetricsPanel - Timeseries metrics display
 * operator/frontend/src/components/MetricsPanel.tsx
 */

import React, { useEffect, useState } from 'react'
import { useMetricsStore } from '../stores'

export const MetricsPanel: React.FC = () => {
    const { metrics, setMetrics, selectedMetrics, toggleMetric, timeWindow, setTimeWindow, loading, setLoading } =
        useMetricsStore()
    const [error, setError] = useState<string | null>(null)

    // Fetch metrics
    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                setLoading(true)
                setError(null)

                const token = localStorage.getItem('vx11_token') || ''
                const response = await fetch(
                    `/api/metrics?window_seconds=${timeWindow === '1h' ? 3600 : timeWindow === '6h' ? 21600 : timeWindow === '24h' ? 86400 : 604800}`,
                    { headers: { 'x-vx11-token': token } }
                )

                if (!response.ok) throw new Error(`HTTP ${response.status}`)
                const data = await response.json()
                setMetrics(data.metrics || [])
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error')
            } finally {
                setLoading(false)
            }
        }

        fetchMetrics()
    }, [timeWindow, setMetrics, setLoading])

    const availableMetrics = Array.from(new Set(metrics.map((m) => m.metric_name)))

    const latestMetrics = availableMetrics.reduce(
        (acc, metricName) => {
            const latest = metrics
                .filter((m) => m.metric_name === metricName)
                .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0]
            if (latest) acc[metricName] = latest
            return acc
        },
        {} as Record<string, any>
    )

    const formatValue = (value: number, unit: string) => {
        if (unit === 'bytes') {
            if (value > 1e9) return `${(value / 1e9).toFixed(2)} GB`
            if (value > 1e6) return `${(value / 1e6).toFixed(2)} MB`
            if (value > 1e3) return `${(value / 1e3).toFixed(2)} KB`
            return `${value} B`
        }
        return `${value.toFixed(2)} ${unit}`
    }

    return (
        <div className="flex flex-col h-full bg-slate-950 text-slate-100 rounded-lg border border-slate-700">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-700 bg-slate-900">
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-lg font-semibold">📊 Metrics</h3>
                    <div className="flex gap-2">
                        {(['1h', '6h', '24h', '7d'] as const).map((window) => (
                            <button
                                key={window}
                                onClick={() => setTimeWindow(window)}
                                className={`px-2 py-1 rounded text-xs font-medium ${timeWindow === window
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                    }`}
                            >
                                {window}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Metric Selector */}
                <div className="flex flex-wrap gap-2">
                    {availableMetrics.map((metricName) => (
                        <button
                            key={metricName}
                            onClick={() => toggleMetric(metricName)}
                            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${selectedMetrics.includes(metricName)
                                    ? 'bg-blue-700 text-white'
                                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                                }`}
                        >
                            {metricName}
                        </button>
                    ))}
                </div>
            </div>

            {/* Error */}
            {error && <div className="px-4 py-2 bg-red-900 text-red-100 text-sm">{error}</div>}

            {/* Content */}
            <div className="flex-1 overflow-auto p-4">
                {loading ? (
                    <div className="text-center text-slate-400">Loading metrics...</div>
                ) : Object.keys(latestMetrics).length === 0 ? (
                    <div className="text-center text-slate-400">No metrics available</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {Object.entries(latestMetrics)
                            .filter(([name]) => selectedMetrics.includes(name))
                            .map(([metricName, metric]) => (
                                <div key={metricName} className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                                    <div className="text-xs text-slate-400 mb-1">{metricName}</div>
                                    <div className="text-2xl font-bold text-blue-300 mb-1">
                                        {formatValue(metric.value, metric.unit)}
                                    </div>
                                    <div className="text-xs text-slate-500">
                                        Module: <span className="text-slate-400">{metric.module}</span>
                                    </div>
                                    <div className="text-xs text-slate-500 mt-1">
                                        <span className="font-mono">{new Date(metric.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                </div>
                            ))}
                    </div>
                )}
            </div>
        </div>
    )
}

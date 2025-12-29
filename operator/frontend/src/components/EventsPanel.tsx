/**
 * EventsPanel - Real-time event stream with filtering
 * operator/frontend/src/components/EventsPanel.tsx
 */

import React, { useEffect, useState, useCallback } from 'react'
import { useEventsStore, VX11Event } from '../stores'

interface EventsPanelProps {
    autoRefresh?: boolean
    refreshInterval?: number
}

export const EventsPanel: React.FC<EventsPanelProps> = ({
    autoRefresh = true,
    refreshInterval = 5000,
}) => {
    const {
        events,
        setEvents,
        filterSeverity,
        setFilterSeverity,
        filterModule,
        setFilterModule,
        loading,
        setLoading,
        error,
        setError,
    } = useEventsStore()

    const [scrollToBottom, setScrollToBottom] = useState(true)

    // Fetch events from API
    const fetchEvents = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)

            const params = new URLSearchParams()
            if (filterSeverity !== 'all') params.append('severity', filterSeverity)
            if (filterModule) params.append('module', filterModule)
            params.append('limit', '100')

            const response = await fetch(`/api/events?${params}`, {
                headers: {
                    'x-vx11-token': localStorage.getItem('vx11_token') || '',
                },
            })

            if (!response.ok) throw new Error(`HTTP ${response.status}`)

            const data = await response.json()
            setEvents(data.events || [])
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error')
            setEvents([])
        } finally {
            setLoading(false)
        }
    }, [filterSeverity, filterModule, setEvents, setLoading, setError])

    // Initial fetch
    useEffect(() => {
        fetchEvents()
    }, [filterSeverity, filterModule, fetchEvents])

    // Auto-refresh
    useEffect(() => {
        if (!autoRefresh) return

        const interval = setInterval(fetchEvents, refreshInterval)
        return () => clearInterval(interval)
    }, [autoRefresh, refreshInterval, fetchEvents])

    const severityColors: Record<string, string> = {
        critical: 'bg-red-900 text-red-100',
        error: 'bg-orange-900 text-orange-100',
        warn: 'bg-yellow-900 text-yellow-100',
        info: 'bg-blue-900 text-blue-100',
    }

    const filteredEvents = events.filter((e) => {
        if (filterSeverity !== 'all' && e.severity !== filterSeverity) return false
        if (filterModule && e.module !== filterModule) return false
        return true
    })

    // Auto scroll to bottom when new events arrive
    useEffect(() => {
        if (scrollToBottom) {
            const container = document.querySelector('[data-events-scroll]')
            if (container) {
                container.scrollTop = container.scrollHeight
            }
        }
    }, [events, scrollToBottom])

    return (
        <div className="flex flex-col h-full bg-slate-950 text-slate-100 rounded-lg border border-slate-700">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-700 bg-slate-900">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold">📡 Events Stream</h3>
                    <button
                        onClick={fetchEvents}
                        disabled={loading}
                        className="px-3 py-1 bg-blue-700 hover:bg-blue-600 disabled:bg-slate-600 rounded text-sm font-medium"
                    >
                        {loading ? 'Loading...' : 'Refresh'}
                    </button>
                </div>

                {/* Filters */}
                <div className="flex gap-3 flex-wrap">
                    <div>
                        <label htmlFor="severity-filter" className="block text-xs text-slate-400 mb-1">Severity</label>
                        <select
                            id="severity-filter"
                            value={filterSeverity}
                            onChange={(e) => setFilterSeverity(e.target.value)}
                            className="px-2 py-1 bg-slate-800 border border-slate-600 rounded text-sm text-slate-100"
                        >
                            <option value="all">All</option>
                            <option value="critical">Critical</option>
                            <option value="error">Error</option>
                            <option value="warn">Warn</option>
                            <option value="info">Info</option>
                        </select>
                    </div>

                    <div>
                        <label htmlFor="module-filter" className="block text-xs text-slate-400 mb-1">Module</label>
                        <input
                            id="module-filter"
                            type="text"
                            placeholder="Filter by module"
                            value={filterModule}
                            onChange={(e) => setFilterModule(e.target.value)}
                            className="px-2 py-1 bg-slate-800 border border-slate-600 rounded text-sm text-slate-100 placeholder-slate-500"
                        />
                    </div>

                    <div className="flex items-end">
                        <label className="flex items-center gap-2 text-xs">
                            <input
                                type="checkbox"
                                checked={scrollToBottom}
                                onChange={(e) => setScrollToBottom(e.target.checked)}
                                className="accent-blue-500"
                            />
                            <span className="text-slate-300">Auto-scroll</span>
                        </label>
                    </div>
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="px-4 py-2 bg-red-900 text-red-100 text-sm border-b border-red-700">
                    {error}
                </div>
            )}

            {/* Events List */}
            <div
                data-events-scroll
                className="flex-1 overflow-y-auto scroll-smooth max-h-[calc(100%-140px)]"
            >
                {filteredEvents.length === 0 ? (
                    <div className="p-4 text-center text-slate-400">
                        {events.length === 0 ? 'No events yet' : 'No events match filters'}
                    </div>
                ) : (
                    <div className="divide-y divide-slate-700">
                        {filteredEvents.map((event: VX11Event) => (
                            <div
                                key={event.event_id}
                                className={`px-4 py-3 hover:bg-slate-900 transition-colors ${severityColors[event.severity] || 'bg-slate-800'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <span className="font-mono text-xs text-slate-400">
                                        {new Date(event.created_at).toLocaleTimeString()}
                                    </span>
                                    <span className="text-xs font-mono text-slate-500">
                                        {event.correlation_id.slice(0, 8)}
                                    </span>
                                </div>
                                <div className="font-semibold text-sm mb-1">{event.summary}</div>
                                <div className="flex gap-2 text-xs text-slate-300">
                                    <span className="bg-slate-800 px-2 py-1 rounded">{event.event_type}</span>
                                    <span className="bg-slate-800 px-2 py-1 rounded">{event.module}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-slate-700 bg-slate-900 text-xs text-slate-400">
                Showing {filteredEvents.length} of {events.length} events
            </div>
        </div>
    )
}

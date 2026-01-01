import { useEffect, useMemo, useState } from 'react'
import { apiClient } from '../services/api'
import { useEventsStore } from '../stores'
import './HormigueroView.css'

export function HormigueroView() {
    const { events, setEvents } = useEventsStore()
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadEvents()
    }, [])

    async function loadEvents() {
        setLoading(true)
        setError(null)
        try {
            const resp = await apiClient.events()
            if (resp.ok && resp.data) {
                setEvents(resp.data.events || resp.data)
            } else {
                // OFF_BY_POLICY means no events available in solo_madre mode, not an error
                if (resp.data?.status === 'OFF_BY_POLICY' || resp.status === 403) {
                    setError('solo_madre: events unavailable (open window to enable)')
                    setEvents([])
                } else {
                    setError(resp.error || 'Unable to load events')
                }
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load events')
        } finally {
            setLoading(false)
        }
    }

    const summary = useMemo(() => {
        const counts: Record<string, number> = {}
        events.forEach((event) => {
            const key = event.severity || 'info'
            counts[key] = (counts[key] || 0) + 1
        })
        return counts
    }, [events])

    return (
        <div className="hormiguero-view">
            <div className="view-header">
                <h2>Hormiguero</h2>
                <button onClick={loadEvents} className="btn-secondary">
                    ⟳ Refresh
                </button>
            </div>

            {error && <div className="error-banner">{error}</div>}

            <div className="hormiguero-summary">
                {Object.entries(summary).map(([severity, count]) => {
                    const pct = Math.min(100, count * 10)
                    return (
                        <div key={severity} className={`summary-card bar-${pct}`}>
                            <span className={`severity-dot severity-${severity}`}></span>
                            <div className="summary-info">
                                <span className="summary-label">{severity}</span>
                                <span className="summary-count">{count}</span>
                            </div>
                            <div className="summary-bar"></div>
                        </div>
                    )
                })}
            </div>

            {loading ? (
                <div className="view-loading">⟳ Loading events...</div>
            ) : (
                <div className="event-feed">
                    {events.length > 0 ? (
                        events.map((event) => (
                            <div key={event.event_id} className="event-item">
                                <div className="event-header">
                                    <span className={`severity-dot severity-${event.severity}`}></span>
                                    <span className="event-type">{event.event_type}</span>
                                    <span className="event-module">{event.module}</span>
                                    <span className="event-time">
                                        {new Date(event.created_at).toLocaleTimeString()}
                                    </span>
                                </div>
                                <div className="event-summary">{event.summary}</div>
                            </div>
                        ))
                    ) : (
                        <p className="empty">No events available</p>
                    )}
                </div>
            )}
        </div>
    )
}

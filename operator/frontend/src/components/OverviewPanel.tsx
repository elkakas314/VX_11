/**
 * OverviewPanel - System health summary
 * operator/frontend/src/components/OverviewPanel.tsx
 */

import React, { useEffect } from 'react'
import { useOverviewStore, useWindowStatusStore } from '../stores'
import { apiClient } from '../services/api'

export const OverviewPanel: React.FC = () => {
    const {
        totalEvents,
        setTotalEvents,
        activeModules,
        setActiveModules,
        lastEventTime,
        setLastEventTime,
        activeLanes,
        setActiveLanes,
    } = useOverviewStore()

    const { windowStatus } = useWindowStatusStore()

    // Fetch overview data
    useEffect(() => {
        const fetchOverview = async () => {
            try {
                // Fetch events count
                const eventsResp = await apiClient.request<{
                    total?: number
                    events?: Array<{ created_at?: string }>
                    }>('GET', '/operator/api/events?limit=1')
                if (eventsResp.ok && eventsResp.data) {
                    setTotalEvents(eventsResp.data.total || 0)
                    if (eventsResp.data.events?.[0]?.created_at) {
                        setLastEventTime(eventsResp.data.events[0].created_at)
                    }
                }

                // Fetch lanes count
                const lanesResp = await apiClient.request<{ lanes?: unknown[] }>(
                    'GET',
                    '/operator/api/rails/lanes'
                )
                if (lanesResp.ok && lanesResp.data) {
                    setActiveLanes(lanesResp.data.lanes?.length || 0)
                }

                // Set active modules
                if (windowStatus) {
                    const services = windowStatus.services || []
                    setActiveModules({
                        madre: services.includes('madre'),
                        redis: services.includes('redis'),
                        tentaculo: services.includes('tentaculo_link'),
                        operator: true,
                    })
                }
            } catch (err) {
                console.error('Failed to fetch overview:', err)
            }
        }

        fetchOverview()
    }, [windowStatus, setTotalEvents, setLastEventTime, setActiveLanes, setActiveModules])

    const moduleCards = [
        { name: 'Madre', status: activeModules.madre, color: 'bg-blue-900' },
        { name: 'Redis', status: activeModules.redis, color: 'bg-red-900' },
        { name: 'Tentáculo', status: activeModules.tentaculo, color: 'bg-green-900' },
        { name: 'Operator', status: activeModules.operator, color: 'bg-purple-900' },
    ]

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Module Status Cards */}
            {moduleCards.map((module) => (
                <div
                    key={module.name}
                    className={`${module.color} rounded-lg p-4 border border-slate-600 text-white`}
                >
                    <div className="text-sm font-semibold mb-2">{module.name}</div>
                    <div className="text-2xl font-bold mb-2">{module.status ? '🟢' : '🔴'}</div>
                    <div className="text-xs text-slate-300">
                        Status: <span className={module.status ? 'text-green-300' : 'text-red-300'}>
                            {module.status ? 'UP' : 'DOWN'}
                        </span>
                    </div>
                </div>
            ))}

            {/* Events Counter */}
            <div className="bg-orange-900 rounded-lg p-4 border border-slate-600 text-white md:col-span-1 lg:col-span-2">
                <div className="text-sm font-semibold mb-2">Total Events</div>
                <div className="text-3xl font-bold mb-2">{totalEvents}</div>
                <div className="text-xs text-slate-300">
                    Last event:{' '}
                    <span className="text-slate-100">
                        {lastEventTime ? new Date(lastEventTime).toLocaleTimeString() : 'N/A'}
                    </span>
                </div>
            </div>

            {/* Active Lanes */}
            <div className="bg-teal-900 rounded-lg p-4 border border-slate-600 text-white md:col-span-1 lg:col-span-2">
                <div className="text-sm font-semibold mb-2">Active Lanes</div>
                <div className="text-3xl font-bold mb-2">{activeLanes}</div>
                <div className="text-xs text-slate-300">
                    Pipeline stages: <span className="text-slate-100">detect → plan → validate → apply</span>
                </div>
            </div>

            {/* Mode Indicator */}
            {windowStatus && (
                <div
                    className={`rounded-lg p-4 border border-slate-600 text-white md:col-span-1 lg:col-span-4 ${windowStatus.mode === 'solo_madre' ? 'bg-blue-900' : 'bg-green-900'
                        }`}
                >
                    <div className="text-sm font-semibold mb-2">System Mode</div>
                    <div className="flex justify-between items-center">
                        <span className="text-xl font-bold uppercase">{windowStatus.mode}</span>
                        <span className={windowStatus.degraded ? 'text-yellow-300' : 'text-green-300'}>
                            Health: {windowStatus.degraded ? 'degraded' : 'ok'}
                        </span>
                    </div>
                </div>
            )}
        </div>
    )
}

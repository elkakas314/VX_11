/**
 * WindowStatusBar - Sticky header showing system status + mode + TTL
 * operator/frontend/src/components/WindowStatusBar.tsx
 */

import React, { useEffect } from 'react'
import { useWindowStatusStore } from '../stores'

export const WindowStatusBar: React.FC = () => {
    const { windowStatus, ttlCountdown, setTtlCountdown } = useWindowStatusStore()

    // Countdown timer for window mode
    useEffect(() => {
        if (!windowStatus || windowStatus.mode !== 'window_active' || !windowStatus.ttl_seconds) {
            return
        }

        const interval = setInterval(() => {
            setTtlCountdown(Math.max(0, ttlCountdown - 1))
        }, 1000)

        return () => clearInterval(interval)
    }, [windowStatus, setTtlCountdown, ttlCountdown])

    if (!windowStatus) {
        return null
    }

    const modeColor = {
        solo_madre: 'bg-blue-900',
        window_active: 'bg-green-700',
        degraded: 'bg-yellow-700',
    }[windowStatus.mode]

    const healthIcon = {
        ok: '✓',
        degraded: '⚠',
        offline: '✕',
    }[windowStatus.health]

    const healthColor = {
        ok: 'text-green-400',
        degraded: 'text-yellow-400',
        offline: 'text-red-400',
    }[windowStatus.health]

    return (
        <div className={`${modeColor} text-white px-4 py-2 flex items-center justify-between text-sm sticky top-0 z-50`}>
            <div className="flex items-center gap-4">
                <span className="font-bold">VX11 {windowStatus.mode.toUpperCase()}</span>

                <div className="flex gap-6 text-xs">
                    <span>
                        Madre: <span className={windowStatus.madre_status === 'UP' ? 'text-green-300' : 'text-red-300'}>
                            {windowStatus.madre_status}
                        </span>
                    </span>
                    <span>
                        Redis: <span className={windowStatus.redis_status === 'UP' ? 'text-green-300' : 'text-red-300'}>
                            {windowStatus.redis_status}
                        </span>
                    </span>
                    <span>
                        Tentáculo: <span className={windowStatus.tentaculo_status === 'UP' ? 'text-green-300' : 'text-red-300'}>
                            {windowStatus.tentaculo_status}
                        </span>
                    </span>
                </div>
            </div>

            <div className="flex items-center gap-4">
                <span className={`font-mono ${healthColor}`}>
                    {healthIcon} {windowStatus.health}
                </span>

                {windowStatus.mode === 'window_active' && windowStatus.ttl_seconds && (
                    <span className="font-mono text-yellow-300">
                        TTL: {Math.floor(ttlCountdown / 60)}:{String(ttlCountdown % 60).padStart(2, '0')}
                    </span>
                )}

                {windowStatus.request_id && (
                    <span className="text-xs opacity-75 font-mono">
                        ID: {windowStatus.request_id.slice(0, 8)}...
                    </span>
                )}
            </div>
        </div>
    )
}

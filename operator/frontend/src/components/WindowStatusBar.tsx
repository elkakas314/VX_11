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

        setTtlCountdown(Math.floor(windowStatus.ttl_seconds))

        const interval = setInterval(() => {
            setTtlCountdown((prev) => Math.max(0, prev - 1))
        }, 1000)

        return () => clearInterval(interval)
    }, [windowStatus, setTtlCountdown])

    if (!windowStatus) {
        return null
    }

    const modeColor = {
        solo_madre: 'bg-blue-900',
        window_active: 'bg-green-700',
        degraded: 'bg-yellow-700',
    }[windowStatus.mode]

    const healthState = windowStatus.degraded ? 'degraded' : 'ok'
    const healthIcon = {
        ok: '✓',
        degraded: '⚠',
    }[healthState]

    const healthColor = {
        ok: 'text-green-400',
        degraded: 'text-yellow-400',
    }[healthState]

    const serviceStatus = (name: string) =>
        windowStatus.services?.includes(name) ? 'UP' : 'OFF'

    return (
        <div className={`${modeColor} text-white px-4 py-2 flex items-center justify-between text-sm sticky top-0 z-50`}>
            <div className="flex items-center gap-4">
                <span className="font-bold">VX11 {windowStatus.mode.toUpperCase()}</span>

                <div className="flex gap-6 text-xs">
                    <span>
                        Madre: <span className={serviceStatus('madre') === 'UP' ? 'text-green-300' : 'text-red-300'}>
                            {serviceStatus('madre')}
                        </span>
                    </span>
                    <span>
                        Redis: <span className={serviceStatus('redis') === 'UP' ? 'text-green-300' : 'text-red-300'}>
                            {serviceStatus('redis')}
                        </span>
                    </span>
                    <span>
                        Tentáculo: <span className={serviceStatus('tentaculo_link') === 'UP' ? 'text-green-300' : 'text-red-300'}>
                            {serviceStatus('tentaculo_link')}
                        </span>
                    </span>
                </div>
            </div>

            <div className="flex items-center gap-4">
                <span className={`font-mono ${healthColor}`}>
                    {healthIcon} {healthState}
                </span>

                {windowStatus.mode === 'window_active' && windowStatus.ttl_seconds && (
                    <span className="font-mono text-yellow-300">
                        TTL: {Math.floor(ttlCountdown / 60)}:{String(ttlCountdown % 60).padStart(2, '0')}
                    </span>
                )}

                {windowStatus.window_id && (
                    <span className="text-xs opacity-75 font-mono">
                        ID: {windowStatus.window_id.slice(0, 8)}...
                    </span>
                )}
            </div>
        </div>
    )
}

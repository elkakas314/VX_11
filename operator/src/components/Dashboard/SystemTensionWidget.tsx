/**
 * System Tension Widget — Real-time stress metric (0-100)
 * WS: switch.system_tension
 * Fallback: "—" if no event within 5s
 */

import React, { useEffect, useState } from "react";

interface SystemTensionWidgetProps {
    wsValue?: number; // 0-100, from WS
    refreshInterval?: number; // fallback check interval (ms)
}

export const SystemTensionWidget: React.FC<SystemTensionWidgetProps> = ({
    wsValue,
    refreshInterval = 5000,
}) => {
    const [value, setValue] = useState<number | null>(wsValue ?? null);
    const [showFallback, setShowFallback] = useState(false);

    useEffect(() => {
        if (wsValue !== undefined && wsValue !== null) {
            setValue(wsValue);
            setShowFallback(false);
        }
    }, [wsValue]);

    useEffect(() => {
        const timer = setTimeout(() => {
            if (value === null) {
                setShowFallback(true);
            }
        }, refreshInterval);
        return () => clearTimeout(timer);
    }, [value, refreshInterval]);

    // Color logic: green <30, yellow 30-70, red >70
    const getColor = (v: number): string => {
        if (v < 30) return "text-green-600";
        if (v < 70) return "text-yellow-600";
        return "text-red-600";
    };

    const getBackgroundColor = (v: number): string => {
        if (v < 30) return "bg-green-100";
        if (v < 70) return "bg-yellow-100";
        return "bg-red-100";
    };

    return (
        <div className={`p-4 rounded-lg ${getBackgroundColor(value ?? 0)} border border-gray-300`}>
            <div className="text-sm font-semibold text-gray-700 mb-2">System Tension</div>
            {showFallback ? (
                <div className="text-2xl font-bold text-gray-500">—</div>
            ) : value !== null ? (
                <div className={`text-3xl font-bold ${getColor(value)}`}>
                    {value}%
                </div>
            ) : (
                <div className="text-xl text-gray-400 animate-pulse">Connecting...</div>
            )}
            <div className="text-xs text-gray-600 mt-2">
                {value === null ? "Waiting for WS" : `Last update: now`}
            </div>
        </div>
    );
};

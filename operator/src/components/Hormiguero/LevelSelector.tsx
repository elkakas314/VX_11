/**
 * Hormiguero Level Selector — Macro / Meso / Micro abstraction
 * Passive UI: selector buttons, emit WS request, render based on data
 */

import React, { useState } from "react";
import { HormigueroLevel } from "../../types/v8_1_extensions";

interface LevelSelectorProps {
    currentLevel?: HormigueroLevel;
    onLevelChange?: (level: HormigueroLevel) => void;
    levelData?: Record<string, unknown>;
}

export const HormigueroLevelSelector: React.FC<LevelSelectorProps> = ({
    currentLevel = HormigueroLevel.MACRO,
    onLevelChange,
    levelData = {},
}) => {
    const [loading, setLoading] = useState(false);

    const handleSelectLevel = (level: HormigueroLevel) => {
        setLoading(true);
        onLevelChange?.(level);
        setTimeout(() => setLoading(false), 500); // Fallback
    };

    const descriptions = {
        [HormigueroLevel.MACRO]: "Colony overview",
        [HormigueroLevel.MESO]: "Team dynamics",
        [HormigueroLevel.MICRO]: "Individual ants",
    };

    return (
        <div className="p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg border border-orange-300">
            <div className="text-sm font-semibold mb-3">🐜 Hormiguero Abstraction Level</div>

            <div className="flex gap-2 mb-4">
                {Object.values(HormigueroLevel).map((level) => (
                    <button
                        key={level}
                        onClick={() => handleSelectLevel(level)}
                        disabled={loading}
                        className={`px-4 py-2 rounded font-semibold text-sm transition-all ${currentLevel === level
                                ? "bg-orange-600 text-white shadow-lg"
                                : "bg-white text-orange-700 border border-orange-300 hover:bg-orange-100"
                            } disabled:opacity-50`}
                    >
                        {level.toUpperCase()}
                    </button>
                ))}
            </div>

            {/* Current level description */}
            <div className="text-xs text-gray-700 mb-3">
                <span className="font-semibold">Mode:</span> {descriptions[currentLevel]}
            </div>

            {/* Level data (if any) */}
            {Object.keys(levelData).length > 0 ? (
                <div className="p-2 bg-white rounded border border-orange-200 text-xs">
                    <div className="font-semibold mb-1">Data:</div>
                    <pre className="text-gray-600 overflow-auto max-h-32">
                        {JSON.stringify(levelData, null, 2)}
                    </pre>
                </div>
            ) : (
                <div className="text-xs text-gray-500 italic">No level-specific data yet</div>
            )}
        </div>
    );
};

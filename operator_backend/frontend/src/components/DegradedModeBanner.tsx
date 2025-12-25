import React, { useEffect, useState } from "react";

export interface DegradedModeBannerProps {
    visible: boolean;
    hint?: string;
    autoDismissMs?: number;
    onDismiss?: () => void;
}

export const DegradedModeBanner: React.FC<DegradedModeBannerProps> = ({
    visible,
    hint,
    autoDismissMs = 5000,
    onDismiss,
}) => {
    const [isShowing, setIsShowing] = useState(visible);

    useEffect(() => {
        setIsShowing(visible);
        if (visible && autoDismissMs > 0) {
            const timer = setTimeout(() => {
                setIsShowing(false);
                onDismiss?.();
            }, autoDismissMs);
            return () => clearTimeout(timer);
        }
    }, [visible, autoDismissMs, onDismiss]);

    if (!isShowing) return null;

    return (
        <div className="mb-3 p-4 bg-yellow-950 border-2 border-yellow-500 rounded-lg text-sm text-yellow-100 flex items-start justify-between shadow-lg animate-pulse">
            <div>
                <p className="font-bold">⚠️ DEGRADED MODE ACTIVE</p>
                <p className="text-xs text-yellow-300 mt-1">
                    {hint || "Limited functionality - using fallback"}
                </p>
            </div>
            <button
                onClick={() => {
                    setIsShowing(false);
                    onDismiss?.();
                }}
                className="text-yellow-300 hover:text-yellow-100 font-bold ml-4 cursor-pointer"
                aria-label="Dismiss degraded mode banner"
            >
                ✕
            </button>
        </div>
    );
};

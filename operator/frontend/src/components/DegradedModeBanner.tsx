interface DegradedModeBannerProps {
    show?: boolean
    message?: string
}

export function DegradedModeBanner({
    show = true,
    message = 'Degraded Mode: Some services are unavailable (solo_madre policy active)',
}: DegradedModeBannerProps) {
    if (!show) return null

    return (
        <div className="degraded-mode-banner">
            <span className="degraded-icon">⚠️</span>
            <span className="degraded-message">{message}</span>
        </div>
    )
}

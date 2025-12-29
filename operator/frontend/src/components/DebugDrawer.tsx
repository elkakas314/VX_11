import { useState } from 'react'
import './DebugDrawer.css'

interface DebugDrawerProps {
    data?: Record<string, unknown>
    title?: string
}

export function DebugDrawer({ data = {}, title = 'Debug Info' }: DebugDrawerProps) {
    const [open, setOpen] = useState(false)

    if (!data || Object.keys(data).length === 0) return null

    return (
        <div className={`debug-drawer ${open ? 'open' : ''}`}>
            <button
                className="debug-toggle"
                onClick={() => setOpen(!open)}
                title="Toggle debug panel"
            >
                🔧
            </button>

            {open && (
                <div className="debug-panel">
                    <div className="debug-header">
                        <span>{title}</span>
                        <button
                            className="debug-close"
                            onClick={() => setOpen(false)}
                        >
                            ✕
                        </button>
                    </div>

                    <div className="debug-content">
                        <pre>{JSON.stringify(data, null, 2)}</pre>
                    </div>

                    <button
                        className="debug-copy"
                        onClick={() => {
                            navigator.clipboard.writeText(JSON.stringify(data, null, 2))
                        }}
                    >
                        📋 Copy JSON
                    </button>
                </div>
            )}
        </div>
    )
}

import type { CanonicalEvent } from "../../types/canonical-events";

interface PanelProps {
    title: string;
    events: CanonicalEvent[];
    icon?: string;
}

export function Panel({ title, events, icon = "◆" }: PanelProps) {
    return (
        <div className="bg-gradient-to-b from-gray-900/70 via-gray-950/60 to-gray-950 border border-gray-800/60 rounded-lg p-4 min-h-[16rem] flex flex-col backdrop-blur-sm hover:border-gray-700/80 transition-colors duration-300">
            <div className="flex items-center gap-2 mb-4">
                <span className="text-lg text-gray-400">{icon}</span>
                <h3 className="text-sm font-semibold text-gray-200 tracking-wide">{title}</h3>
                <span className="ml-auto text-xs bg-gray-800/60 px-2 py-1 rounded-sm text-gray-400 font-mono">
                    {events.length}
                </span>
            </div>
            <div className="flex-1 space-y-2 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
                {events.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-center">
                        <div className="text-gray-700">
                            <div className="text-3xl opacity-20 mb-2 animate-pulse">◇◆◇</div>
                            <p className="text-xs text-gray-600">Los tentáculos aguardan señales…</p>
                        </div>
                    </div>
                ) : (
                    events.map((e, i) => <EventRow key={i} event={e} />)
                )}
            </div>
        </div>
    );
}

function EventRow({ event }: { event: CanonicalEvent }) {
    const timestamp = safeEventTime(event);
    const eventPreview = safePreview(event);

    return (
        <div className="text-xs p-3 bg-gray-800/20 rounded border border-gray-700/40 hover:bg-gray-800/40 hover:border-gray-600/60 transition-all duration-200">
            <div className="text-gray-500 font-mono text-[10px] mb-1">{timestamp}</div>
            <div className="text-gray-400 line-clamp-2 font-light">
                {eventPreview}
            </div>
        </div>
    );
}

function safeEventTime(event: CanonicalEvent): string {
    const raw = (event as { timestamp?: unknown }).timestamp;
    const numeric = typeof raw === "number" ? raw : Number(raw);
    const ms = Number.isFinite(numeric) ? numeric * 1000 : NaN;
    try {
        return new Date(ms).toLocaleTimeString();
    } catch {
        return "—";
    }
}

function safePreview(event: CanonicalEvent): string {
    try {
        const s = JSON.stringify(event);
        return s.length > 120 ? `${s.slice(0, 120)}…` : s;
    } catch {
        return "{\"type\":\"unknown\"}";
    }
}

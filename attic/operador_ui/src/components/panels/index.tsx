import { Panel } from "./Panel";
import type { CanonicalEvent } from "../../types/canonical-events";

export function SystemAlertPanel({ events }: { events: CanonicalEvent[] }) {
    return <Panel title="System Alerts" events={events} icon="🚨" />;
}

export function CorrelationPanel({ events }: { events: CanonicalEvent[] }) {
    return <Panel title="Correlations (DAG)" events={events} icon="🔗" />;
}

export function ForensicPanel({ events }: { events: CanonicalEvent[] }) {
    return <Panel title="Forensic Timeline" events={events} icon="📸" />;
}

export function MadrePanel({ events }: { events: CanonicalEvent[] }) {
    return <Panel title="Madre Decisions" events={events} icon="🧠" />;
}

export function SwitchPanel({ events }: { events: CanonicalEvent[] }) {
    return <Panel title="Switch Tension" events={events} icon="⚡" />;
}

export function ShubPanel({ events }: { events: CanonicalEvent[] }) {
    return <Panel title="Shub Narratives" events={events} icon="🎙️" />;
}

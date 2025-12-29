---
title: "VX11 Operator UI - PHASE 4 Component Examples"
description: "Practical code examples for React + TypeScript + Tailwind CSS implementation"
date: "2025-12-29"
phase: "PHASE 4"
---

# VX11 Operator UI Architecture - Code Examples

## 1. Type Definitions (`services/types.ts`)

```typescript
/**
 * Core types for VX11 Operator UI
 * All APIs return these normalized types
 */

export type Severity = 'critical' | 'error' | 'warn' | 'info' | 'debug';
export type Health = 'ok' | 'degraded' | 'offline';
export type LaneStage = 'detect' | 'plan' | 'validate' | 'apply';
export type LaneStatus = 'in_progress' | 'passed' | 'failed' | 'blocked';
export type WindowMode = 'solo_madre' | 'window_active' | 'full';

export interface ServiceHealth {
  name: string;
  status: 'up' | 'down';
  enabled_by_default: boolean;
  profile: string;
  port: number;
  health_status: 'healthy' | 'degraded' | 'unhealthy';
  response_time_ms: number;
}

export interface Event {
  id: string;
  timestamp: string; // ISO8601
  severity: Severity;
  module: string;
  correlation_id: string;
  message: string;
  context?: Record<string, any>;
}

export interface EventFilter {
  severity: Severity[];
  modules: string[];
  time_range: {
    from: string; // ISO8601
    to: string;   // ISO8601
  };
}

export interface Datapoint {
  timestamp: string;
  metric_name: string;
  value: number;
  tags?: Record<string, string>;
}

export interface Lane {
  lane_id: string;
  stage: LaneStage;
  status: LaneStatus;
  severity: Severity;
  check_count: number;
  checks_passed: number;
  created_at: string;
  updated_at: string;
}

export interface LaneDetails extends Lane {
  history: LaneStateTransition[];
  checks: Check[];
  audit_findings: AuditFinding[];
  related_events: Event[];
}

export interface Check {
  check_id: string;
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration_ms: number;
  error_message?: string;
}

export interface AuditFinding {
  finding_id: string;
  severity: Severity;
  category: string;
  message: string;
  remediation?: string;
}

export interface LaneStateTransition {
  from_stage: LaneStage;
  to_stage: LaneStage;
  timestamp: string;
  duration_ms: number;
}

export interface FileSystemItem {
  name: string;
  type: 'file' | 'directory';
  size: number;
  modified: string; // ISO8601
}

export interface StatusData {
  mode: WindowMode;
  ttl_remaining_ms: number | null;
  health: Health;
  request_id: string;
  route_taken: string;
  policy: string;
}

export interface MetricsSnapshot {
  cpu: number;
  memory: number; // MB
  db_size: number; // bytes
  error_rate: number; // 0-1
  timestamp: string;
}

export interface ApiResponse<T> {
  ok: boolean;
  data?: T;
  error?: string;
  timestamp: string;
  request_id?: string;
}
```

---

## 2. Zustand Stores

### OperatorStore (Global State)

```typescript
// stores/operatorStore.ts
import { create } from 'zustand';
import { StatusData, Health, WindowMode } from '../services/types';

interface OperatorState {
  // State
  mode: WindowMode;
  ttl_remaining_ms: number | null;
  health: Health;
  request_id: string;
  route_taken: string;
  last_updated: string;

  // Actions
  setMode: (mode: WindowMode) => void;
  setTTL: (ms: number | null) => void;
  setHealth: (health: Health) => void;
  setRequestMetadata: (id: string, route: string) => void;
  updateFromStatus: (status: StatusData) => void;
}

export const useOperatorStore = create<OperatorState>((set) => ({
  mode: 'solo_madre',
  ttl_remaining_ms: null,
  health: 'ok',
  request_id: '',
  route_taken: '',
  last_updated: new Date().toISOString(),

  setMode: (mode) => set({ mode }),
  setTTL: (ms) => set({ ttl_remaining_ms: ms }),
  setHealth: (health) => set({ health }),
  setRequestMetadata: (id, route) => set({ request_id: id, route_taken: route }),
  updateFromStatus: (status) => set({
    mode: status.mode,
    ttl_remaining_ms: status.ttl_remaining_ms,
    health: status.health,
    request_id: status.request_id,
    route_taken: status.route_taken,
    last_updated: new Date().toISOString(),
  }),
}));
```

### EventsStore

```typescript
// stores/eventsStore.ts
import { create } from 'zustand';
import { Event, EventFilter, Severity } from '../services/types';

interface EventsState {
  // State
  events: Event[];
  filters: EventFilter;
  is_streaming: boolean;
  stream_enabled: boolean;
  loading: boolean;
  error: string | null;

  // Actions
  addEvent: (event: Event) => void;
  setFilters: (filters: Partial<EventFilter>) => void;
  setSeverityFilter: (severities: Severity[]) => void;
  setModuleFilter: (modules: string[]) => void;
  setTimeRange: (from: string, to: string) => void;
  clearFilters: () => void;
  startStream: () => void;
  stopStream: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setEvents: (events: Event[]) => void;
}

const DEFAULT_FILTER: EventFilter = {
  severity: ['critical', 'error', 'warn'],
  modules: [],
  time_range: {
    from: new Date(Date.now() - 3600000).toISOString(), // Last 1 hour
    to: new Date().toISOString(),
  },
};

export const useEventsStore = create<EventsState>((set) => ({
  events: [],
  filters: DEFAULT_FILTER,
  is_streaming: false,
  stream_enabled: true,
  loading: false,
  error: null,

  addEvent: (event) => set((state) => ({
    events: [event, ...state.events].slice(0, 10000), // Keep last 10k
  })),
  
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters },
  })),
  
  setSeverityFilter: (severities) => set((state) => ({
    filters: { ...state.filters, severity: severities },
  })),
  
  setModuleFilter: (modules) => set((state) => ({
    filters: { ...state.filters, modules },
  })),
  
  setTimeRange: (from, to) => set((state) => ({
    filters: { ...state.filters, time_range: { from, to } },
  })),
  
  clearFilters: () => set({ filters: DEFAULT_FILTER }),
  startStream: () => set({ is_streaming: true }),
  stopStream: () => set({ is_streaming: false }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setEvents: (events) => set({ events }),
}));
```

### MetricsStore

```typescript
// stores/metricsStore.ts
import { create } from 'zustand';
import { Datapoint } from '../services/types';

type TimeWindow = '1h' | '6h' | '24h' | '7d' | '30d';
type Aggregation = 'avg' | 'max' | 'min' | 'p50' | 'p95' | 'p99';

interface MetricsState {
  datapoints: Datapoint[];
  time_window: TimeWindow;
  selected_metrics: string[];
  aggregation: Aggregation;
  loading: boolean;
  error: string | null;

  setTimeWindow: (window: TimeWindow) => void;
  setSelectedMetrics: (metrics: string[]) => void;
  setAggregation: (agg: Aggregation) => void;
  setDatapoints: (points: Datapoint[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useMetricsStore = create<MetricsState>((set) => ({
  datapoints: [],
  time_window: '24h',
  selected_metrics: ['cpu_utilization', 'memory_usage'],
  aggregation: 'avg',
  loading: false,
  error: null,

  setTimeWindow: (window) => set({ time_window: window }),
  setSelectedMetrics: (metrics) => set({ selected_metrics: metrics }),
  setAggregation: (agg) => set({ aggregation: agg }),
  setDatapoints: (points) => set({ datapoints: points }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));
```

---

## 3. Custom Hooks

### useWindowStatus (Poll /api/status)

```typescript
// hooks/useWindowStatus.ts
import { useEffect } from 'react';
import { useOperatorStore } from '../stores/operatorStore';
import { apiClient } from '../services/api';

export function useWindowStatus(pollInterval = 5000) {
  const updateFromStatus = useOperatorStore(s => s.updateFromStatus);

  useEffect(() => {
    let mounted = true;
    let timeoutId: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const resp = await apiClient.status();
        if (mounted && resp.ok && resp.data) {
          updateFromStatus(resp.data);
        }
      } catch (err) {
        console.error('Failed to poll status:', err);
      }

      if (mounted) {
        timeoutId = setTimeout(poll, pollInterval);
      }
    }

    // Initial poll
    poll();

    return () => {
      mounted = false;
      clearTimeout(timeoutId);
    };
  }, [pollInterval, updateFromStatus]);
}
```

### useEventStream (SSE with Fallback)

```typescript
// hooks/useEventStream.ts
import { useEffect } from 'react';
import { useEventsStore } from '../stores/eventsStore';
import { Event } from '../services/types';

export function useEventStream(pollFallbackMs = 5000) {
  const { addEvent, startStream, stopStream, setError } = useEventsStore();

  useEffect(() => {
    let mounted = true;
    let eventSource: EventSource | null = null;
    let pollTimeoutId: ReturnType<typeof setTimeout>;

    function setupSSE() {
      try {
        eventSource = new EventSource('/operator/api/events/stream');

        eventSource.addEventListener('event', (e) => {
          if (mounted) {
            const event: Event = JSON.parse(e.data);
            addEvent(event);
          }
        });

        eventSource.addEventListener('error', () => {
          console.warn('SSE error, falling back to polling');
          eventSource?.close();
          fallbackToPolling();
        });

        startStream();
      } catch (err) {
        console.warn('SSE not supported, using polling');
        fallbackToPolling();
      }
    }

    async function fallbackToPolling() {
      try {
        const resp = await fetch('/operator/api/events?limit=50');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        
        const data = await resp.json();
        if (mounted && data.ok && data.data?.events) {
          data.data.events.forEach((evt: Event) => addEvent(evt));
        }
      } catch (err) {
        setError((err as Error).message);
      }

      if (mounted) {
        pollTimeoutId = setTimeout(fallbackToPolling, pollFallbackMs);
      }
    }

    setupSSE();

    return () => {
      mounted = false;
      stopStream();
      eventSource?.close();
      clearTimeout(pollTimeoutId);
    };
  }, [addEvent, startStream, stopStream, setError, pollFallbackMs]);
}
```

---

## 4. Components

### WindowStatusBar Component

```typescript
// components/windows/WindowStatusBar.tsx
import { useOperatorStore } from '../../stores/operatorStore';
import { ModeIndicator } from './ModeIndicator';
import { HealthStatus } from './HealthStatus';
import { TTLCountdown } from './TTLCountdown';
import { RequestMetadata } from './RequestMetadata';

export function WindowStatusBar() {
  const { mode, health, ttl_remaining_ms, request_id, route_taken } = useOperatorStore();

  return (
    <div className="sticky top-0 z-50 flex justify-between items-center px-4 py-2 bg-slate-900 border-b border-slate-700 shadow-lg">
      <div className="flex items-center gap-4">
        <ModeIndicator mode={mode} />
        <HealthStatus health={health} />
        {ttl_remaining_ms && <TTLCountdown ms={ttl_remaining_ms} />}
      </div>

      <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
        <RequestMetadata request_id={request_id} route_taken={route_taken} />
      </div>
    </div>
  );
}
```

### EventsPanel Component

```typescript
// components/events/EventsPanel.tsx
import { useEffect, useState } from 'react';
import { useEventsStore } from '../../stores/eventsStore';
import { useEventStream } from '../../hooks/useEventStream';
import { EventFilters } from './EventFilters';
import { EventTable } from './EventTable';
import { Event } from '../../services/types';

export function EventsPanel() {
  const { events, filters, loading, error, setFilters } = useEventsStore();
  useEventStream(); // Start SSE or polling

  // Filter events locally
  const filtered = events.filter(evt => {
    const severityMatch = filters.severity.includes(evt.severity);
    const moduleMatch = filters.modules.length === 0 || filters.modules.includes(evt.module);
    const timeMatch =
      new Date(evt.timestamp) >= new Date(filters.time_range.from) &&
      new Date(evt.timestamp) <= new Date(filters.time_range.to);

    return severityMatch && moduleMatch && timeMatch;
  });

  if (loading && events.length === 0) {
    return <div className="p-6 text-slate-400">⟳ Loading events...</div>;
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <EventFilters
        filters={filters}
        onFilterChange={setFilters}
      />

      {error && (
        <div className="p-3 bg-rose-900/30 border border-rose-600 rounded text-rose-200 text-sm">
          ⚠️ {error}
        </div>
      )}

      <div className="flex-1 overflow-auto">
        <EventTable events={filtered} />
      </div>

      <div className="text-xs text-slate-400 px-4">
        Showing {filtered.length} of {events.length} events
      </div>
    </div>
  );
}
```

### MetricsPanel with Recharts

```typescript
// components/metrics/MetricsPanel.tsx
import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { useMetricsStore } from '../../stores/metricsStore';
import { apiClient } from '../../services/api';
import { MetricsControls } from './MetricsControls';

export function MetricsPanel() {
  const { datapoints, time_window, selected_metrics, aggregation, setDatapoints, setLoading } = useMetricsStore();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMetrics();
  }, [time_window, selected_metrics, aggregation]);

  async function loadMetrics() {
    setLoading(true);
    setError(null);

    try {
      const resp = await apiClient.metrics({
        window: time_window,
        metrics: selected_metrics,
        aggregation,
      });

      if (resp.ok && resp.data?.datapoints) {
        setDatapoints(resp.data.datapoints);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  // Group datapoints by timestamp for Recharts
  const grouped: Record<string, any> = {};
  datapoints.forEach(dp => {
    if (!grouped[dp.timestamp]) grouped[dp.timestamp] = { timestamp: dp.timestamp };
    grouped[dp.timestamp][dp.metric_name] = dp.value;
  });

  const chartData = Object.values(grouped);

  return (
    <div className="flex flex-col gap-4 h-full">
      <MetricsControls />

      {error && (
        <div className="p-3 bg-rose-900/30 border border-rose-600 rounded text-rose-200 text-sm">
          ⚠️ {error}
        </div>
      )}

      <div className="flex-1 bg-slate-800 rounded-lg p-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="timestamp"
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              tickFormatter={(ts) => new Date(ts).toLocaleTimeString()}
            />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
                color: '#e2e8f0',
              }}
            />
            <Legend />
            {selected_metrics.map((metric, idx) => (
              <Line
                key={metric}
                type="monotone"
                dataKey={metric}
                stroke={`hsl(${idx * 60}, 70%, 60%)`}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
```

### RailsPanel Component

```typescript
// components/rails/RailsPanel.tsx
import { useEffect, useState } from 'react';
import { useRailsStore } from '../../stores/railsStore';
import { apiClient } from '../../services/api';
import { RailsGrid } from './RailsGrid';
import { LaneDetail } from './LaneDetail';

export function RailsPanel() {
  const { lanes, selected_lane_id, selectLane } = useRailsStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadLanes();
    const interval = setInterval(loadLanes, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  async function loadLanes() {
    try {
      const resp = await apiClient.rails.lanes();
      if (resp.ok && resp.data?.lanes) {
        // Update store with new lanes
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-4 h-full">
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="p-6 text-slate-400">⟳ Loading lanes...</div>
        ) : error ? (
          <div className="p-3 bg-rose-900/30 border border-rose-600 rounded text-rose-200">
            ⚠️ {error}
          </div>
        ) : (
          <RailsGrid lanes={lanes} onSelectLane={selectLane} />
        )}
      </div>

      {selected_lane_id && (
        <div className="w-96 border-l border-slate-700 pl-4 overflow-auto">
          <LaneDetail lane_id={selected_lane_id} />
        </div>
      )}
    </div>
  );
}
```

---

## 5. Tailwind CSS Utilities

### Severity Color Mapping

```typescript
// utils/colors.ts
import { Severity } from '../services/types';

export const SEVERITY_COLORS: Record<Severity, string> = {
  critical: 'text-rose-500 bg-rose-900/20 border-rose-600',
  error: 'text-rose-400 bg-rose-900/10 border-rose-500',
  warn: 'text-amber-400 bg-amber-900/10 border-amber-500',
  info: 'text-blue-400 bg-blue-900/10 border-blue-500',
  debug: 'text-slate-400 bg-slate-900/10 border-slate-600',
};

export const SEVERITY_DOT_COLORS: Record<Severity, string> = {
  critical: 'bg-rose-500',
  error: 'bg-rose-500',
  warn: 'bg-amber-500',
  info: 'bg-blue-500',
  debug: 'bg-slate-400',
};

export function getSeverityClass(severity: Severity): string {
  return SEVERITY_COLORS[severity];
}

export function getSeverityDot(severity: Severity): string {
  return SEVERITY_DOT_COLORS[severity];
}
```

### Formatting Utilities

```typescript
// utils/formatting.ts
export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIdx = 0;

  while (size > 1024 && unitIdx < units.length - 1) {
    size /= 1024;
    unitIdx++;
  }

  return `${size.toFixed(2)} ${units[unitIdx]}`;
}

export function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

export function truncate(text: string, maxLen: number): string {
  return text.length > maxLen ? `${text.slice(0, maxLen - 3)}...` : text;
}
```

---

## 6. Error Handling & Loading States

### Error Boundary

```typescript
// components/common/ErrorBoundary.tsx
import { ReactNode, Component, ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen bg-slate-950">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-bold text-rose-500">Something went wrong</h1>
            <p className="text-slate-400">{this.state.error?.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Toast Notifications

```typescript
// components/common/Toast.tsx
import { useEffect } from 'react';

interface ToastProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  onClose?: () => void;
}

export function Toast({ type, message, duration = 5000, onClose }: ToastProps) {
  useEffect(() => {
    if (duration > 0 && onClose) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const colorClasses = {
    success: 'bg-emerald-900/80 border-emerald-600 text-emerald-100',
    error: 'bg-rose-900/80 border-rose-600 text-rose-100',
    warning: 'bg-amber-900/80 border-amber-600 text-amber-100',
    info: 'bg-blue-900/80 border-blue-600 text-blue-100',
  };

  return (
    <div className={`fixed bottom-4 right-4 max-w-sm px-4 py-3 rounded border backdrop-blur-sm ${colorClasses[type]}`}>
      {message}
    </div>
  );
}
```

---

## 7. Key Implementation Notes

### State Management Patterns

1. **Zustand for global state**: Lightweight, no boilerplate, ideal for shared UI state
2. **Component-level state**: Use `useState` for ephemeral UI state (filters, expanded items, etc.)
3. **React Query for server state**: Cache API responses, handle stale data automatically

### API Integration Strategy

1. **Entrypoint**: All calls go through `/operator/api/*` (proxied via tentaculo_link:8000)
2. **Error handling**: Normalize all API errors to `ApiResponse<T>` format
3. **Retry logic**: Implement exponential backoff for transient failures
4. **Caching**: Use React Query's built-in cache with 30s default stale time

### Performance Optimization

1. **Virtual scrolling**: Use `react-window` for large event lists (1000+ rows)
2. **Memoization**: Use `React.memo` for expensive components
3. **Lazy loading**: Code-split views with `React.lazy` + `Suspense`
4. **Image optimization**: Compress SVGs, use CSS for icons

### Accessibility (WCAG 2.1 AA)

1. **Contrast**: All text ≥ 4.5:1 ratio
2. **Keyboard navigation**: Tab through all interactive elements
3. **ARIA labels**: Add `aria-label`, `aria-describedby` to complex widgets
4. **Focus management**: Visible focus indicators on all buttons

---

## 8. Testing Examples

### Unit Test (EventsStore)

```typescript
// __tests__/stores/eventsStore.test.ts
import { renderHook, act } from '@testing-library/react';
import { useEventsStore } from '../../stores/eventsStore';
import { Event } from '../../services/types';

describe('EventsStore', () => {
  beforeEach(() => {
    useEventsStore.setState({
      events: [],
      filters: { severity: ['critical', 'error'], modules: [], time_range: { from: '', to: '' } },
    });
  });

  it('should add event', () => {
    const { result } = renderHook(() => useEventsStore());
    const event: Event = {
      id: '1',
      timestamp: new Date().toISOString(),
      severity: 'critical',
      module: 'madre',
      correlation_id: 'corr-123',
      message: 'Test event',
    };

    act(() => {
      result.current.addEvent(event);
    });

    expect(result.current.events).toHaveLength(1);
    expect(result.current.events[0]).toEqual(event);
  });

  it('should filter by severity', () => {
    const { result } = renderHook(() => useEventsStore());

    act(() => {
      result.current.setSeverityFilter(['error']);
    });

    expect(result.current.filters.severity).toEqual(['error']);
  });
});
```

### Component Test (EventsPanel)

```typescript
// __tests__/components/events/EventsPanel.test.tsx
import { render, screen } from '@testing-library/react';
import { EventsPanel } from '../../../components/events/EventsPanel';
import { useEventStream } from '../../../hooks/useEventStream';

jest.mock('../../../hooks/useEventStream');

describe('EventsPanel', () => {
  it('should render loading state', () => {
    render(<EventsPanel />);
    expect(screen.getByText(/Loading events/i)).toBeInTheDocument();
  });

  it('should render error state', () => {
    render(<EventsPanel />);
    useEventsStore.setState({ error: 'API Error', loading: false });
    expect(screen.getByText(/API Error/i)).toBeInTheDocument();
  });
});
```

---

## 9. Deployment Configuration

### package.json Scripts

```json
{
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 5173",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:cov": "vitest --coverage",
    "lint": "eslint src --ext .ts,.tsx",
    "type-check": "tsc --noEmit",
    "analyze": "ANALYZE=true npm run build"
  }
}
```

### Dockerfile

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY src ./src
COPY *.config.* ./
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 8020
CMD ["serve", "-s", "dist", "-l", "8020"]
```

---

This document provides all the building blocks needed to implement the PHASE 4 Operator UI with proper architecture, type safety, state management, and component organization.

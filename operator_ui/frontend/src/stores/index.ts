/**
 * VX11 Operator Frontend - Zustand Store Architecture
 * operator/frontend/src/stores/index.ts
 *
 * Central state management using Zustand
 * Single source of truth for all UI state
 */

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

// ============================================================================
// TYPE DEFINITIONS (Canonical)
// ============================================================================

export interface VX11Event {
  event_id: string
  event_type: string
  summary: string
  module: string
  severity: 'critical' | 'error' | 'warn' | 'info'
  correlation_id: string
  payload: Record<string, unknown>
  created_at: string
}

export interface Metric {
  metric_id: string
  metric_name: string
  value: number
  module: string
  unit: string
  timestamp: string
  dimensions?: Record<string, string>
}

export interface RailsLane {
  lane_id: string
  name: string
  description: string
  stage: 'detect' | 'plan' | 'validate' | 'apply'
  checks: Check[]
  created_at: string
}

export interface Check {
  check_id: string
  name: string
  timeout_seconds: number
}

export interface Rail {
  rail_id: string
  name: string
  description: string
  rule_type: string
  severity_on_violation: 'critical' | 'error' | 'warn'
  active: boolean
}

export interface WindowStatus {
  mode: 'solo_madre' | 'window_active' | 'degraded'
  health: 'ok' | 'degraded' | 'offline'
  ttl_seconds?: number
  madre_status: string
  redis_status: string
  tentaculo_status: string
  request_id?: string
  route_taken?: string
}

// ============================================================================
// ZUSTAND STORES
// ============================================================================

/**
 * OperatorStore - Main app state
 */
interface OperatorState {
  degraded: boolean
  setDegraded: (d: boolean) => void
  activeTab: string
  setActiveTab: (tab: string) => void
}

export const useOperatorStore = create<OperatorState>()(
  devtools(
    (set) => ({
      degraded: false,
      setDegraded: (d) => set({ degraded: d }),
      activeTab: 'overview',
      setActiveTab: (tab) => set({ activeTab: tab }),
    }),
    { name: 'OperatorStore' }
  )
)

/**
 * WindowStatusStore - Window mode + health tracking
 */
interface WindowStatusState {
  windowStatus: WindowStatus | null
  setWindowStatus: (status: WindowStatus) => void
  ttlCountdown: number
  setTtlCountdown: (seconds: number) => void
}

export const useWindowStatusStore = create<WindowStatusState>()(
  devtools(
    (set) => ({
      windowStatus: null,
      setWindowStatus: (status) => set({ windowStatus: status }),
      ttlCountdown: 0,
      setTtlCountdown: (seconds) => set({ ttlCountdown: seconds }),
    }),
    { name: 'WindowStatusStore' }
  )
)

/**
 * EventsStore - Event stream + filtering
 */
interface EventsState {
  events: VX11Event[]
  setEvents: (events: VX11Event[]) => void
  addEvent: (event: VX11Event) => void
  filterSeverity: 'all' | 'critical' | 'error' | 'warn' | 'info'
  setFilterSeverity: (severity: any) => void
  filterModule: string
  setFilterModule: (module: string) => void
  loading: boolean
  setLoading: (loading: boolean) => void
  error: string | null
  setError: (error: string | null) => void
}

export const useEventsStore = create<EventsState>()(
  devtools(
    (set) => ({
      events: [],
      setEvents: (events) => set({ events }),
      addEvent: (event) =>
        set((state) => ({
          events: [event, ...state.events].slice(0, 1000), // Keep last 1000
        })),
      filterSeverity: 'all',
      setFilterSeverity: (severity) => set({ filterSeverity: severity }),
      filterModule: '',
      setFilterModule: (module) => set({ filterModule: module }),
      loading: false,
      setLoading: (loading) => set({ loading }),
      error: null,
      setError: (error) => set({ error }),
    }),
    { name: 'EventsStore' }
  )
)

/**
 * MetricsStore - Timeseries metrics tracking
 */
interface MetricsState {
  metrics: Metric[]
  setMetrics: (metrics: Metric[]) => void
  selectedMetrics: string[]
  toggleMetric: (metricName: string) => void
  timeWindow: '1h' | '6h' | '24h' | '7d'
  setTimeWindow: (window: '1h' | '6h' | '24h' | '7d') => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

export const useMetricsStore = create<MetricsState>()(
  devtools(
    (set) => ({
      metrics: [],
      setMetrics: (metrics) => set({ metrics }),
      selectedMetrics: ['cpu', 'memory'],
      toggleMetric: (metricName) =>
        set((state) => ({
          selectedMetrics: state.selectedMetrics.includes(metricName)
            ? state.selectedMetrics.filter((m) => m !== metricName)
            : [...state.selectedMetrics, metricName],
        })),
      timeWindow: '24h',
      setTimeWindow: (window) => set({ timeWindow: window }),
      loading: false,
      setLoading: (loading) => set({ loading }),
    }),
    { name: 'MetricsStore' }
  )
)

/**
 * RailsStore - Rails + Lanes state
 */
interface RailsState {
  lanes: RailsLane[]
  setLanes: (lanes: RailsLane[]) => void
  rails: Rail[]
  setRails: (rails: Rail[]) => void
  expandedLanes: Set<string>
  toggleLaneExpanded: (laneId: string) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

export const useRailsStore = create<RailsState>()(
  devtools(
    (set) => ({
      lanes: [],
      setLanes: (lanes) => set({ lanes }),
      rails: [],
      setRails: (rails) => set({ rails }),
      expandedLanes: new Set(),
      toggleLaneExpanded: (laneId) =>
        set((state) => {
          const newSet = new Set(state.expandedLanes)
          if (newSet.has(laneId)) {
            newSet.delete(laneId)
          } else {
            newSet.add(laneId)
          }
          return { expandedLanes: newSet }
        }),
      loading: false,
      setLoading: (loading) => set({ loading }),
    }),
    { name: 'RailsStore' }
  )
)

/**
 * OverviewStore - System overview data
 */
interface OverviewState {
  totalEvents: number
  setTotalEvents: (count: number) => void
  activeModules: Record<string, boolean>
  setActiveModules: (modules: Record<string, boolean>) => void
  lastEventTime: string | null
  setLastEventTime: (time: string | null) => void
  activeLanes: number
  setActiveLanes: (count: number) => void
}

export const useOverviewStore = create<OverviewState>()(
  devtools(
    (set) => ({
      totalEvents: 0,
      setTotalEvents: (count) => set({ totalEvents: count }),
      activeModules: {},
      setActiveModules: (modules) => set({ activeModules: modules }),
      lastEventTime: null,
      setLastEventTime: (time) => set({ lastEventTime: time }),
      activeLanes: 0,
      setActiveLanes: (count) => set({ activeLanes: count }),
    }),
    { name: 'OverviewStore' }
  )
)

/**
 * FileExplorerStore - Sandboxed file navigator
 */
interface FileExplorerState {
  currentPath: string
  setCurrentPath: (path: string) => void
  files: string[]
  setFiles: (files: string[]) => void
  whitelistedPaths: string[]
}

export const useFileExplorerStore = create<FileExplorerState>()((set) => ({
  currentPath: '/docs/audit',
  setCurrentPath: (path) => set({ currentPath: path }),
  files: [],
  setFiles: (files) => set({ files }),
  whitelistedPaths: [
    '/docs/audit',
    '/data/runtime',
    '/logs',
    '/build/artifacts',
    '/forensic',
  ],
}))

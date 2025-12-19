import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { BridgeHealth, ChatMessage, SystemStatus, WsEvent } from "../types/api";

const MAX_EVENTS = 400;
const MAX_MESSAGES = 400;

type SystemSlice = {
  status: SystemStatus | null;
  statusError: string | null;
  bridgeHealth: BridgeHealth | null;
  setStatus: (status: SystemStatus | null) => void;
  setStatusError: (error: string | null) => void;
  setBridgeHealth: (health: BridgeHealth | null) => void;
};

type ChatSlice = {
  messages: ChatMessage[];
  appendMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  clearMessages: () => void;
};

type TraceSlice = {
  events: WsEvent[];
  setEvents: (events: WsEvent[]) => void;
  addEvent: (event: WsEvent) => void;
};

type HormigueroSlice = {
  incidents: any[];
  events: WsEvent[];
  setIncidents: (incidents: any[]) => void;
  setEvents: (events: WsEvent[]) => void;
};

type UiSlice = {
  activeTab: string;
  setActiveTab: (tab: string) => void;
};

type OperatorStore = {
  system: SystemSlice;
  chat: ChatSlice;
  traces: TraceSlice;
  hormiguero: HormigueroSlice;
  ui: UiSlice;
};

export const useOperatorStore = create<OperatorStore>()(
  devtools((set) => ({
    system: {
      status: null,
      statusError: null,
      bridgeHealth: null,
      setStatus: (status) => set((state) => ({ system: { ...state.system, status } })),
      setStatusError: (statusError) => set((state) => ({ system: { ...state.system, statusError } })),
      setBridgeHealth: (bridgeHealth) => set((state) => ({ system: { ...state.system, bridgeHealth } })),
    },
    chat: {
      messages: [],
      appendMessage: (message) =>
        set((state) => ({
          chat: { ...state.chat, messages: [...state.chat.messages, message].slice(-MAX_MESSAGES) },
        })),
      setMessages: (messages) => set((state) => ({ chat: { ...state.chat, messages: messages.slice(-MAX_MESSAGES) } })),
      clearMessages: () => set((state) => ({ chat: { ...state.chat, messages: [] } })),
    },
    traces: {
      events: [],
      setEvents: (events) => set((state) => ({ traces: { ...state.traces, events: events.slice(0, MAX_EVENTS) } })),
      addEvent: (event) =>
        set((state) => ({
          traces: { ...state.traces, events: [event, ...state.traces.events].slice(0, MAX_EVENTS) },
        })),
    },
    hormiguero: {
      incidents: [],
      events: [],
      setIncidents: (incidents) => set((state) => ({ hormiguero: { ...state.hormiguero, incidents } })),
      setEvents: (events) => set((state) => ({ hormiguero: { ...state.hormiguero, events: events.slice(0, MAX_EVENTS) } })),
    },
    ui: {
      activeTab: "dashboard",
      setActiveTab: (tab) => set((state) => ({ ui: { ...state.ui, activeTab: tab } })),
    },
  }))
);

export const selectSystem = (state: OperatorStore) => state.system;
export const selectChat = (state: OperatorStore) => state.chat;
export const selectTraces = (state: OperatorStore) => state.traces;
export const selectHormiguero = (state: OperatorStore) => state.hormiguero;
export const selectUi = (state: OperatorStore) => state.ui;

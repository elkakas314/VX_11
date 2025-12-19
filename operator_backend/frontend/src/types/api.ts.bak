// Tipos base para endpoints confirmados. Ajustar/afinar cuando se conozca el contrato exacto.
export type SystemStatus = {
  ok?: boolean;
  modules?: Record<string, any>;
  modules_list?: any[];
  summary?: string;
  [key: string]: any;
};

export type BridgeHealth = {
  ok?: boolean;
  playwright?: boolean;
  chromium?: boolean;
  error?: string;
};

export type WsEvent = {
  type?: string;
  payload?: any;
  data?: any;
  module?: string;
  level?: string;
  timestamp?: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  trace?: Record<string, any>;
  latency_ms?: number;
  intent?: string;
};

export type ManifestValidationResult = {
  ok?: boolean;
  errors?: string[];
  warnings?: string[];
  summary?: string;
  data?: any;
};

export type PatchPlanResult = {
  ok?: boolean;
  summary?: string;
  data?: any[];
  error?: string;
};

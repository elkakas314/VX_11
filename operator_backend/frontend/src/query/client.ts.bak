import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5_000,
      gcTime: 60_000,
      refetchOnWindowFocus: false,
      retry: 2,
    },
    mutations: {
      retry: 1,
    },
  },
});

export const queryKeys = {
  systemStatus: ["systemStatus"] as const,
  bridgeHealth: ["bridgeHealth"] as const,
  hormigueroIncidents: ["hormigueroIncidents"] as const,
  shubDashboard: ["shubDashboard"] as const,
  manifestator: {
    validate: ["manifestator", "validate"] as const,
    patchPlan: ["manifestator", "patchPlan"] as const,
    apply: ["manifestator", "apply"] as const,
  },
  chatSession: (sessionId: string) => ["chatSession", sessionId] as const,
};

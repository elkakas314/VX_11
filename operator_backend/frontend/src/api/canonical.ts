/**
 * Canonical API client for VX11 Operator Backend v7
 * Handles JWT auth, policy gating, and all canonical /api/* endpoints
 */

import {
    AuthToken,
    OperatorStatus,
    AuditLog,
    OperatorJob,
    SystemEvent,
    ChatResponse
} from "../types/canonical";

const API_BASE = import.meta.env.VITE_OPERATOR_BASE_URL || "http://127.0.0.1:8000";

let currentToken: string | null = null;let currentCsrfToken: string | null = null;
// Load token from localStorage on app start
export function initializeAuth() {
    currentToken = localStorage.getItem("vx11_jwt_token");
    currentCsrfToken = localStorage.getItem("vx11_csrf_token");
}

// Save token to localStorage
function saveToken(token: string) {
    currentToken = token;
    localStorage.setItem("vx11_jwt_token", token);
}

// Clear token and CSRF token
export function clearAuth() {
    currentToken = null;
    currentCsrfToken = null;
    localStorage.removeItem("vx11_jwt_token");
    localStorage.removeItem("vx11_csrf_token");
}

// Get current token
export function getToken(): string | null {
    return currentToken;
}

// Helper: make authenticated fetch
async function fetchAPI<T>(
    path: string,
    options: RequestInit = {}
): Promise<T | { error: string; status?: number }> {
    const url = `${API_BASE}${path}`;
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string> || {}),
    };

    if (currentToken) {
        headers["Authorization"] = `Bearer ${currentToken}`;
    }

    // Add CSRF token for POST/PUT/DELETE requests
    if (currentCsrfToken && options.method && ["POST", "PUT", "DELETE"].includes(options.method)) {
        headers["X-CSRF-Token"] = currentCsrfToken;
    }

    try {
        const response = await fetch(url, { ...options, headers });
        const data = await response.json();

        if (!response.ok) {
            return {
                error: data?.detail || data?.error || `HTTP ${response.status}`,
                status: response.status,
            };
        }

        return data as T;
    } catch (err) {
        return { error: `Network error: ${err}` };
    }
}

// ===================== AUTH ENDPOINTS =====================

export async function login(username: string, password: string): Promise<AuthToken | { error: string }> {
    const result = await fetchAPI<AuthToken>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
    });

    if ("error" in result) {
        return result;
    }

    // Save tokens on successful login
    if (result.access_token) {
        saveToken(result.access_token);
        if (result.csrf_token) {
            currentCsrfToken = result.csrf_token;
            localStorage.setItem("vx11_csrf_token", result.csrf_token);
        }
    }

    return result;
}

export async function logout(): Promise<{ ok: boolean } | { error: string }> {
    const result = await fetchAPI<{ ok: boolean }>("/auth/logout", { method: "POST" });
    if (!("error" in result)) {
        clearAuth();
    }
    return result;
}

export async function verifyToken(): Promise<{ valid: boolean; user_id?: string; mode?: string } | { error: string }> {
    return fetchAPI("/auth/verify", { method: "POST" });
}

// ===================== CORE ENDPOINTS =====================

export async function getStatus(): Promise<OperatorStatus | { error: string; status?: number }> {
    return fetchAPI<OperatorStatus>("/api/status");
}

export async function getModules(): Promise<{ modules: any[] } | { error: string }> {
    return fetchAPI<{ modules: any[] }>("/api/modules");
}

// ===================== AUDIT ENDPOINTS =====================

export async function listAuditLogs(
    skip: number = 0,
    limit: number = 50,
    status?: string,
    level?: string
): Promise<{ logs: AuditLog[]; total: number } | { error: string }> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (status) params.append("status", status);
    if (level) params.append("level", level);
    return fetchAPI(`/api/audit?${params}`);
}

export async function getAuditDetail(id: string): Promise<AuditLog | { error: string }> {
    return fetchAPI(`/api/audit/${id}`);
}

export async function downloadAuditCSV(id: string): Promise<Blob | { error: string }> {
    const url = `${API_BASE}/api/audit/${id}/download`;
    const headers: Record<string, string> = {};
    if (currentToken) {
        headers["Authorization"] = `Bearer ${currentToken}`;
    }

    try {
        const response = await fetch(url, { headers });
        if (!response.ok) {
            const data = await response.json();
            return { error: data?.detail || `HTTP ${response.status}` };
        }
        return response.blob();
    } catch (err) {
        return { error: `Network error: ${err}` };
    }
}

// ===================== POWER ENDPOINTS =====================

export async function restartModule(name: string): Promise<{ status: string } | { error: string }> {
    return fetchAPI(`/api/module/${name}/restart`, { method: "POST" });
}

export async function powerUpModule(name: string): Promise<{ status: string } | { error: string }> {
    return fetchAPI(`/api/module/${name}/power_up`, { method: "POST" });
}

export async function powerDownModule(name: string): Promise<{ status: string } | { error: string }> {
    return fetchAPI(`/api/module/${name}/power_down`, { method: "POST" });
}

// ===================== JOBS ENDPOINTS =====================

export async function listJobs(
    skip: number = 0,
    limit: number = 50,
    status?: string
): Promise<{ jobs: OperatorJob[]; total: number } | { error: string }> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (status) params.append("status", status);
    return fetchAPI(`/api/jobs?${params}`);
}

export async function getJobDetail(id: string): Promise<OperatorJob | { error: string }> {
    return fetchAPI(`/api/jobs/${id}`);
}

// ===================== EVENTS (SSE) =====================

export function subscribeToEvents(
    onEvent: (event: SystemEvent) => void,
    onError?: (error: string) => void,
    onClose?: () => void
): EventSource | null {
    const url = `${API_BASE}/api/events`;
    const headers: HeadersInit = {};
    if (currentToken) {
        headers["Authorization"] = `Bearer ${currentToken}`;
    }

    try {
        const eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onEvent(data);
            } catch (err) {
                if (onError) onError(`Parse error: ${err}`);
            }
        };

        eventSource.onerror = () => {
            if (onError) onError("EventSource connection error");
            if (onClose) onClose();
        };

        return eventSource;
    } catch (err) {
        if (onError) onError(`Failed to subscribe: ${err}`);
        return null;
    }
}

// ===================== CHAT ENDPOINT =====================

export async function sendChat(message: string, mode?: string): Promise<ChatResponse | { error: string }> {
    return fetchAPI<ChatResponse>("/api/chat", {
        method: "POST",
        body: JSON.stringify({ message, mode }),
    });
}

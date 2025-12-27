import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || `${OPERATOR_BASE_URL}`;

const client = axios.create({
    baseURL: API_BASE,
    headers: {
        'X-VX11-Token': import.meta.env.VITE_API_TOKEN || 'default',
    },
});

const safeCall = async (promise) => {
    try {
        return await promise;
    } catch (err) {
        return { data: { status: 'service_offline', error: err.message } };
    }
};

export const operatorApi = {
    // Chat
    postChat: (sessionId, message, metadata = {}) =>
        safeCall(client.post('/operator/chat', { session_id: sessionId, message, metadata })),

    // Sessions
    getSession: (sessionId) => safeCall(client.get(`/operator/session/${sessionId}`)),

    // System
    getVx11Overview: () => safeCall(client.get('/operator/vx11/overview')),

    // Shub
    getShubDashboard: () => safeCall(client.get('/operator/shub/dashboard')),

    // Resources
    getResources: () => safeCall(client.get('/operator/resources')),

    // Browser
    postBrowserTask: (url, sessionId) =>
        safeCall(client.post('/operator/browser/task', { url, session_id: sessionId })),
    getBrowserTaskStatus: (taskId) =>
        safeCall(client.get(`/operator/browser/task/${taskId}`)),
};

export default client;

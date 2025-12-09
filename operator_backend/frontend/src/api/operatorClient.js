import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const client = axios.create({
    baseURL: API_BASE,
    headers: {
        'X-VX11-Token': import.meta.env.VITE_API_TOKEN || 'default',
    },
});

export const operatorApi = {
    // Chat
    postChat: (sessionId, message, metadata = {}) =>
        client.post('/operator/chat', { session_id: sessionId, message, metadata }),

    // Sessions
    getSession: (sessionId) => client.get(`/operator/session/${sessionId}`),

    // System
    getVx11Overview: () => client.get('/operator/vx11/overview'),

    // Shub
    getShubDashboard: () => client.get('/operator/shub/dashboard'),

    // Resources
    getResources: () => client.get('/operator/resources'),

    // Browser
    postBrowserTask: (url, sessionId) =>
        client.post('/operator/browser/task', { url, session_id: sessionId }),
    getBrowserTaskStatus: (taskId) =>
        client.get(`/operator/browser/task/${taskId}`),
};

export default client;

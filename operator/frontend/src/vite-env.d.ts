/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_BASE?: string
    readonly VITE_API_TIMEOUT?: string
    readonly VITE_API_RETRIES?: string
    readonly VITE_BACKEND_URL?: string
    readonly VITE_MADRE_URL?: string
    readonly VITE_TENTACULO_URL?: string
    readonly VITE_MOCK_MODE?: string
    readonly DEV?: boolean
    readonly PROD?: boolean
    readonly SSR?: boolean
}

interface ImportMeta {
    readonly env: ImportMetaEnv

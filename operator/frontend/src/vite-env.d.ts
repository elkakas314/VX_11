/// <reference types="vite/client" />
/// <reference types="vitest/globals" />
/// <reference types="node" />

declare module 'vite/client' {
    interface ImportMetaEnv {
        readonly VITE_API_BASE?: string
    }
    interface ImportMeta {
        readonly env: ImportMetaEnv
    }
}

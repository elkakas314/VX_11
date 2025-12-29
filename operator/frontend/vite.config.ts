import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    base: '/operator/ui/',
    server: {
        host: '0.0.0.0',
        port: 3000,
        proxy: {
            // Dev proxy: /operator/api/* routes to tentaculo_link:8000
            '^/operator/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                rewrite: (path) => path, // Keep /operator/api intact; tentaculo_link handles it
            },
        },
    },
    build: {
        outDir: 'dist',
        sourcemap: false,
    },
    define: {
        // Allow runtime env var VITE_VX11_API_BASE_URL (default empty = relative)
        'import.meta.env.VITE_VX11_API_BASE_URL': JSON.stringify(process.env.VITE_VX11_API_BASE_URL ?? ''),
    },
})

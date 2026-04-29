import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// API_TARGET_URL is a build/server-side env var (not exposed to the browser).
// In Docker it is set to http://api:8000 (internal Docker network).
// In local dev it defaults to http://localhost:8000.
// The browser always calls /api/* — Vite proxies those requests here.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.API_TARGET_URL || 'http://localhost:8000'

  return {
    plugins: [react()],
    server: {
      port: 3000,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})

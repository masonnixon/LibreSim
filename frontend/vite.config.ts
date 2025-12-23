import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Use backend service name in Docker, localhost for local dev
const backendUrl = process.env.VITE_BACKEND_URL || 'http://backend:9000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 4200,
    host: true,
    allowedHosts: ['irongiant.tail7d452.ts.net'],
    watch: {
      // Use polling for Docker on Windows (file system events don't propagate reliably)
      usePolling: true,
      interval: 1000,
    },
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/ws': {
        target: backendUrl.replace('http', 'ws'),
        ws: true,
      },
    },
  },
})

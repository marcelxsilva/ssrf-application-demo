import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// O alvo do proxy é configurável: no Docker aponta para o serviço "backend";
// rodando localmente (fora do Docker), use VITE_API_TARGET=http://localhost:8000.
const target = process.env.VITE_API_TARGET || 'http://backend:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
})

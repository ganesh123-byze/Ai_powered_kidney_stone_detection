import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const parsedPort = Number(env.VITE_DEV_PORT)
  const devPort = Number.isFinite(parsedPort) && parsedPort > 0 ? parsedPort : undefined

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      // No hardcoded port: use VITE_DEV_PORT if provided, else Vite default/next free port.
      port: devPort,
      strictPort: false,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})

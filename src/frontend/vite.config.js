import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 10010,
    proxy: {
      '/api': {
        target: 'http://localhost:10012',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:10012',
        ws: true
      }
    }
  }
})

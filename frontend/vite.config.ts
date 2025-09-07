import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite';
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [react(), tailwindcss(), VitePWA({
    registerType: 'autoUpdate',
    injectRegister: 'auto',
    devOptions: {
      enabled: true,
    },
    manifest: {
      "name": "nextbus",
      "short_name": "nextbus",
      "description": "Super easy bus and train tracking for the UK.",
      "id": "/",
      "start_url": "/",
      "icons": [
        {
          "src": "/favicon/web-app-manifest-192x192.png",
          "sizes": "192x192",
          "type": "image/png",
          "purpose": "maskable"
        },
        {
          "src": "/favicon/web-app-manifest-512x512.png",
          "sizes": "512x512",
          "type": "image/png",
          "purpose": "maskable"
        }
      ],
      "theme_color": "#00A0EB",
      "background_color": "#131313",
      "display": "standalone"
    },
    scope: '/',
    workbox: {
      navigateFallbackDenylist: [/^\/api(\/.*)?$/, /^\/ws(\/.*)?$/],
      navigateFallbackAllowlist: undefined,
      clientsClaim: true,
      skipWaiting: true,
    },
  })],
  server: {
    allowedHosts: ['pi5.tailefc815.ts.net'],
    proxy: {
      // REST API
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '/api')
      },
      // WebSocket endpoints
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
        rewrite: path => path.replace(/^\/ws/, '/ws'),
      },
    },
  },
  build: {
    manifest: true,
    outDir: "dist",
  }
})
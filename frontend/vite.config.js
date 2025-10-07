/**
 * Vite Configuration
 *
 * Vite is the build tool and dev server for this project.
 *
 * Configuration includes:
 * - React plugin for JSX support and Fast Refresh
 * - Dev server on port 3000
 * - API proxy to backend (optional, for CORS)
 * - Vitest for unit testing
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  // Plugins
  plugins: [
    react(), // Enables React JSX and Fast Refresh (hot reload)
  ],

  // Development server configuration
  server: {
    port: 3000, // Run dev server on http://localhost:3000

    // Optional: Proxy API requests to backend
    // This avoids CORS issues during development
    // Example: fetch('/api/vehicles') → http://localhost:8000/api/vehicles
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Backend URL
        changeOrigin: true, // Needed for virtual hosted sites
      },
    },
  },

  // Vitest configuration
  test: {
    globals: true, // Use global test functions (describe, it, expect)
    environment: 'jsdom', // Simulate browser environment for React components
    setupFiles: './src/test/setup.js', // Run setup file before tests
    css: true, // Process CSS imports in tests
  },
})

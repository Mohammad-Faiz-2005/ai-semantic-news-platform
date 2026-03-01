import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    host: true,           // Allow connections from network (useful for Docker)
    strictPort: true,     // Fail if port is already in use

    // Proxy API requests to the FastAPI backend during development.
    // This avoids CORS issues when running frontend and backend separately.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },

  build: {
    outDir: "dist",
    sourcemap: false,     // Disable sourcemaps in production build
    chunkSizeWarningLimit: 1000,
  },

  preview: {
    port: 4173,
  },
});
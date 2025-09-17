import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/ask': 'http://0.0.0.0:8000',
      '/ping': 'http://0.0.0.0:8000',
    },
  },
});

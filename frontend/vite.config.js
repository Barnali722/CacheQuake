import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy API calls to backend during development
    // Day 3: ensure backend is running on 8000 before starting dev server
    proxy: {
      '/simulate': 'http://localhost:8000',
      '/step':     'http://localhost:8000',
      '/compare':  'http://localhost:8000',
    },
  },
});

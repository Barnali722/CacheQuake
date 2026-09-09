import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],

  // GitHub Pages serves the app at /CacheQuake/ (repo name).
  // Set base to '/' when using a custom domain or Netlify/Vercel.
  base: '/',

  optimizeDeps: {
    entries: ['src/index.jsx'],
  },

  server: {
    port: 5173,
    proxy: {
      '/simulate': 'http://localhost:8000',
      '/step':     'http://localhost:8000',
      '/compare':  'http://localhost:8000',
      '/data':     'http://localhost:8000',
    },
  },
}));

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: { target: 'chrome90', outDir: 'build', sourcemap: false },
  server: { proxy: { '/api': process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000', '/ws': { target: (process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000').replace('http', 'ws'), ws: true } } },
  test: { environment: 'jsdom', globals: true, setupFiles: './src/setupTests.ts', include: ['src/**/*.test.{ts,tsx}'] },
});

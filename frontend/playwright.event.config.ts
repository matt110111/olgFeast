import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/event',
  timeout: 60000,
  expect: { timeout: 10000 },
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: { baseURL: process.env.E2E_URL || 'http://127.0.0.1:3002', screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  projects: [
    { name: 'ipad-landscape', use: { browserName: 'webkit', viewport: { width: 1024, height: 768 }, hasTouch: true } },
    { name: 'ipad-portrait', use: { browserName: 'webkit', viewport: { width: 768, height: 1024 }, hasTouch: true } },
    { name: 'tablet-landscape', use: { browserName: 'chromium', viewport: { width: 1024, height: 600 }, hasTouch: true } },
    { name: 'tablet-portrait', use: { browserName: 'chromium', viewport: { width: 800, height: 1280 }, hasTouch: true } },
  ],
});

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/ui-integration',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'line',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev --prefix apps/web',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});

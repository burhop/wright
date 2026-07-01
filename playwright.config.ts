import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/ui-integration",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  maxFailures: process.env.CI ? 1 : undefined,
  workers: process.env.CI ? 1 : undefined,
  reporter: "line",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:5173",
    trace: process.env.CI ? "retain-on-failure" : "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        command: "npm run dev --prefix apps/web",
        url: "http://localhost:5173",
        reuseExistingServer: !process.env.CI,
      },
});

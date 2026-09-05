import { defineConfig, devices } from "@playwright/test";
import { workspaceSurfaceProjects } from "./tests/ui-integration/playwright.workspace-surfaces";

const configuredBaseUrl = process.env.PLAYWRIGHT_BASE_URL;
const testUiHost = process.env.WRIGHT_PLAYWRIGHT_HOST || "127.0.0.1";
const testUiPort = process.env.WRIGHT_PLAYWRIGHT_PORT || "5173";
const managedBaseUrl = `http://${testUiHost}:${testUiPort}`;
const testOutputDir =
  process.env.WRIGHT_PLAYWRIGHT_OUTPUT_DIR || "test-results/playwright";

export default defineConfig({
  testDir: "./tests/ui-integration",
  expect: {
    timeout: 15_000,
  },
  fullyParallel: true,
  outputDir: testOutputDir,
  forbidOnly: !!process.env.CI,
  retries: 0,
  maxFailures: process.env.CI ? 5 : undefined,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [["line"], ["html", { outputFolder: "playwright-report", open: "never" }]]
    : "line",
  grepInvert: process.env.PLAYWRIGHT_INCLUDE_LIVE ? undefined : /@live/,
  use: {
    baseURL: configuredBaseUrl || managedBaseUrl,
    trace: process.env.CI ? "retain-on-failure" : "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    ...workspaceSurfaceProjects,
  ],
  webServer: configuredBaseUrl
    ? undefined
    : {
        command: `npm run dev --prefix apps/web -- --host ${testUiHost} --port ${testUiPort}`,
        url: managedBaseUrl,
        reuseExistingServer: false,
        env: {
          VITE_WRIGHT_PROCESS_DEFINITION_VIEW:
            process.env.VITE_WRIGHT_PROCESS_DEFINITION_VIEW ?? "1",
        },
      },
});

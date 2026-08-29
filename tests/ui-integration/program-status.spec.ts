import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const bundle = readFileSync(
  resolve("src/wright_engineering/static/program-status/current.json"),
  "utf8",
);
const parsedBundle = JSON.parse(bundle) as { bundle_id: string };

async function mockProgramStatus(page: Page) {
  await page.route("**/api/auth/session/status", (route) =>
    route.fulfill({ json: { auth_required: false, authenticated: true } }),
  );
  await page.route("**/api/setup/status", (route) =>
    route.fulfill({ json: { is_configured: true, theme: "dark" } }),
  );
  await page.route("**/api/program-status/publisher", (route) =>
    route.fulfill({
      json: {
        state: "active",
        mode: "committed_watch",
        observed_commit: null,
        last_attempt_at: "2026-08-29T12:54:04Z",
        last_success_at: "2026-08-29T12:54:04Z",
        failure_code: null,
        recovery: null,
      },
    }),
  );
  await page.route("**/api/program-status", (route) =>
    route.fulfill({
      body: bundle,
      contentType: "application/json",
      headers: { ETag: `"${parsedBundle.bundle_id}"` },
    }),
  );
}

test.describe("Program status comprehension and accessibility", () => {
  test.beforeEach(async ({ page }) => mockProgramStatus(page));

  test("answers the six operator questions and keeps exact fallbacks usable", async ({
    page,
  }) => {
    await page.goto("/program-status");

    await expect(page.getByTestId("page-program-status")).toBeVisible();
    for (const id of [
      "program-work-summary",
      "active-work-summary",
      "customer-capability-summary",
      "process-benchmark-summary",
      "test-health-summary",
      "next-action-summary",
    ]) {
      await expect(page.getByTestId(id)).toBeVisible();
    }
    await expect(
      page.getByText("0/100 qualified", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Independent readiness areas" }),
    ).toBeVisible();
    await expect(
      page
        .getByRole("heading", { name: "Independent readiness areas" })
        .locator("xpath=..")
        .getByRole("article"),
    ).toHaveCount(4);
    await expect(
      page
        .getByRole("heading", { name: "Independent readiness areas" })
        .locator("xpath=.."),
    ).toContainText(/not_started|blocked|in_progress/);

    const firstPlot = page.locator(".js-plotly-plot").first();
    await expect(firstPlot).toBeVisible();
    await firstPlot.locator(".point").first().hover({ force: true });
    await expect(firstPlot.locator(".hovertext").first()).toContainText(
      /commit [0-9a-f]{8}/,
    );

    const tableDisclosure = page
      .getByText("Exact checkpoint table", { exact: true })
      .first();
    await tableDisclosure.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("table").first()).toBeVisible();

    const accessibility = await new AxeBuilder({ page })
      .exclude(".js-plotly-plot")
      .analyze();
    expect(accessibility.violations).toEqual([]);
  });

  test("remains understandable when narrow, zoomed, reduced-motion, and graph code is unavailable", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 640, height: 720 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.route(/plotly(?:__|_)js-dist-min|plotly\.js-dist-min/, (route) =>
      route.abort(),
    );
    await page.goto("/program-status");
    await page.evaluate(() => {
      document.documentElement.style.zoom = "2";
    });

    await expect(page.getByTestId("program-at-a-glance")).toBeVisible();
    await expect(
      page.getByText("Not release eligible", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByLabel("Governed benchmark qualification"),
    ).toBeVisible();
    await expect(
      page.getByText("Exact checkpoint table", { exact: true }).first(),
    ).toBeVisible();
    await expect(page.getByTestId("program-history")).toContainText(
      "Exact committed checkpoints only",
    );
  });
});

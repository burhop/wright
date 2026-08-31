import {
  mkdtempSync,
  readFileSync,
  renameSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page, type Route } from "@playwright/test";

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

function command(executable: string, args: string[]): string {
  const result = spawnSync(executable, args, {
    cwd: resolve("."),
    encoding: "utf8",
    env: Object.fromEntries(
      Object.entries(process.env).filter(([key]) => key !== "PYTHONPATH"),
    ),
    timeout: 120_000,
  });
  expect(
    result.status,
    `${executable}: ${result.stderr}\n${result.stdout}`,
  ).toBe(0);
  return result.stdout.trim();
}

function installCommittedFixture(
  dataRoot: string,
  raw: string,
  observedCommit: string,
  observedAt: string,
): void {
  const currentTemp = resolve(dataRoot, ".current.json.tmp");
  writeFileSync(currentTemp, raw, "utf8");
  renameSync(currentTemp, resolve(dataRoot, "current.json"));
  const publisherTemp = resolve(dataRoot, ".publisher.json.tmp");
  writeFileSync(
    publisherTemp,
    JSON.stringify({
      state: "active",
      mode: "committed_watch",
      observed_commit: observedCommit,
      last_attempt_at: observedAt,
      last_success_at: observedAt,
      failure_code: null,
      recovery: null,
    }),
    "utf8",
  );
  renameSync(publisherTemp, resolve(dataRoot, "publisher.json"));
}

function canonicalFixture(value: unknown): string {
  if (value === null || typeof value === "boolean" || typeof value === "string")
    return JSON.stringify(value);
  if (typeof value === "number") {
    if (!Number.isFinite(value) || !Number.isSafeInteger(value))
      throw new Error("refresh fixture uses the integer canonical subset");
    return String(value);
  }
  if (Array.isArray(value)) return `[${value.map(canonicalFixture).join(",")}]`;
  if (typeof value === "object") {
    const row = value as Record<string, unknown>;
    return `{${Object.keys(row)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalFixture(row[key])}`)
      .join(",")}}`;
  }
  throw new Error("refresh fixture contains an unsupported value");
}

function fixtureDigest(value: unknown): string {
  return createHash("sha256").update(canonicalFixture(value)).digest("hex");
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
    await expect(page.getByTestId("program-work-summary")).toContainText(
      "EPP-F01B tasks complete",
    );
    await expect(page.getByTestId("active-work-summary")).toContainText(
      "Committed assignment unavailable",
    );
    await expect(page.getByTestId("customer-capability-summary")).toContainText(
      "100 proposed customer stories",
    );
    await expect(page.getByTestId("test-health-summary")).toContainText(
      "50 passed · 0 failed",
    );
    await expect(page.getByTestId("next-action-summary")).toContainText(
      "Authority: authorized; human approval: not required",
    );
    await expect(page.getByTestId("release-posture-summary")).toContainText(
      "Not release eligible",
    );
    await expect(page.getByTestId("release-posture-summary")).toContainText(
      "feature task progress cannot compensate",
    );
    await page.getByText("Historical dashboard action", { exact: true }).click();
    await expect(page.getByTestId("next-action-summary")).toContainText(
      "current program-state action above takes precedence",
    );
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

  test("refreshes atomically after an exact committed publication and observes its separate heartbeat", async ({
    page,
  }) => {
    test.setTimeout(180_000);
    const dataRoot = mkdtempSync(resolve(tmpdir(), "wright-program-status-"));
    const artifactPath =
      "src/wright_engineering/static/program-status/current.json";
    const fixtureCommit = command("git", [
      "log",
      "--format=%H",
      "--max-count=1",
      "HEAD",
      "--",
      artifactPath,
    ]);
    expect(fixtureCommit).toMatch(/^[0-9a-f]{40}$/);
    const firstRaw = command("git", [
      "show",
      `${fixtureCommit}:${artifactPath}`,
    ]);
    const servedEtags: string[] = [];
    const observedPublisherCommits: Array<string | null> = [];
    const observedPublisherTimes: Array<string | null> = [];

    try {
      const first = JSON.parse(firstRaw);
      const second = structuredClone(first);
      second.generated_at = "2026-08-29T14:00:00Z";
      second.supplement.work.tasks.total += 1;
      second.supplement.work.tasks.remaining += 1;
      second.supplement.work.current_milestone =
        "Committed refresh acceptance fixture";
      second.bundle_id = fixtureDigest({
        source: second.source,
        dashboard: second.dashboard,
        supplement: second.supplement,
      });
      const secondRaw = JSON.stringify(second);
      installCommittedFixture(
        dataRoot,
        firstRaw,
        first.source.commit,
        "2026-08-29T13:52:16Z",
      );
      await page.route("**/api/program-status/publisher", (route) => {
        const publisher = JSON.parse(
          readFileSync(resolve(dataRoot, "publisher.json"), "utf8"),
        );
        observedPublisherCommits.push(publisher.observed_commit);
        observedPublisherTimes.push(publisher.last_success_at);
        return route.fulfill({ json: publisher });
      });
      await page.route("**/api/program-status", (route) => {
        const body = readFileSync(resolve(dataRoot, "current.json"), "utf8");
        const current = JSON.parse(body);
        const etag = `"${current.bundle_id}"`;
        servedEtags.push(etag);
        if (route.request().headers()["if-none-match"] === etag) {
          return route.fulfill({ status: 304, headers: { ETag: etag } });
        }
        return route.fulfill({
          body,
          contentType: "application/json",
          headers: { ETag: etag },
        });
      });

      await page.goto("/program-status");
      await expect(page.getByTestId("program-work-summary")).toContainText(
        `${first.supplement.work.tasks.completed}/${first.supplement.work.tasks.total}`,
      );
      await expect(
        page.getByTestId("program-status-refresh-state"),
      ).toContainText("Publisher: active");

      installCommittedFixture(
        dataRoot,
        secondRaw,
        second.source.commit,
        "2026-08-29T14:00:00Z",
      );
      const installedSecond = JSON.parse(
        readFileSync(resolve(dataRoot, "current.json"), "utf8"),
      );
      expect(installedSecond.bundle_id).not.toBe(first.bundle_id);
      await expect(page.getByTestId("program-work-summary")).toContainText(
        `${installedSecond.supplement.work.tasks.completed}/${installedSecond.supplement.work.tasks.total}`,
        { timeout: 20_000 },
      );
      expect(new Set(servedEtags)).toEqual(
        new Set([`"${first.bundle_id}"`, `"${installedSecond.bundle_id}"`]),
      );
      expect(observedPublisherCommits).toContain(first.source.commit);
      expect(new Set(observedPublisherTimes)).toEqual(
        new Set(["2026-08-29T13:52:16Z", "2026-08-29T14:00:00Z"]),
      );
      await expect(
        page.getByText("Program status unavailable", { exact: true }),
      ).toHaveCount(0);
    } finally {
      rmSync(dataRoot, { recursive: true, force: true });
    }
  });

  test("keeps last-valid evidence on refresh failure and stays honest with no prior bundle", async ({
    page,
  }) => {
    let bundleCalls = 0;
    let failRefresh = false;
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
          observed_commit: parsedBundle.bundle_id.slice(0, 40),
          last_attempt_at: "2026-08-29T14:00:00Z",
          last_success_at: "2026-08-29T14:00:00Z",
          failure_code: null,
          recovery: null,
        },
      }),
    );
    const fail = (route: Route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        json: {
          error_code: "PROGRAM_STATUS_READ_FAILED",
          message: "Program status could not be read.",
          recovery_class: "inspect_local_runtime",
          trace_id: "test-refresh-failure",
        },
      });
    await page.route("**/api/program-status", (route) => {
      bundleCalls += 1;
      if (failRefresh) return fail(route);
      return route.fulfill({
        body: bundle,
        contentType: "application/json",
        headers: { ETag: `"${parsedBundle.bundle_id}"` },
      });
    });

    await page.goto("/program-status");
    await expect(page.getByTestId("program-status-refresh-state")).toContainText(
      "Committed evidence current",
    );
    failRefresh = true;
    await expect
      .poll(() => bundleCalls, { timeout: 12_000 })
      .toBeGreaterThan(1);
    await expect(page.getByTestId("program-status-refresh-state")).toContainText(
      "Showing last valid evidence",
    );
    await expect(page.getByTestId("program-work-summary")).toBeVisible();

    await page.unroute("**/api/program-status");
    await page.route("**/api/program-status", fail);
    await page.reload();
    await expect(
      page.getByRole("heading", {
        name: "No validated program-status bundle is available yet",
      }),
    ).toBeVisible();
    await expect(page.getByTestId("program-status-refresh-state")).toContainText(
      "Program status unavailable",
    );
  });
});

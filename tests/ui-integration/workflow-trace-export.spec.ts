import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { expect, test } from "@playwright/test";

test("opens a relocated workflow review package offline with working links", async ({
  page,
}) => {
  const root = mkdtempSync(join(tmpdir(), "wright-trace-export-"));
  try {
    const fileUrls = JSON.parse(
      execFileSync(
        "uv",
        [
          "run",
          "python",
          "tests/ui-integration/fixtures/build-workflow-trace-export.py",
          root,
        ],
        { encoding: "utf8" },
      ),
    ) as { full_data: string; report_only: string };
    const networkRequests: string[] = [];
    await page.route("http://**/*", (route) => {
      networkRequests.push(route.request().url());
      return route.abort();
    });
    await page.route("https://**/*", (route) => {
      networkRequests.push(route.request().url());
      return route.abort();
    });

    await page.goto(fileUrls.full_data);
    await expect(
      page.getByRole("heading", { name: "portable-review" }),
    ).toBeVisible();
    await expect(page.locator(".step-node").filter({ hasText: "Generate housing" })).toBeVisible();
    await page.getByRole("button", { name: "Run-level files (1)", exact: true }).click();
    await expect(page.getByRole("dialog")).toContainText("Producing activity not recorded");
    await page.getByRole("dialog").getByRole("button", { name: /^Housing/ }).click();
    const included = page.getByRole("link", { name: "Download original STEP" });
    await expect(included).toHaveAttribute(
      "href",
      "outputs/output/housing.step",
    );
    expect(networkRequests).toEqual([]);
    expect(
      readFileSync(
        join(
          root,
          "relocated",
          "full_data",
          "review",
          "outputs",
          "output",
          "housing.step",
        ),
        "utf8",
      ),
    ).toContain("ISO-10303-21");
    await page.goto(fileUrls.report_only);
    await expect(
      page.getByRole("heading", { name: "portable-review" }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Download original STEP" }),
    ).toHaveCount(0);
    await page.getByRole("button", { name: /^Housing/ }).click();
    await expect(
      page.getByText("The original file is not included", { exact: false }),
    ).toBeVisible();
    expect(networkRequests).toEqual([]);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("SVG evidence is rendered only as an inert image offline", async ({ page }) => {
  const root = mkdtempSync(join(tmpdir(), "wright-trace-svg-"));
  try {
    const urls = JSON.parse(execFileSync("uv", ["run", "python", "tests/ui-integration/fixtures/build-workflow-trace-export.py", root, "svg"], { encoding: "utf8" }));
    const requests: string[] = [];
    await page.route(/^https?:/, route => { requests.push(route.request().url()); return route.abort(); });
    for (const mode of ["full_data", "report_only"]) {
      await page.goto(urls[mode]);
      await page.getByRole("button", { name: "Run-level files (2)", exact: true }).click();
      await page.getByRole("dialog").getByRole("button", { name: /Toolpath projection/ }).click();
      const picture = page.getByRole("dialog").getByRole("img", { name: "Toolpath projection" });
      await expect(picture).toBeVisible();
      expect(await picture.evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth === 256)).toBe(true);
      expect(await page.evaluate(() => (window as unknown as {svgExecuted?: boolean}).svgExecuted)).toBeUndefined();
      await expect(page.locator("object,embed,iframe")).toHaveCount(0);
    }
    expect(requests).toEqual([]);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("activity file controls preserve iteration-specific outputs and navigation", async ({ page }) => {
  const root = mkdtempSync(join(tmpdir(), "wright-trace-file-iterations-"));
  try {
    const urls = JSON.parse(execFileSync("uv", ["run", "python", "tests/ui-integration/fixtures/build-workflow-trace-export.py", root, "iterations"], { encoding: "utf8" }));
    for (const width of [944, 390]) {
      await page.setViewportSize({ width, height: 791 });
      await page.goto(urls.full_data);
      await page.getByRole("button", { name: "Workflow execution", exact: true }).click();
      await page.getByRole("button", { name: "Files from Generate housing (2)", exact: true }).click();
      const detail = page.getByRole("dialog");
      await expect(detail.locator(".document-link strong")).toHaveText(["Housing revised"]);
      await detail.getByRole("button", { name: "Iteration 1 / Failed", exact: true }).click();
      await expect(detail.locator(".document-link strong")).toHaveText(["Housing"]);
      await detail.locator(".document-link").click();
      await expect(detail.getByRole("link", { name: "Download original STEP" })).toHaveAttribute("href", "outputs/output/housing.step");
      await detail.getByRole("button", { name: "Produced by: Generate housing", exact: true }).click();
      await expect(detail.getByRole("button", { name: "Iteration 1 / Failed", exact: true })).toHaveAttribute("aria-pressed", "true");
      await detail.getByRole("button", { name: "Back", exact: true }).click();
      await detail.getByRole("button", { name: "Back", exact: true }).click();
      await detail.getByRole("button", { name: "View activity details", exact: true }).click();
      await expect(detail.getByRole("button", { name: "Iteration 1 / Failed", exact: true })).toHaveAttribute("aria-pressed", "true");
      await expect(detail.locator(".document-link strong")).toHaveText(["Housing"]);
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("compact blocks retain all swimlanes and inspectable handoffs for 30 activities", async ({ page }) => {
  const root = mkdtempSync(join(tmpdir(), "wright-trace-thirty-"));
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  try {
    const urls = JSON.parse(execFileSync("uv", ["run", "python", "tests/ui-integration/fixtures/build-workflow-trace-export.py", root, "thirty-activities"], { encoding: "utf8" }));
    for (const width of [1440, 909, 390]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(urls.full_data);
      const laneLabels = ["Requirements", "Design", "Analysis", "Manufacturing", "Approval"];
      await expect(page.locator(".lane > .lane-title > span:last-child")).toHaveText(laneLabels);
      await expect(page.getByRole("group", { name: "Process detail level" })).toHaveCount(0);
      await expect(page.locator(".step-node")).toHaveCount(30);
      await expect(page.locator(".edge-tag")).toHaveCount(29);
      expect(await page.locator(".step-node").first().evaluate(element => element.getBoundingClientRect().width)).toBeLessThanOrEqual(128);
      expect(await page.locator(".lane").evaluateAll(lanes => lanes.every(lane => getComputedStyle(lane).display === "grid"))).toBe(true);
      const compactHeights = await page.locator(".lane").evaluateAll(lanes => lanes.map(lane => lane.getBoundingClientRect().height));
      await page.getByRole("button", { name: "Fit width", exact: true }).click();
      expect(await page.locator(".diagram-scroll").evaluate(element => element.scrollWidth <= element.clientWidth + 2)).toBe(true);
      await expect.poll(() => page.evaluate(() => {
        const review = JSON.parse(document.getElementById('wright-trace-data')!.textContent!).review;
        return [...document.querySelectorAll<SVGPathElement>('.edge-line')].every((path, index) => {
          const end = path.getPointAtLength(path.getTotalLength());
          const actual = new DOMPoint(end.x, end.y).matrixTransform(path.getScreenCTM()!);
          const target = document.getElementById(review.edges[index].target)!.getBoundingClientRect();
          return actual.x >= target.left - 5 && actual.x <= target.right + 5 && actual.y >= target.top - 5 && actual.y <= target.bottom + 5;
        });
      })).toBe(true);
      await page.locator(".step-node").last().click();
      await expect(page.getByRole("dialog").getByRole("heading", { name: "Engineering activity 30", exact: true })).toBeVisible();
      await expect(page.getByRole("dialog")).toContainText("Layout fixture tool");
      await page.getByRole("button", { name: "Close details" }).click();
      await page.locator(".edge-tag").last().click();
      await expect(page.getByRole("dialog").getByRole("heading", { name: "Handoff 29", exact: true })).toBeVisible();
      await page.getByRole("button", { name: "Close details" }).click();
      if (width === 909) await page.screenshot({ path: resolve("specs/083-workflow-trace-review/evidence/live-campaign/layout-fixture-30-compact-fit.png"), fullPage: true });
      await page.getByRole("slider", { name: "Process zoom" }).evaluate((input: HTMLInputElement) => { input.value = "100"; input.dispatchEvent(new Event("input", { bubbles: true })); });
      await page.getByRole("button", { name: "Approval", exact: true }).focus();
      await page.keyboard.press("Enter");
      await expect(page.getByRole("button", { name: "Approval", exact: true })).toHaveAttribute("aria-expanded", "true");
      await expect(page.locator(".lane > .lane-title > span:last-child")).toHaveText(laneLabels);
      const expandedHeights = await page.locator(".lane").evaluateAll(lanes => lanes.map(lane => lane.getBoundingClientRect().height));
      expect(expandedHeights.slice(0, 4)).toEqual(compactHeights.slice(0, 4));
      expect(expandedHeights[4]).toBeGreaterThan(compactHeights[4]);
      await expect(page.locator(".lane[data-expanded=true]")).toHaveCount(1);
      await expect(page.locator(".lane").last().getByRole("button", { name: "Files from Engineering activity 30 (1)" })).toBeVisible();
      await page.locator(".step-node").last().focus();
      await page.keyboard.press("Enter");
      await expect(page.getByRole("dialog").getByRole("heading", { name: "Engineering activity 30", exact: true })).toBeVisible();
      await page.getByRole("button", { name: "Close details" }).click();
      await page.locator(".lane").getByRole("button", { name: "Requirements", exact: true }).click();
      await page.getByRole("button", { name: "Approval", exact: true }).click();
      await expect(page.locator(".lane[data-expanded=true]")).toHaveCount(1);
      await expect(page.locator(".lane").getByRole("button", { name: "Requirements", exact: true })).toHaveAttribute("aria-expanded", "true");
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    }
    expect(errors).toEqual([]);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

for (const scenario of ["short", "many", "empty"]) {
  test(`input overview handles ${scenario} inputs with progressive disclosure`, async ({ page }) => {
    const root = mkdtempSync(join(tmpdir(), "wright-trace-inputs-"));
    try {
      const urls = JSON.parse(execFileSync("uv", ["run", "python", "tests/ui-integration/fixtures/build-workflow-trace-export.py", root, scenario], { encoding: "utf8" }));
      const requests: string[] = [];
      await page.route(/^https?:/, route => { requests.push(route.request().url()); return route.abort(); });
      for (const mode of ["full_data", "report_only"]) {
        for (const width of [944, 702, 390]) {
          await page.setViewportSize({ width, height: 791 });
          await page.goto(urls[mode]);
          const inputs = page.getByRole("region", { name: "Inputs", exact: true });
          const outputs = page.getByRole("region", { name: "Outputs", exact: true });
          expect((await inputs.boundingBox())!.y).toBeLessThan((await outputs.boundingBox())!.y);
          await expect(inputs.locator(".section-heading button")).toHaveCount(0);
          expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
          if (scenario === "short") {
            await expect(inputs.getByText("Create a housing for the sensor.", { exact: true })).toBeVisible();
            await expect(inputs.getByRole("button", { name: "Read full prompt" })).toHaveCount(0);
          } else if (scenario === "many") {
            await expect(inputs.locator(".input-attachments > .input-preview-list button")).toHaveCount(3);
            await expect(inputs.locator(".input-more .input-link")).toHaveCount(23);
            await expect(inputs.locator(".input-more .input-link").first()).toBeHidden();
            expect((await inputs.locator(".input-excerpt").boundingBox())!.height).toBeLessThan(75);
            await inputs.getByRole("button", { name: "Read full prompt" }).click();
            await expect(page.getByRole("dialog")).toContainText("END OF REQUEST");
            await page.getByRole("button", { name: "Close details" }).click();
            await inputs.locator(".input-more > summary").focus();
            await page.keyboard.press("Enter");
            await expect(inputs.locator(".input-more > summary")).toHaveText("23 more inputs");
            await expect(inputs.locator(".input-more .input-link").last()).toBeVisible();
            await inputs.getByRole("button", { name: /Reference 23/ }).click();
            const dialog = page.getByRole("dialog");
            await expect(dialog).toContainText("original content is not included");
            await dialog.getByRole("button", { name: "Close details" }).click();
            await inputs.locator(".input-more > summary").click();
            await expect(inputs.locator(".input-more .input-link").first()).toBeHidden();
            const inputLane = page.locator(".input-lane").first();
            await expect(inputLane.locator(".input-card")).toHaveCount(4);
            await expect(inputLane.locator(".input-card-details").first()).toBeHidden();
            if (width > 520) expect((await inputLane.boundingBox())!.height).toBeLessThanOrEqual(200);
            await inputLane.getByRole("button", { name: /24 more inputs/ }).click();
            await expect(dialog.getByRole("searchbox", { name: "Find an input" })).toBeVisible();
            await dialog.getByRole("searchbox", { name: "Find an input" }).fill("reference-23");
            await expect(dialog.locator(".input-link")).toHaveCount(1);
            await expect(dialog.getByRole("button", { name: /Reference 23/ })).toBeVisible();
            await dialog.getByRole("button", { name: /Reference 23/ }).click();
            await expect(dialog).toContainText("original content is not included");
            await dialog.getByRole("button", { name: "Back", exact: true }).click();
            await expect(dialog.getByRole("searchbox", { name: "Find an input" })).toHaveValue("reference-23");
            await dialog.getByRole("searchbox", { name: "Find an input" }).fill("does-not-exist");
            await expect(dialog).toContainText("No matching inputs.");
            await dialog.getByRole("button", { name: "Close details" }).click();
            await inputLane.locator(".lane-toggle").click();
            await expect(inputLane.locator(".input-card-details").first()).toBeVisible();
            expect(await inputLane.locator(".input-card").evaluateAll(cards => cards.every(card => card.scrollWidth <= card.clientWidth + 1))).toBe(true);
          } else {
            await expect(inputs).toContainText("Input records were not retained for this run.");
            await expect(page.locator(".input-lane")).toHaveCount(0);
          }
        }
      }
      expect(requests).toEqual([]);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
}

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { chromium, expect, test } from "@playwright/test";

const reportPath = process.env.WRIGHT_TRACE_CAMPAIGN_REPORT;
const campaignRoot = process.env.WRIGHT_TRACE_CAMPAIGN_ROOT;

test("@live PDF drawing stays painted through scrollbar, zoom and resize changes", async ({}, testInfo) => {
  test.skip(
    !reportPath,
    "Set WRIGHT_TRACE_CAMPAIGN_REPORT to an extracted report.",
  );
  test.setTimeout(90_000);
  // Desktop browsers reserve scrollbar space; headless Chromium normally hides it.
  const browser = await chromium.launch({
    ignoreDefaultArgs: ["--hide-scrollbars"],
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 796, height: 791 },
      deviceScaleFactor: 1.6,
    });
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.route(/^https?:/, (route) => route.abort());
    await page.goto(pathToFileURL(resolve(reportPath!)).href);
    await page.locator(".step-node").first().click();
    const viewer = page.getByRole("dialog").locator("[data-pdf-viewer]");
    await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
    const observation = await viewer.evaluateHandle((element) => {
      const result = { resets: 0, blankFrames: 0, paints: 0 };
      const observer = new MutationObserver((changes) => {
        for (const change of changes) {
          if (
            change.type === "attributes" &&
            change.target instanceof HTMLCanvasElement
          )
            result.resets++;
          if (change.type === "childList") result.paints++;
        }
        const canvas = element.querySelector("canvas")!;
        const pixels = canvas
          .getContext("2d")!
          .getImageData(0, 0, canvas.width, canvas.height).data;
        let ink = 0;
        for (let index = 0; index < pixels.length; index += 4)
          if (pixels[index + 3] && pixels[index] < 180) ink++;
        if (ink < 1000) result.blankFrames++;
      });
      observer.observe(element.querySelector(".pdf-viewport")!, {
        subtree: true,
        childList: true,
        attributes: true,
        attributeFilter: ["width", "height"],
      });
      return result;
    });
    const dimensions = await viewer.locator(".pdf-viewport").boundingBox();
    await viewer.getByRole("button", { name: "Zoom in", exact: true }).click();
    await expect(viewer.locator("[data-pdf-scale]")).toHaveText("125%");
    await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
    expect(await viewer.locator(".pdf-viewport").boundingBox()).toEqual(
      dimensions,
    );
    await viewer.getByRole("button", { name: "Fit drawing to view" }).click();
    await expect(viewer.locator("[data-pdf-scale]")).toHaveText("100%");
    for (const width of [430, 1297, 796]) {
      await page.setViewportSize({ width, height: 791 });
      await page.waitForTimeout(350);
      await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
    }
    const settled = await observation.jsonValue();
    // A settled canvas must not oscillate between loading and ready while idle.
    await page.waitForTimeout(1200);
    expect(await observation.jsonValue()).toEqual(settled);
    expect(settled.resets).toBe(0);
    expect(settled.blankFrames).toBe(0);
    await page.screenshot({
      path: testInfo.outputPath("pdf-stable-scrollbars.png"),
    });
    expect(errors).toEqual([]);
  } finally {
    await browser.close();
  }
});

test("@live CAD activities open on interactive geometry with correct provenance", async ({
  page,
}, testInfo) => {
  test.skip(
    !reportPath,
    "Set WRIGHT_TRACE_CAMPAIGN_REPORT to an extracted report index.",
  );
  test.setTimeout(90_000);
  const errors: string[] = [];
  const requests: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route(/^https?:/, (route) => {
    requests.push(route.request().url());
    return route.abort();
  });
  await page.goto(pathToFileURL(resolve(reportPath!)).href);
  const detail = page.getByRole("dialog");
  const viewer = detail.locator(".activity-evidence .stl-viewer");
  const pixels = () =>
    viewer.locator("canvas").evaluate(
      (canvas: HTMLCanvasElement) =>
        new Promise<{ count: number; signature: number }>((done) =>
          requestAnimationFrame(() => {
            const gl = canvas.getContext("webgl2")!;
            const values = new Uint8Array(canvas.width * canvas.height * 4);
            gl.readPixels(
              0,
              0,
              canvas.width,
              canvas.height,
              gl.RGBA,
              gl.UNSIGNED_BYTE,
              values,
            );
            let count = 0,
              signature = 0;
            for (let i = 0; i < values.length; i += 4) {
              if (
                Math.abs(values[i] - 19) > 4 ||
                Math.abs(values[i + 1] - 28) > 4 ||
                Math.abs(values[i + 2] - 43) > 4
              )
                count++;
              signature =
                (Math.imul(signature, 31) +
                  values[i] +
                  values[i + 1] * 2 +
                  values[i + 2] * 3) >>>
                0;
            }
            done({ count, signature });
          }),
        ),
    );
  for (const [name, origin] of [
    ["Author CAD source", "Later CAD result / AgentCAD enclosure"],
    ["AgentCAD enclosure", "Geometry produced in this activity"],
    ["Inspect CAD exports", "Geometry inspected in this activity"],
  ]) {
    await page.setViewportSize({ width: 1297, height: 900 });
    await page.getByRole("button", { name, exact: true }).first().click();
    await expect(viewer).toHaveAttribute("data-viewer-state", "ready");
    await expect(detail.locator(".geometry-origin")).toContainText(origin);
    if (name === "Author CAD source")
      await expect(detail.locator(".geometry-note")).toContainText(
        "not captured during source authoring",
      );
    for (const width of [1297, 796, 430]) {
      await page.setViewportSize({ width, height: 860 });
      await expect(viewer).toBeInViewport();
      expect((await pixels()).count).toBeGreaterThan(1000);
      expect(
        await detail.evaluate(
          (element) => element.scrollWidth <= element.clientWidth + 1,
        ),
      ).toBe(true);
      await page.screenshot({
        path: testInfo.outputPath(`${name.replaceAll(" ", "-")}-${width}.png`),
      });
    }
    await detail
      .getByRole("combobox", { name: "Activity evidence" })
      .selectOption({ label: "Enclosure concept B" });
    await expect(viewer).toHaveAttribute(
      "aria-label",
      "Interactive 3D view of Enclosure concept B",
    );
    await expect(viewer).toHaveAttribute("data-viewer-state", "ready");
    const before = await pixels();
    const bounds = (await viewer.boundingBox())!;
    await page.mouse.move(
      bounds.x + bounds.width * 0.4,
      bounds.y + bounds.height * 0.5,
    );
    await page.mouse.down();
    await page.mouse.move(
      bounds.x + bounds.width * 0.7,
      bounds.y + bounds.height * 0.6,
      { steps: 8 },
    );
    await page.mouse.up();
    await expect
      .poll(async () => (await pixels()).signature)
      .not.toBe(before.signature);
    await viewer.getByRole("button", { name: "Fit model to view" }).click();
    expect((await pixels()).count).toBeGreaterThan(1000);
    await detail.getByRole("button", { name: "Close details" }).click();
  }
  expect(errors).toEqual([]);
  expect(requests).toEqual([]);
});

test("@live activity opens its drawing and research account without a file-list detour", async ({
  page,
}, testInfo) => {
  test.skip(
    !reportPath,
    "Set WRIGHT_TRACE_CAMPAIGN_REPORT to an extracted report index.",
  );
  const errors: string[] = [];
  const remoteRequests: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route(/^https?:/, (route) => {
    remoteRequests.push(route.request().url());
    return route.abort();
  });
  await page.setViewportSize({ width: 1297, height: 900 });
  await page.goto(pathToFileURL(resolve(reportPath!)).href);
  await page.locator(".step-node").first().click();
  const detail = page.getByRole("dialog");
  const viewer = detail.locator("[data-pdf-viewer]");
  await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
  await expect(viewer.locator("canvas")).toHaveAccessibleName(
    "Manufacturer drawing, page 1 of 1",
  );
  await expect(detail.locator(".evidence-source")).toContainText(
    "pip-assets.raspberrypi.com",
  );
  await expect(detail.locator(".activity-report")).toContainText("85");
  await expect(
    detail.locator("details.execution-record").first(),
  ).not.toHaveAttribute("open", "");
  const pixels = () =>
    viewer.locator("canvas").evaluate((canvas: HTMLCanvasElement) => {
      const values = canvas
        .getContext("2d")!
        .getImageData(0, 0, canvas.width, canvas.height).data;
      let dark = 0;
      for (let i = 0; i < values.length; i += 4)
        if (values[i] < 180 && values[i + 1] < 180 && values[i + 2] < 180)
          dark += 1;
      return dark;
    });
  expect(await pixels()).toBeGreaterThan(1000);
  for (const width of [1297, 796, 430]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
    await expect(viewer).toBeInViewport();
    expect(
      await detail.evaluate(
        (element) => element.scrollWidth <= element.clientWidth + 1,
      ),
    ).toBe(true);
    await page.screenshot({
      path: testInfo.outputPath(`drawing-first-${width}.png`),
    });
  }
  await page.setViewportSize({ width: 1297, height: 900 });
  await detail
    .getByRole("combobox", { name: "Activity evidence", exact: true })
    .selectOption({ label: "Manufacturer product brief" });
  await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
  await expect(viewer.locator("canvas")).toHaveAccessibleName(/page 1 of 6/);
  await viewer.getByRole("button", { name: "Next page", exact: true }).click();
  await expect(viewer.locator("canvas")).toHaveAccessibleName(/page 2 of 6/);
  await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
  expect(await pixels()).toBeGreaterThan(1000);
  await viewer.getByRole("button", { name: "Zoom in", exact: true }).click();
  await expect(viewer.locator("[data-pdf-scale]")).toHaveText("125%");
  await detail
    .getByRole("button", { name: "Open document", exact: true })
    .click();
  await expect(
    detail.getByRole("heading", {
      name: "Manufacturer product brief",
      exact: true,
    }),
  ).toBeVisible();
  await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
  await expect(detail).not.toContainText(
    "The original supporting file is retained below.",
  );
  await expect(
    detail.getByRole("link", { name: "Download original PDF", exact: true }),
  ).toBeVisible();
  await detail.getByRole("button", { name: "Back", exact: true }).click();
  await expect(
    detail.getByRole("heading", { name: "Source dimensions", exact: true }),
  ).toBeVisible();
  await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
  await page.keyboard.press("Escape");
  await expect(detail).not.toBeVisible();
  await page.locator(".step-node").first().click();
  await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
  expect(errors).toEqual([]);
  expect(remoteRequests).toEqual([]);
});

test("@live an unreadable PDF offers its original without another navigation", async ({
  page,
}) => {
  test.skip(
    !reportPath,
    "Set WRIGHT_TRACE_CAMPAIGN_REPORT to an extracted report index.",
  );
  await page.goto(pathToFileURL(resolve(reportPath!)).href);
  await page.evaluate(() => {
    const viewer = (
      window as unknown as {
        WrightPDFViewer: { mount: (...args: unknown[]) => void };
      }
    ).WrightPDFViewer;
    const mount = viewer.mount;
    viewer.mount = (element, _bytes, title, path) =>
      mount(element, btoa("invalid PDF test input"), title, path);
  });
  await page.locator(".step-node").first().click();
  const viewer = page.getByRole("dialog").locator("[data-pdf-viewer]");
  await expect(viewer).toHaveAttribute("data-pdf-state", "error");
  await expect(viewer.locator(".pdf-viewport")).not.toBeVisible();
  await expect(
    viewer.getByRole("link", { name: "Download original PDF", exact: true }),
  ).toHaveAttribute("href", /manufacturer-drawing\.pdf$/);
});

test("@live printing activities keep the engineering account ahead of execution metadata", async ({
  page,
}) => {
  test.skip(
    !campaignRoot,
    "Set WRIGHT_TRACE_CAMPAIGN_ROOT to the generated campaign directory.",
  );
  await page.route(/^https?:/, (route) => route.abort());
  await page.goto(
    pathToFileURL(
      resolve(
        campaignRoot!,
        "reports/printed-replacement-part-01/full_data/index.html",
      ),
    ).href,
  );
  const detail = page.getByRole("dialog");
  for (let index = 0; index < 4; index++) {
    await page.locator(".step-node").nth(index).click();
    await expect(
      detail.getByRole("heading", { name: "Work performed", exact: true }),
    ).toBeVisible();
    await expect(
      detail.locator(".detail-body > .execution-record"),
    ).not.toHaveAttribute("open", "");
    if (index === 0)
      await expect(
        detail.getByRole("heading", { name: "Design dimensions", exact: true }),
      ).toHaveCount(1);
    if (index === 3) {
      await expect(
        detail.getByRole("row").filter({ hasText: "Authorized by" }),
      ).toHaveCount(1);
      await expect(
        detail
          .getByRole("row")
          .filter({ hasText: "Physical printer transfer" }),
      ).toContainText("Not performed");
    }
    await detail.locator(".detail-body > .execution-record > summary").click();
    await expect(
      detail.getByRole("heading", { name: "Tool & execution", exact: true }),
    ).toBeVisible();
    await detail.getByRole("button", { name: "Close details" }).click();
  }
});

test("@live input connectors reach the process in compact and expanded lanes", async ({
  page,
}, testInfo) => {
  test.skip(
    !campaignRoot,
    "Set WRIGHT_TRACE_CAMPAIGN_ROOT to the generated campaign directory.",
  );
  const errors: string[] = [];
  const remoteRequests: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route(/^https?:/, (route) => {
    remoteRequests.push(route.request().url());
    return route.abort();
  });

  for (const [caseId, scope, label] of [
    ["raspberry-pi-enclosure-01", "run", "Run inputs"],
    ["printed-replacement-part-01", "activity", "Inputs used"],
  ]) {
    await page.goto(
      pathToFileURL(
        resolve(campaignRoot!, "reports", caseId, "full_data", "index.html"),
      ).href,
    );
    const arrow = page
      .locator(`.input-line[data-input-scope="${scope}"]`)
      .first();
    const tag = page
      .getByRole("button", { name: new RegExp(`^${label}:`) })
      .first();
    await expect(arrow).toHaveCount(1);
    const expectAttached = async () => {
      await expect
        .poll(async () =>
          arrow.evaluate((element) => {
            const path = element as SVGPathElement;
            const matrix = path.getScreenCTM();
            if (!matrix) return Infinity;
            const end = path
              .getPointAtLength(path.getTotalLength())
              .matrixTransform(matrix);
            const target = document
              .querySelector(".step-block")!
              .getBoundingClientRect();
            return Math.max(
              Math.abs(end.x - (target.left + target.width / 2)),
              Math.abs(end.y - target.top),
            );
          }),
        )
        .toBeLessThan(5);
    };
    for (const width of [1297, 796, 430]) {
      await page.setViewportSize({ width, height: 791 });
      for (const expanded of [false, true]) {
        const toggle = page.locator(".input-lane .lane-toggle").first();
        if ((await toggle.getAttribute("aria-expanded")) !== String(expanded))
          await toggle.click();
        await page.locator("#process-heading").scrollIntoViewIfNeeded();
        await tag.scrollIntoViewIfNeeded();
        await expect(tag).toBeVisible();
        await expect(tag).toBeInViewport();
        await expectAttached();
        await expect(arrow).toHaveAttribute("marker-end", "url(#arrow)");
        await page.screenshot({
          path: testInfo.outputPath(
            `${caseId}-inputs-${width}-${expanded ? "expanded" : "compact"}.png`,
          ),
        });
      }
    }
    await tag.click();
    const detail = page.getByRole("dialog");
    await expect(detail).toContainText("Design request");
    if (scope === "run") {
      await expect(detail).toContainText("Workflow entry");
      await expect(detail).toContainText(
        "activity-specific consumption was not retained",
      );
      await expect(detail).not.toContainText("Recorded inputs used by");
    } else {
      await expect(detail).toContainText(
        "Recorded inputs used by Create part geometry",
      );
    }
    await detail.getByRole("button", { name: "Close details" }).click();
    await page.locator("[data-diagram-zoom]").fill("75");
    await expectAttached();
  }
  expect(remoteRequests).toEqual([]);
  expect(errors).toEqual([]);
});

test("@live campaign CAD review presents useful visual evidence offline", async ({
  page,
}, testInfo) => {
  test.skip(
    !reportPath,
    "Set WRIGHT_TRACE_CAMPAIGN_REPORT to an extracted report index.",
  );
  const remoteRequests: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.route(/^https?:/, (route) => {
    remoteRequests.push(route.request().url());
    return route.abort();
  });

  await page.setViewportSize({ width: 1297, height: 900 });
  await page.goto(pathToFileURL(resolve(reportPath!)).href);

  const inputVisual = page.locator(".input-visual");
  await expect(inputVisual).toHaveCount(1);
  expect(
    await inputVisual
      .locator("img")
      .evaluate(
        (image: HTMLImageElement) =>
          image.complete &&
          image.naturalWidth > 100 &&
          image.naturalHeight > 100,
      ),
  ).toBe(true);

  const viewers = page.locator(".result-band .stl-viewer");
  await expect(viewers).toHaveCount(2);
  await expect(viewers.locator("canvas")).toHaveCount(2);
  for (let index = 0; index < 2; index += 1) {
    const viewer = viewers.nth(index);
    await expect(viewer).toBeVisible();
    expect(
      await viewer.locator("canvas").evaluate(
        (canvas: HTMLCanvasElement) =>
          new Promise<number>((done) =>
            requestAnimationFrame(() => {
              const gl =
                canvas.getContext("webgl2") || canvas.getContext("webgl");
              if (!gl || canvas.width === 0 || canvas.height === 0)
                return done(0);
              const pixels = new Uint8Array(canvas.width * canvas.height * 4);
              gl.readPixels(
                0,
                0,
                canvas.width,
                canvas.height,
                gl.RGBA,
                gl.UNSIGNED_BYTE,
                pixels,
              );
              let geometryPixels = 0;
              for (let offset = 0; offset < pixels.length; offset += 4) {
                if (
                  Math.abs(pixels[offset] - 19) > 4 ||
                  Math.abs(pixels[offset + 1] - 28) > 4 ||
                  Math.abs(pixels[offset + 2] - 43) > 4
                )
                  geometryPixels += 1;
              }
              done(geometryPixels);
            }),
          ),
      ),
    ).toBeGreaterThan(100);
  }
  await expect(page.locator(".model-frame figcaption")).toContainText([
    "Enclosure concept A",
    "Enclosure concept B",
  ]);
  const cfdVisuals = page.locator(".outputs-section .image-frame img");
  await expect(cfdVisuals).toHaveCount(2);
  expect(
    await cfdVisuals.evaluateAll((images) =>
      images.every(
        (image) =>
          (image as HTMLImageElement).complete &&
          (image as HTMLImageElement).naturalWidth === 2200 &&
          (image as HTMLImageElement).naturalHeight === 990,
      ),
    ),
  ).toBe(true);
  await expect(page.locator(".image-frame figcaption")).toContainText([
    "Airflow comparison",
    "Temperature comparison",
  ]);
  await page.screenshot({
    path: testInfo.outputPath("cad-review-desktop.png"),
  });
  await page
    .locator(".outputs-section")
    .screenshot({ path: testInfo.outputPath("cad-review-outputs.png") });

  await expect(page.locator(".edge-tag")).toHaveCount(10);
  const requirementsLane = page.locator(".lane").filter({
    has: page.getByRole("button", {
      name: "Requirements & design basis",
      exact: true,
    }),
  });
  await requirementsLane
    .getByRole("button", { name: "Requirements & design basis", exact: true })
    .click();
  const researchVisuals = requirementsLane.locator(".step-visuals img");
  await expect(researchVisuals).toHaveCount(2);
  expect(
    await researchVisuals.evaluateAll((images) =>
      images.every(
        (image) =>
          (image as HTMLImageElement).complete &&
          (image as HTMLImageElement).naturalWidth > 100,
      ),
    ),
  ).toBe(true);
  const cadLane = page.locator(".lane").filter({
    has: page.getByRole("button", { name: "CAD engineering", exact: true }),
  });
  await cadLane
    .getByRole("button", { name: "CAD engineering", exact: true })
    .click();
  await expect(cadLane).toHaveAttribute("data-expanded", "true");
  await expect(page.locator(".lane[data-expanded=true]")).toHaveCount(2);
  const resultsLane = page.locator(".lane").filter({
    has: page.getByRole("button", {
      name: "Verification & results",
      exact: true,
    }),
  });
  await resultsLane
    .getByRole("button", { name: "Verification & results", exact: true })
    .click();
  await expect(resultsLane.locator(".step-visuals img")).toHaveCount(2);
  await expect(resultsLane.locator(".step-visuals span")).toContainText([
    "Airflow comparison",
    "Temperature comparison",
  ]);
  await page.screenshot({
    path: testInfo.outputPath("cad-review-expanded-process.png"),
  });

  const inspectionStep = page
    .locator(".activity-column")
    .filter({ hasText: "Inspect CAD exports" });
  await inspectionStep
    .getByRole("button", { name: /CAD export inspection/ })
    .click();
  const detail = page.getByRole("dialog");
  await expect(detail).toContainText("All 14 expected CAD and CFD exports");
  await expect(detail).toContainText("14 / 14 SHA-256 matches");
  await expect(detail).not.toContainText("Bytes");
  await expect(detail.locator(".record-table")).toContainText(
    "Verified export identities 14",
  );
  await detail.getByRole("button", { name: "Close details" }).click();

  expect(remoteRequests).toEqual([]);
  expect(pageErrors).toEqual([]);

  await page.setViewportSize({ width: 430, height: 860 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect(inputVisual).toBeVisible();
  await expect(viewers.first()).toBeVisible();
  expect((await viewers.first().boundingBox())!.width).toBeLessThanOrEqual(398);
  await page.screenshot({ path: testInfo.outputPath("cad-review-mobile.png") });
});

test("@live all campaign reviews remain usable offline", async ({ page }) => {
  test.setTimeout(120_000);
  test.skip(
    !campaignRoot,
    "Set WRIGHT_TRACE_CAMPAIGN_ROOT to the generated campaign directory.",
  );
  const root = resolve(campaignRoot!);
  const catalog = JSON.parse(
    readFileSync(resolve(root, "catalog.json"), "utf8"),
  ) as {
    reports: { case_id: string; report_path: string }[];
  };
  expect(catalog.reports).toHaveLength(30);
  const remoteRequests: string[] = [];
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.route(/^https?:/, (route) => {
    remoteRequests.push(route.request().url());
    return route.abort();
  });

  for (const report of catalog.reports) {
    const localReport = resolve(root, report.report_path);
    expect(dirname(localReport).startsWith(root)).toBe(true);
    await page.goto(pathToFileURL(localReport).href);
    await expect(
      page.locator(".step-node").first(),
      report.case_id,
    ).toBeVisible();
    await page.locator(".step-node").first().click();
    await expect(page.getByRole("dialog"), report.case_id).toBeVisible();
    await page.getByRole("button", { name: "Close details" }).click();
  }

  expect(remoteRequests).toEqual([]);
  expect(pageErrors).toEqual([]);
});

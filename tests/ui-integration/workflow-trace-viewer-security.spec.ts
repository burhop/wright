import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { expect, test } from "@playwright/test";

test.use({ launchOptions: { args: ["--enable-unsafe-swiftshader"] } });

test("paints a model without insecure randomness or network access", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  const requests: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route(/^https?:/, (route) => {
    requests.push(route.request().url());
    return route.abort();
  });
  await page.setContent(
    '<div id="model" style="width:480px;height:360px"></div>',
  );
  await page.evaluate(() => {
    const original = globalThis.crypto.getRandomValues.bind(globalThis.crypto);
    const observed = window as unknown as { secureViewerCalls: number };
    observed.secureViewerCalls = 0;
    Object.defineProperty(globalThis.crypto, "getRandomValues", {
      value: (values: Uint32Array) => {
        observed.secureViewerCalls++;
        return original(values);
      },
    });
    Math.random = () => {
      throw new Error("Insecure random source used");
    };
  });
  await page.addScriptTag({
    content: readFileSync(
      resolve(
        "packages/workspace_service/src/workspace_service/workflow_trace/portable/stl-viewer.js",
      ),
      "utf8",
    ),
  });
  await page.evaluate(() => {
    const source =
      "solid test\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 10 0 0\nvertex 0 10 0\nendloop\nendfacet\nendsolid test";
    const viewer = window as unknown as {
      WrightSTLViewer: {
        mount: (element: HTMLElement, source: string, label: string) => void;
      };
    };
    viewer.WrightSTLViewer.mount(
      document.getElementById("model")!,
      btoa(source),
      "Test mesh",
    );
  });
  await expect(page.locator("#model")).toHaveAttribute(
    "data-viewer-state",
    "ready",
  );
  await expect(
    page.getByRole("img", { name: "Interactive 3D view of Test mesh" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () =>
        (window as unknown as { secureViewerCalls: number }).secureViewerCalls,
    ),
  ).toBeGreaterThan(0);
  const painted = await page.locator("canvas").evaluate(
    (canvas: HTMLCanvasElement) =>
      new Promise<{ count: number; total: number }>((done) =>
        requestAnimationFrame(() => {
          const gl = canvas.getContext("webgl2")!;
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
          let count = 0;
          for (let index = 0; index < pixels.length; index += 4)
            if (
              Math.abs(pixels[index] - 19) > 4 ||
              Math.abs(pixels[index + 1] - 28) > 4 ||
              Math.abs(pixels[index + 2] - 43) > 4
            )
              count++;
          done({ count, total: canvas.width * canvas.height });
        }),
      ),
  );
  expect(painted.count).toBeGreaterThan(100);
  expect(painted.count).toBeLessThan(painted.total);
  expect(errors).toEqual([]);
  expect(requests).toEqual([]);
  await page.screenshot({
    path: testInfo.outputPath("secure-offline-model.png"),
  });
});

test("paints an included PDF and keeps zoom usable without network access", async ({
  page,
}, testInfo) => {
  const root = mkdtempSync(join(tmpdir(), "wright-trace-pdf-"));
  try {
    const urls = JSON.parse(
      execFileSync(
        "uv",
        [
          "run",
          "python",
          "tests/ui-integration/fixtures/build-workflow-trace-export.py",
          root,
          "pdf",
        ],
        { encoding: "utf8" },
      ),
    ) as { full_data: string };
    const requests: string[] = [];
    await page.route(/^https?:/, (route) => {
      requests.push(route.request().url());
      return route.abort();
    });
    await page.goto(urls.full_data);
    await page
      .getByRole("button", { name: "Run-level files (1)", exact: true })
      .click();
    const dialog = page.getByRole("dialog");
    await dialog.getByRole("button", { name: /^Housing/ }).click();
    const viewer = dialog.locator("[data-pdf-viewer]");
    await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
    const canvas = viewer.locator("canvas");
    await expect(canvas).toBeVisible();
    await expect(canvas).toBeInViewport();
    const observePaint = (element: HTMLCanvasElement) => {
      const pixels = element
        .getContext("2d")!
        .getImageData(0, 0, element.width, element.height).data;
      let orange = 0;
      for (let i = 0; i < pixels.length; i += 4)
        if (
          Math.abs(pixels[i] - 220) < 25 &&
          Math.abs(pixels[i + 1] - 60) < 25 &&
          Math.abs(pixels[i + 2] - 20) < 25
        )
          orange++;
      return {
        orange,
        total: element.width * element.height,
        width: element.width,
      };
    };
    const painted = await canvas.evaluate(observePaint);
    expect(painted.orange).toBeGreaterThan(painted.total / 2);
    await viewer.getByRole("button", { name: "Zoom in", exact: true }).click();
    await expect(viewer.locator("[data-pdf-scale]")).toHaveText("125%");
    await expect(viewer).toHaveAttribute("data-pdf-state", "ready");
    const zoomed = await canvas.evaluate(observePaint);
    expect(zoomed.width).toBeGreaterThan(painted.width);
    expect(zoomed.orange).toBeGreaterThan(zoomed.total / 2);
    await expect(
      viewer.getByRole("button", { name: "Zoom out", exact: true }),
    ).toBeEnabled();
    expect(requests).toEqual([]);
    await page.screenshot({
      path: testInfo.outputPath("secure-offline-pdf.png"),
    });
    await page.goto("about:blank");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("renders Markdown tables while keeping executable content inert offline", async ({
  page,
}) => {
  const requests: string[] = [];
  await page.route(/^https?:/, (route) => {
    requests.push(route.request().url());
    return route.abort();
  });
  await page.setContent('<div id="document"></div>');
  await page.addScriptTag({
    content: readFileSync(
      resolve(
        "packages/workspace_service/src/workspace_service/workflow_trace/portable/document-viewer.js",
      ),
      "utf8",
    ),
  });
  await page.evaluate(() => {
    const state = window as unknown as {
      markdownExecuted: boolean;
      WrightDocumentViewer: { markdown: (source: string) => string };
    };
    state.markdownExecuted = false;
    document.getElementById("document")!.innerHTML =
      state.WrightDocumentViewer.markdown(
        '## Synthetic result\n\n| Load | Value |\n| --- | --- |\n| Design load | 20 N |\n\n<img src="https://invalid.example/image" onerror="window.markdownExecuted=true">\n\n[unsafe](javascript:window.markdownExecuted=true)',
      );
  });
  await expect(
    page.getByRole("heading", { name: "Synthetic result" }),
  ).toBeVisible();
  await expect(page.getByRole("table")).toContainText("20 N");
  await expect(
    page.locator(
      '#document img, #document script, #document iframe, #document a[href^="javascript:"]',
    ),
  ).toHaveCount(0);
  expect(
    await page.evaluate(
      () =>
        (window as unknown as { markdownExecuted: boolean }).markdownExecuted,
    ),
  ).toBe(false);
  expect(requests).toEqual([]);
});

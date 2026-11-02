import { readFileSync } from "node:fs";
import { resolve } from "node:path";
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

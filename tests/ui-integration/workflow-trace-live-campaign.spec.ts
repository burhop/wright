import { execFileSync } from "node:child_process";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  renameSync,
  rmSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

import { expect, test } from "@playwright/test";

const workspaceId = process.env.WRIGHT_TRACE_LIVE_WORKSPACE_ID;
const sessionId = process.env.WRIGHT_TRACE_LIVE_SESSION_ID;
const reviewRoot = process.env.WRIGHT_TRACE_LIVE_REVIEW_ROOT;
const evidenceDir = resolve(
  process.cwd(),
  "specs/083-workflow-trace-review/evidence/live-campaign",
);

test.describe("@live retained campaign Trace review", () => {
  test.skip(
    !workspaceId || !sessionId || !reviewRoot,
    "Set the feature-083 live review workspace environment variables.",
  );

  test("opens a real retained run from Workflows and exports its evidence", async ({
    page,
    request,
  }) => {
    const index = JSON.parse(
      readFileSync(resolve(reviewRoot!, "trace-review-index.json"), "utf8"),
    ) as {
      indexed_runs: number;
      runs: Array<{
        case_id: string;
        workflow_path: string;
        run_path: string;
        run_id: string;
      }>;
    };
    expect(index.indexed_runs).toBe(24);
    for (const run of index.runs) {
      const response = await request.get(
        `/api/workspace/workflow-sources/run-trace?session_id=${encodeURIComponent(sessionId!)}&run_path=${encodeURIComponent(run.run_path)}`,
      );
      expect(response.status(), run.case_id).toBe(200);
      const trace = (await response.json()) as {
        run: { run_id: string; state: string };
        final_outputs: unknown[];
      };
      expect(trace.run.run_id).toBe(run.run_id);
      expect(trace.run.state).toBe("succeeded");
      expect(trace.final_outputs.length).toBeGreaterThan(0);
    }

    await page.goto(`/workspace/${workspaceId}`);
    await page.getByTestId("activity-bar-workflows-btn").click();
    await expect(page).toHaveURL(/workflow=canonical/);
    await page.getByTestId("workflow-file-menu").click();
    await page.getByTestId("workflow-file-open").click();
    await page
      .getByTestId(
        "workflow-file-choice-workflows/printed-replacement-part-01.workflow.wflow",
      )
      .click();
    await expect(page).toHaveURL(/printed-replacement-part-01/);

    const activeWorkflow = page.locator(
      '[data-testid="retained-workspace-workflow-panel"][aria-hidden="false"]',
    );
    await activeWorkflow
      .getByTestId("workflow-recovery-run-details-toggle")
      .click();
    const history = activeWorkflow.getByTestId("workflow-run-history");
    await history.locator(":scope > summary").click();
    await history
      .locator("details > summary")
      .filter({ hasText: /^Completed/ })
      .click();
    const tracePage = activeWorkflow.getByTestId("workflow-trace-page");
    await expect(tracePage).toBeVisible();
    await expect(page.getByRole("region", { name: "Run results" })).toBeVisible();
    await expect(page.getByText("Created artifacts")).toBeVisible();
    await expect(
      page.getByTestId("rivet-run-result-mesh-preview.png"),
    ).toBeVisible();
    await expect(
      page.getByRole("img", {
        name: "Recorded preview for mesh-preview.png",
      }),
    ).toBeVisible();

    await page.getByRole("button", { name: "Process" }).click();
    const graph = page.getByLabel("Executed graph Printed Replacement Part 01");
    await expect(graph.locator(".react-flow__node")).toHaveCount(4);
    await graph.locator(".react-flow__node").nth(1).click();
    await expect(
      page.getByRole("complementary", { name: "Selected process detail" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Close process detail" }).click();
    await page.getByRole("button", { name: "Results" }).click();

    mkdirSync(evidenceDir, { recursive: true });
    await tracePage.screenshot({
      path: resolve(evidenceDir, "real-campaign-results.png"),
    });
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(tracePage).toBeVisible();
    await expect(
      page.getByRole("img", {
        name: "Recorded preview for mesh-preview.png",
      }),
    ).toBeVisible();
    await tracePage.screenshot({
      path: resolve(evidenceDir, "real-campaign-mobile.png"),
    });
    const traceBounds = await tracePage.boundingBox();
    expect(traceBounds).not.toBeNull();
    expect(traceBounds!.x).toBeGreaterThanOrEqual(0);
    expect(traceBounds!.width).toBeLessThanOrEqual(390);
    await page.setViewportSize({ width: 1280, height: 720 });

    await page.getByText("Export review").click();
    const reportDownload = page.waitForEvent("download");
    await page.getByRole("button", { name: "Report ZIP" }).click();
    const reportOnlyPath = resolve(evidenceDir, "report-only.zip");
    await (await reportDownload).saveAs(reportOnlyPath);
    const fullDownload = page.waitForEvent("download");
    await page.getByRole("button", { name: "Report and data ZIP" }).click();
    const fullDataPath = resolve(evidenceDir, "report-and-data.zip");
    await (await fullDownload).saveAs(fullDataPath);

    await page.getByText("Export review").click();
    await page
      .getByTestId("rivet-run-result-source_mesh.stl")
      .getByRole("button", { name: "Open artifact" })
      .click();
    await expect(page.getByRole("tab", { name: "source_mesh.stl" })).toBeVisible();
    const canvas = page.getByTestId("3d-canvas");
    await expect(canvas).toBeVisible();
    const renderedPixels = await canvas.evaluate(
      (element) =>
        new Promise<number>((done) => {
          requestAnimationFrame(() => {
            const rendered = element as HTMLCanvasElement;
            const gl =
              rendered.getContext("webgl2") || rendered.getContext("webgl");
            if (!gl || rendered.width === 0 || rendered.height === 0) {
              done(0);
              return;
            }
            const pixels = new Uint8Array(
              rendered.width * rendered.height * 4,
            );
            gl.readPixels(
              0,
              0,
              rendered.width,
              rendered.height,
              gl.RGBA,
              gl.UNSIGNED_BYTE,
              pixels,
            );
            let visible = 0;
            for (let offset = 0; offset < pixels.length; offset += 4) {
              if (
                pixels[offset] !== 0 ||
                pixels[offset + 1] !== 0 ||
                pixels[offset + 2] !== 0
              ) {
                visible += 1;
              }
            }
            done(visible);
          });
        }),
    );
    expect(renderedPixels).toBeGreaterThan(100);

    const offlineRoot = mkdtempSync(join(tmpdir(), "wright-trace-live-export-"));
    try {
      const extracted = [
        { archive: fullDataPath, name: "full-data" },
        { archive: reportOnlyPath, name: "report-only" },
      ].map(({ archive, name }) => {
        const original = join(offlineRoot, `${name}-original`);
        const relocated = join(offlineRoot, `${name}-relocated`);
        mkdirSync(original);
        execFileSync("unzip", ["-q", archive, "-d", original]);
        renameSync(original, relocated);
        return { name, root: relocated };
      });
      const networkRequests: string[] = [];
      await page.route("http://**/*", (route) => {
        networkRequests.push(route.request().url());
        return route.abort();
      });
      await page.route("https://**/*", (route) => {
        networkRequests.push(route.request().url());
        return route.abort();
      });

      const fullData = extracted.find(({ name }) => name === "full-data")!;
      await page.goto(pathToFileURL(join(fullData.root, "index.html")).href);
      await expect(
        page.getByRole("heading", { name: "Printed Replacement Part 01" }),
      ).toBeVisible();
      await expect(
        page.getByText("Replacement part design", { exact: true }).first(),
      ).toBeVisible();
      await expect(
        page.getByRole("button", { name: "Files from Create part geometry (2)", exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole("img", {
          name: "Replacement part design",
        }),
      ).toBeVisible();
      await expect(
        page.getByRole("button", { name: /Part mesh after cleanup/ }).first(),
      ).toBeVisible();
      await page.screenshot({
        path: resolve(evidenceDir, "standalone-report.png"),
        fullPage: true,
      });

      const reportOnly = extracted.find(({ name }) => name === "report-only")!;
      await page.goto(pathToFileURL(join(reportOnly.root, "index.html")).href);
      await expect(
        page.getByRole("heading", { name: "Printed Replacement Part 01" }),
      ).toBeVisible();
      await expect(
        page.getByRole("img", {
          name: "Replacement part design",
        }),
      ).toBeVisible();
      await expect(
        page.getByRole("button", { name: /Part mesh after cleanup/ }).first(),
      ).toBeVisible();
      await expect(
        page.getByText("Report with recorded images / originals excluded", { exact: true }),
      ).toBeVisible();
      expect(networkRequests).toEqual([]);
    } finally {
      rmSync(offlineRoot, { recursive: true, force: true });
    }
  });
});

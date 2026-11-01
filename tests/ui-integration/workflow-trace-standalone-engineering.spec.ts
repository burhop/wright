import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  renameSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { expect, test } from "@playwright/test";

const sessionId = process.env.WRIGHT_TRACE_LIVE_SESSION_ID;
const evidenceDir = resolve(
  "specs/083-workflow-trace-review/evidence/live-campaign",
);

test("@live standalone engineering review uses real retained campaign evidence offline", async ({
  page,
  request,
}) => {
  test.skip(
    !sessionId,
    "Set WRIGHT_TRACE_LIVE_SESSION_ID for the retained campaign workspace.",
  );
  mkdirSync(evidenceDir, { recursive: true });
  const root = mkdtempSync(join(tmpdir(), "wright-engineering-review-"));
  const requests: string[] = [];
  const errors: string[] = [];
  let originalAssumptions: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route(/^https?:/, (route) => {
    requests.push(route.request().url());
    return route.abort();
  });
  try {
    for (const mode of ["full_data", "report_only"]) {
      const response = await request.get(
        "/api/workspace/workflow-sources/run-trace/export",
        {
          params: {
            session_id: sessionId!,
            run_path: "runs/printed-replacement-part-01/attempt-003.json",
            mode,
          },
        },
      );
      expect(response.status()).toBe(200);
      const archive = resolve(
        evidenceDir,
        mode === "full_data" ? "report-and-data.zip" : "report-only.zip",
      );
      writeFileSync(archive, await response.body());
      const original = join(root, `${mode}-original`);
      const relocated = join(root, `${mode}-relocated`);
      execFileSync("unzip", ["-q", archive, "-d", original]);
      renameSync(original, relocated);
      const manifest = JSON.parse(
        readFileSync(join(relocated, "manifest.json"), "utf8"),
      );
      expect(
        JSON.parse(readFileSync(join(relocated, "report/report.json"), "utf8"))
          .run.run_id,
      ).toBe(manifest.run_id);
      expect(
        JSON.parse(
          readFileSync(join(relocated, "evidence/run-evidence.json"), "utf8"),
        ).run_id,
      ).toBe(manifest.run_id);
      expect(manifest.entries).toHaveLength(22);
      expect(
        manifest.entries.filter(
          (item: { role: string }) => item.role === "input",
        ),
      ).toHaveLength(5);
      if (mode === "full_data") {
        const source = manifest.entries.find(
          (item: { name: string }) => item.name === "source-model-report.json",
        );
        originalAssumptions = JSON.parse(
          readFileSync(join(relocated, source.package_path), "utf8"),
        ).unresolved_assumptions;
      }
      for (const item of manifest.entries) {
        if (item.package_path) {
          const bytes = readFileSync(join(relocated, item.package_path));
          expect(createHash("sha256").update(bytes).digest("hex")).toBe(
            item.digest,
          );
        } else expect(mode).toBe("report_only");
      }
      await page.setViewportSize({ width: 1440, height: 1100 });
      await page.goto(pathToFileURL(join(relocated, "index.html")).href);
      await expect(
        page.getByRole("heading", { name: "Printed Replacement Part 01" }),
      ).toBeVisible();
      await expect(
        page.locator(".page > section > .section-heading h2"),
      ).toHaveText(["Inputs", "Outputs", "Process & handoffs"]);
      await expect(
        page.getByRole("heading", { name: "Supporting documents" }),
      ).toHaveCount(0);
      await expect(
        page.getByText("Technical archive", { exact: true }),
      ).toHaveCount(0);
      const inputs = page.getByRole("region", { name: "Inputs", exact: true });
      await expect(inputs).toContainText(
        "The plastic focus wheel on our training telescope cracked.",
      );
      await expect(inputs).not.toContainText(
        "The original prompt was not retained",
      );
      await inputs.getByRole("button", { name: "Read full prompt" }).click();
      const originalPrompt = readFileSync(
        resolve(
          "tests/datasets/engineering-workflows/scenarios/printed-replacement-part/01-observatory-focus-wheel/prompt.txt",
        ),
        "utf8",
      );
      expect(
        await page
          .getByRole("dialog")
          .locator(".prompt-text")
          .first()
          .textContent(),
      ).toBe(originalPrompt);
      await expect(page.getByRole("dialog")).toContainText(
        "Original input verified against this run's campaign dataset.",
      );
      await page.getByRole("button", { name: "Close details" }).click();
      await expect(inputs.locator(".input-visual")).toHaveCount(1);
      await inputs
        .locator(".input-visual")
        .getByRole("button", { name: "View" })
        .click();
      expect(
        await page
          .getByRole("dialog")
          .locator(".detail-body > img")
          .evaluate(
            (image: HTMLImageElement) =>
              image.complete && image.naturalWidth > 100,
          ),
      ).toBe(true);
      await page
        .getByRole("dialog")
        .getByText("Editable source", { exact: true })
        .click();
      await expect(page.getByRole("dialog")).toContainText(
        "two formats of the same sketch",
      );
      await page
        .getByRole("dialog")
        .getByRole("button", { name: /Design sketch \(SVG\)/ })
        .click();
      await expect(page.getByRole("dialog")).toContainText("Vector drawing");
      expect(
        await page
          .getByRole("dialog")
          .locator(".detail-body > img")
          .evaluate(
            (img: HTMLImageElement) => img.complete && img.naturalWidth > 100,
          ),
      ).toBe(true);
      await page.getByRole("button", { name: "Close details" }).click();
      await expect(inputs.locator(".section-heading button")).toHaveCount(0);
      await expect(inputs.locator(".section-heading p")).toHaveText(
        "1 prompt / 1 image / 2 documents",
      );
      await expect(
        inputs.getByRole("heading", {
          name: "Other supplied files",
          exact: true,
        }),
      ).toBeVisible();
      await expect(
        inputs.locator(".input-attachments .input-link strong"),
      ).toHaveText(["Design context", "Requester profile"]);
      await expect(inputs.locator(".input-more")).toHaveCount(0);
      await expect(inputs.locator(".input-context .input-link")).toBeHidden();
      await inputs.locator(".input-context > summary").focus();
      await page.keyboard.press("Enter");
      await inputs
        .locator(".input-context")
        .getByRole("button", { name: /Supporting context/ })
        .click();
      await expect(page.getByRole("dialog")).toContainText(
        "Reassembled for this review",
      );
      await expect(page.getByRole("dialog")).toContainText(
        "original assembled execution snapshot was not transferred",
      );
      await expect(
        page
          .getByRole("dialog")
          .getByRole("heading", { name: "Source documents" }),
      ).toBeVisible();
      if (mode === "full_data") {
        const assembled = manifest.entries.find(
          (item: { role: string }) => item.role === "input_reconstruction",
        );
        const originals = ["user-profile.md", "context.md"].map((name) => {
          const item = manifest.entries.find(
            (entry: { name: string }) => entry.name === name,
          );
          return readFileSync(join(relocated, item.package_path), "utf8");
        });
        expect(
          readFileSync(join(relocated, assembled.package_path), "utf8"),
        ).toBe(originals.join("\n\n"));
      }
      await page.getByRole("button", { name: "Close details" }).click();
      await inputs.locator(".input-context > summary").click();
      if (mode === "full_data") {
        await page.setViewportSize({ width: 909, height: 791 });
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.screenshot({
          path: resolve(
            evidenceDir,
            "engineering-review-supplied-inputs-909.png",
          ),
        });
        await page.setViewportSize({ width: 1440, height: 1100 });
      }
      await expect(page.locator(".step-node")).toHaveCount(4);
      await expect(page.locator(".step-node .node-tool b")).toHaveText([
        "Blender",
        "Blender",
        "Bambu Studio",
        "Wright AutoTest",
      ]);
      await expect(
        page.getByRole("group", { name: "Process detail level" }),
      ).toHaveCount(0);
      await expect(page.locator(".lane[data-expanded=false]")).toHaveCount(3);
      await expect(page.locator(".step-outputs").first()).toBeHidden();
      await expect(page.locator(".step-node .node-tool").first()).toBeVisible();
      await expect(
        page.locator(".lane > .lane-title > span:last-child"),
      ).toHaveText([
        "Design & mesh preparation",
        "Manufacturing preparation",
        "Transfer authorization",
      ]);
      await expect(page.locator(".input-feed").first()).toBeVisible();
      const inputLane = page.locator(".input-lane").first();
      await expect(inputLane.locator(".input-card-heading strong")).toHaveText([
        "Design request",
        "Design sketch",
        "Supporting context",
      ]);
      await expect(
        inputLane.locator(".input-card-details").first(),
      ).toBeHidden();
      await expect(inputLane.locator(".feed-recipient")).toBeHidden();
      expect((await inputLane.boundingBox())!.height).toBeLessThanOrEqual(175);
      expect(
        (await inputLane.locator(".input-card").first().boundingBox())!.width,
      ).toBeLessThanOrEqual(128);
      await inputLane
        .getByRole("button", { name: "Design request", exact: true })
        .click();
      await expect(
        page.getByRole("dialog").locator(".prompt-text").first(),
      ).toHaveText(originalPrompt);
      await page.getByRole("button", { name: "Close details" }).click();
      expect(
        (await page.locator(".step-node").first().boundingBox())!.width,
      ).toBeLessThanOrEqual(128);
      await page.locator(".step-node").first().click();
      await expect(page.getByRole("dialog")).toContainText("Blender");
      await page
        .getByRole("dialog")
        .getByRole("button", {
          name: "Execution source: Campaign execution checkpoint",
        })
        .click();
      await expect(page.getByRole("dialog")).toContainText(
        "printed-replacement-part-01/attempt-003",
      );
      await expect(page.getByRole("dialog")).toContainText(
        "one Blender construct/export pass",
      );
      await page.getByRole("button", { name: "Close details" }).click();
      await page
        .getByRole("button", { name: "Design & mesh preparation", exact: true })
        .focus();
      await page.keyboard.press("Enter");
      await expect(page.locator(".lane[data-expanded=true]")).toHaveCount(1);
      await expect(page.locator(".lane[data-expanded=false]")).toHaveCount(2);
      await expect(page.locator(".lane .lane-title")).toHaveCount(3);
      await expect(
        page.getByText("Activity and handoff index", { exact: true }),
      ).toHaveCount(0);
      const feed = page.locator(".input-feed").first();
      const otherHeights = await page
        .locator(".lane")
        .evaluateAll((rows) =>
          rows.map((row) => row.getBoundingClientRect().height),
        );
      await inputLane.locator(".lane-toggle").focus();
      await page.keyboard.press("Enter");
      await expect(inputLane.locator(".lane-toggle")).toHaveAttribute(
        "aria-expanded",
        "true",
      );
      expect(
        await page
          .locator(".lane")
          .evaluateAll((rows) =>
            rows.map((row) => row.getBoundingClientRect().height),
          ),
      ).toEqual(otherHeights);
      await expect(feed.locator(".input-card-details").first()).toBeVisible();
      await expect(feed.locator(".input-card").last()).toContainText(
        "Assembled from",
      );
      await expect(feed.locator(".input-card-sources button")).toHaveCount(2);
      await feed
        .getByRole("button", { name: "Run inputs & context", exact: true })
        .click();
      await expect(
        page.getByRole("dialog").locator(".input-group"),
      ).toHaveCount(4);
      await expect(
        page.getByRole("dialog").locator(".input-group > summary"),
      ).toHaveText([
        "Prompts 1",
        "Images 1",
        "Documents 2",
        "Reassembled context 1",
      ]);
      await expect(
        page
          .getByRole("dialog")
          .getByRole("button", { name: /Supporting context/ }),
      ).toBeVisible();
      await page.getByRole("button", { name: "Close details" }).click();
      await expect(feed).toContainText(
        "The plastic focus wheel on our training telescope cracked.",
      );
      await expect(
        feed.getByRole("button", { name: "Create part geometry", exact: true }),
      ).toBeVisible();
      await feed.getByRole("button", { name: "Read supplied request" }).click();
      await expect(
        page.getByRole("dialog").locator(".prompt-text").first(),
      ).toHaveText(originalPrompt);
      await page.getByRole("button", { name: "Close details" }).click();
      expect(
        await feed
          .locator("img")
          .evaluate(
            (img: HTMLImageElement) => img.complete && img.naturalWidth > 100,
          ),
      ).toBe(true);
      await page
        .locator(".step-outputs")
        .first()
        .getByRole("button", { name: /Generated part model/ })
        .click();
      await expect(page.getByRole("dialog")).toContainText(
        "Generated in this run",
      );
      await expect(page.getByRole("dialog")).toContainText(
        "Produced by Create part geometry",
      );
      await page.getByRole("button", { name: "Close details" }).click();
      await expect(page.locator(".edge-tag")).toHaveCount(3);
      await expect(page.locator(".diagram .node-documents")).toHaveText([
        "All 2 files↗",
        "All 3 files↗",
        "All 8 files↗",
        "All 1 file↗",
      ]);
      const expectedFiles = [
        ["Generated part model", "Part design record"],
        [
          "Part mesh after cleanup",
          "Replacement part design",
          "Mesh repair and measurement report",
        ],
        [
          "Manufacturing package",
          "Slicer model preview",
          "Slicing results",
          "Print settings",
          "Printer settings",
          "Material settings",
          "Slicer log",
          "Slicer operation report",
        ],
        ["Transfer receipt"],
      ];
      for (let activity = 0; activity < 4; activity += 1) {
        const lane = page
          .locator(".activity-column")
          .nth(activity)
          .locator(
            "xpath=ancestor::div[contains(@class,'lane') and not(contains(@class,'lane-cell'))]",
          );
        if ((await lane.getAttribute("data-expanded")) === "false")
          await lane.locator(".lane-toggle").click();
        await page.locator(".node-documents").nth(activity).click();
        const filePanel = page.getByRole("dialog");
        await expect(
          filePanel.getByRole("heading", { name: "Documents & outputs" }),
        ).toBeVisible();
        expect(
          (
            await filePanel.locator(".document-link strong").allTextContents()
          ).sort(),
        ).toEqual(expectedFiles[activity].sort());
        if (activity === 2 && mode === "full_data")
          await page.screenshot({
            path: resolve(evidenceDir, "engineering-review-activity-files.png"),
          });
        for (const title of expectedFiles[activity]) {
          await filePanel
            .locator(".document-link")
            .filter({ has: page.getByText(title, { exact: true }) })
            .click();
          await expect(
            filePanel.getByRole("heading", {
              name: title,
              exact: true,
              level: 2,
            }),
          ).toBeVisible();
          if (title === "Slicer model preview") {
            await expect(filePanel).toContainText(
              "separate preview of the model with support geometry was not retained",
            );
            expect(
              await filePanel
                .locator(".detail-body > img")
                .evaluate(
                  (img: HTMLImageElement) =>
                    img.complete && img.naturalWidth > 100,
                ),
            ).toBe(true);
          }
          if (mode === "full_data")
            await expect(filePanel.locator("a.download")).toHaveCount(1);
          await filePanel
            .getByRole("button", { name: "Back", exact: true })
            .click();
        }
        await filePanel.getByRole("button", { name: "Close details" }).click();
      }
      expect(
        await page
          .locator(".result-band img")
          .evaluateAll((elements) =>
            elements.every(
              (element) =>
                (element as HTMLImageElement).complete &&
                (element as HTMLImageElement).naturalWidth > 100,
            ),
          ),
      ).toBe(true);
      await expect(page.locator("pre")).toHaveCount(0);
      await expect(page.locator("main")).not.toContainText(
        "1114664a543e4d8ea60c8b063c75f002",
      );
      await expect(
        page.getByText("Bambu PETG HF", { exact: true }),
      ).toBeVisible();
      await expect(page.locator(".outcome")).toContainText(
        "new six-scallop replacement handwheel",
      );
      await expect(page.locator(".image-frame figcaption")).toHaveText([
        "Replacement part designAfter digital mesh cleanupView",
      ]);
      await expect(page.locator(".result-band img")).toHaveCount(1);
      await expect(page.locator(".result-band")).not.toContainText(
        "Slicer model preview",
      );
      const printing = page.getByRole("region", {
        name: "3D printing",
        exact: true,
      });
      await expect(printing).toContainText("Bambu Lab P1S / 0.4 mm nozzle");
      await expect(printing).toContainText("0.20 mm / 35%");
      await expect(printing).toContainText(
        "Supports enabled; 0 support toolpath moves reported.",
      );
      await expect(printing).toContainText("Automatic tree supports");
      await expect(printing).toContainText("30 degrees");
      await expect(printing).toContainText(
        "A support-geometry preview was not retained for this run.",
      );
      await expect(
        printing.locator("dl > div").filter({ hasText: "Wall loops" }),
      ).toContainText("4");
      await expect(
        printing.locator("dl > div").filter({ hasText: "Infill pattern" }),
      ).toContainText("Grid");
      await printing.locator(".preparation-summary > summary").click();
      await expect(printing.locator(".preparation-summary")).toContainText(
        "Degenerate faces: 1 to 0",
      );
      await expect(printing.locator(".preparation-summary")).toContainText(
        "Model axes kept; lowest point moved to the build plate",
      );
      await expect(
        printing
          .locator(".preparation-summary dl > div")
          .filter({ hasText: "Voxel remeshing" }),
      ).toContainText("Not applied");
      await expect(
        printing
          .locator(".preparation-summary dl > div")
          .filter({ hasText: "Decimation" }),
      ).toContainText("Not applied");
      await printing
        .getByRole("button", {
          name: "Source: Mesh repair and measurement report",
        })
        .click();
      await expect(
        page.getByRole("dialog").getByRole("heading", {
          name: "Mesh repair and measurement report",
          exact: true,
        }),
      ).toBeVisible();
      await page.getByRole("button", { name: "Close details" }).click();
      await printing.locator(".preparation-summary > summary").click();
      await printing
        .getByRole("button", { name: "Print settings", exact: true })
        .click();
      await expect(
        page
          .getByRole("dialog")
          .getByRole("heading", { name: "3D printing settings" }),
      ).toBeVisible();
      await expect(page.getByRole("dialog")).toContainText("Wall loops");
      await page.getByRole("button", { name: "Close details" }).click();
      await expect(
        page.getByRole("button", { name: /Toolpath projection/ }),
      ).toHaveCount(0);
      const retainedProjection = manifest.entries.find(
        (item: { name: string }) => item.name === "support-preview.svg",
      );
      expect(retainedProjection.package_path).toBeTruthy();
      expect(
        readFileSync(join(relocated, retainedProjection.package_path), "utf8"),
      ).toContain("<svg");
      await expect(
        page.getByText("No physical printer dispatch", { exact: false }),
      ).toBeVisible();
      if (mode === "full_data")
        await page.screenshot({
          path: resolve(evidenceDir, "engineering-review-desktop.png"),
          fullPage: true,
        });

      const detail = page.getByRole("dialog");
      await page.setViewportSize({ width: 944, height: 791 });
      await page.evaluate(() => window.scrollTo(0, 0));
      if (mode === "full_data")
        await page.screenshot({
          path: resolve(evidenceDir, "engineering-review-inputs-outputs.png"),
        });
      for (let index = 0; index < 4; index += 1) {
        await page.locator(".step-node").nth(index).click();
        await expect(detail.locator(".detail-body > :first-child")).toHaveClass(
          "activity-purpose",
        );
        await expect(detail.locator(".activity-purpose")).toBeInViewport();
        await expect(detail).not.toContainText(originalPrompt.trim());
        await expect(detail.locator(".execution-facts")).toContainText(
          "Software used",
        );
        await expect(
          detail.getByRole("heading", { name: "Tool & execution" }),
        ).not.toBeVisible();
        await expect(
          detail.getByRole("heading", { name: "Work performed", exact: true }),
        ).toBeVisible();
        await expect(
          detail.getByRole("button", { name: /Toolpath projection/ }),
        ).toHaveCount(0);
        await expect(
          detail
            .locator(".execution-facts > div")
            .filter({ hasText: "Recorded activity passes" }),
        ).toContainText("1");
        if (index === 0)
          await expect(
            detail
              .locator(".activity-account")
              .getByRole("button", { name: "Design request", exact: true }),
          ).toBeVisible();
        if (index === 2)
          await expect(detail.locator(".execution-facts")).toContainText(
            "02.08.02.61",
          );
        if (index === 1) {
          await expect(detail.locator(".execution-facts")).toContainText(
            "Blender",
          );
          if (mode === "full_data")
            await page.screenshot({
              path: resolve(evidenceDir, "engineering-review-blender-tool.png"),
            });
        }
        if (mode === "full_data" && index === 0)
          await page.screenshot({
            path: resolve(
              evidenceDir,
              "engineering-review-activity-overview.png",
            ),
          });
        await detail
          .locator(".detail-body > .execution-record > summary")
          .click();
        await detail
          .locator(".execution-record .execution-record > summary")
          .click();
        await expect(
          detail.locator(".detail-body > .execution-record"),
        ).toContainText("Activity completed");
        if (index === 0) {
          await expect(
            detail.locator(".detail-body > .execution-record"),
          ).toContainText("constructed six-scallop wheel body");
          await expect(
            detail.locator(".detail-body > .execution-record"),
          ).toContainText(
            "4 requests across the whole run, not this activity's revision count",
          );
          if (mode === "full_data")
            await page.screenshot({
              path: resolve(
                evidenceDir,
                "engineering-review-execution-record.png",
              ),
            });
        }
        await detail.getByRole("button", { name: "Close details" }).click();
      }
      await page.setViewportSize({ width: 1440, height: 1100 });
      await page
        .locator(".step-node")
        .filter({ hasText: "Create part geometry" })
        .click();
      const assumptions = detail.locator(".assumptions-detail");
      await assumptions.locator("summary").click();
      await expect(assumptions.locator("li > p")).toHaveText(
        originalAssumptions,
      );
      await expect(assumptions).toContainText("approval is not implied");
      for (let index = 0; index < originalAssumptions.length; index += 1) {
        await assumptions
          .getByRole("button", { name: "Source: Part design record" })
          .nth(index)
          .click();
        await expect(
          detail.getByRole("heading", {
            name: "Part design record",
            exact: true,
          }),
        ).toBeVisible();
        await expect(detail.locator(".assumption-source li > p")).toHaveText(
          originalAssumptions,
        );
        await expect(detail.locator(".cited-statement > p")).toHaveText(
          originalAssumptions[index],
        );
        await expect(detail.locator(".cited-statement")).toBeInViewport();
        await expect(
          detail.getByRole("button", {
            name: "Recorded during: Create part geometry",
          }),
        ).toBeVisible();
        await expect(detail.locator(".assumption-source")).toContainText(
          "Sep 14, 2026",
        );
        await expect(
          detail.locator(".source-inputs .input-link strong"),
        ).toHaveText(["Design sketch", "Design request", "Supporting context"]);
        if (index === 0) {
          if (mode === "full_data")
            await page.screenshot({
              path: resolve(
                evidenceDir,
                "engineering-review-assumption-source.png",
              ),
            });
          await detail
            .locator(".source-inputs")
            .getByRole("button", { name: /Design request/ })
            .click();
          await expect(detail.locator(".prompt-text").first()).toHaveText(
            originalPrompt,
          );
          await detail
            .getByRole("button", { name: "Back", exact: true })
            .click();
          await expect(detail.locator(".cited-statement > p")).toHaveText(
            originalAssumptions[0],
          );
        }
        await detail.getByRole("button", { name: "Back", exact: true }).click();
        await expect(assumptions).toHaveAttribute("open", "");
      }
      await detail.getByRole("button", { name: "Close details" }).click();
      await page
        .locator(".step-node")
        .filter({ hasText: "Repair & measure mesh" })
        .click();
      await expect(
        detail.getByRole("heading", { name: "Mesh measurements" }),
      ).toBeVisible();
      await expect(
        detail.getByRole("row").filter({ hasText: "Degenerate faces" }),
      ).toHaveText("Degenerate faces10");
      await expect(
        detail.getByRole("row").filter({ hasText: "Merge tolerance" }),
      ).toContainText("0.001 mm");
      if (mode === "full_data")
        await page.screenshot({
          path: resolve(evidenceDir, "engineering-review-mesh-details.png"),
        });
      await detail
        .getByRole("button", {
          name: "Source: Mesh repair and measurement report",
        })
        .first()
        .click();
      await expect(
        detail.getByRole("heading", {
          name: "Mesh repair and measurement report",
          exact: true,
        }),
      ).toBeVisible();
      await detail.getByRole("button", { name: "Close details" }).click();

      await page
        .locator(".step-node")
        .filter({ hasText: "Authorize transfer" })
        .click();
      await expect(
        detail.getByRole("row").filter({ hasText: "Authorized by" }),
      ).toContainText("Engineering campaign automation");
      await expect(
        detail.getByRole("row").filter({ hasText: "Role" }),
      ).toContainText("Automated integration-test actor");
      await expect(
        detail.getByRole("row").filter({ hasText: "Human sign-off" }),
      ).toContainText("Not recorded");
      await expect(
        detail
          .getByRole("row")
          .filter({ hasText: "Physical printer transfer" }),
      ).toContainText("Not performed");
      if (mode === "full_data")
        await page.screenshot({
          path: resolve(evidenceDir, "engineering-review-authorization.png"),
        });
      await detail.getByRole("button", { name: "Close details" }).click();

      await page
        .locator(".edge-tag")
        .filter({ hasText: "Repaired geometry" })
        .click();
      await expect(detail).toContainText(
        "recorded input fingerprint matches the repaired model exactly",
      );
      await detail
        .getByRole("button", { name: "Part mesh after cleanup" })
        .click();
      await expect(
        detail.getByRole("img", { name: "Replacement part design" }),
      ).toBeVisible();
      if (mode === "full_data")
        await expect(
          detail.getByRole("link", { name: "Download original STL" }),
        ).toHaveAttribute("href", "outputs/output/repaired_mesh.stl");
      else await expect(detail).toContainText("original file is not included");
      await detail.getByRole("button", { name: "Close details" }).click();

      await page.setViewportSize({ width: 390, height: 844 });
      await page.evaluate(() => window.scrollTo(0, 0));
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth),
      ).toBeLessThanOrEqual(390);
      await expect(page.locator(".result-band img")).toHaveCount(1);
      await expect(inputs).toBeVisible();
      await expect(
        page.getByRole("heading", { name: "Printed Replacement Part 01" }),
      ).toBeVisible();
      if (mode === "full_data")
        await page.screenshot({
          path: resolve(evidenceDir, "engineering-review-mobile.png"),
          fullPage: true,
        });
      await page
        .locator(".step-node")
        .filter({ hasText: "Create part geometry" })
        .click();
      await assumptions.locator("summary").click();
      await assumptions
        .getByRole("button", { name: "Source: Part design record" })
        .first()
        .click();
      await expect(detail.locator(".cited-statement > p")).toHaveText(
        originalAssumptions[0],
      );
      expect(
        await detail.evaluate(
          (element) => element.scrollWidth <= element.clientWidth,
        ),
      ).toBe(true);
      if (mode === "full_data")
        await page.screenshot({
          path: resolve(
            evidenceDir,
            "engineering-review-assumption-source-mobile.png",
          ),
        });
      await detail.getByRole("button", { name: "Close details" }).click();
      await page.locator(".node-documents").nth(3).click();
      await expect(detail.locator(".document-link strong")).toHaveText([
        "Transfer receipt",
      ]);
      await detail.getByRole("button", { name: "Close details" }).click();
      await page
        .locator(".step-node")
        .filter({ hasText: "Authorize transfer" })
        .focus();
      await page.keyboard.press("Enter");
      await expect(detail.locator(".activity-purpose")).toBeInViewport();
      await expect(
        detail.getByRole("heading", { name: "Authorization record" }),
      ).toBeVisible();
      expect((await detail.boundingBox())!.width).toBeLessThanOrEqual(390);
      await detail.getByRole("button", { name: "Close details" }).click();
      for (const expandedRows of [[], [1], [0, 2]]) {
        const expandInputs = expandedRows.length > 0;
        if (
          (await inputLane
            .locator(".lane-toggle")
            .getAttribute("aria-expanded")) !== String(expandInputs)
        ) {
          await inputLane.locator(".lane-toggle").click();
        }
        for (let row = 0; row < 3; row += 1) {
          const toggle = page.locator(".lane > .lane-toggle").nth(row);
          if (
            (await toggle.getAttribute("aria-expanded")) !==
            String(expandedRows.includes(row))
          ) {
            await toggle.focus();
            await page.keyboard.press("Enter");
          }
        }
        await expect(page.locator(".lane[data-expanded=true]")).toHaveCount(
          expandedRows.length,
        );
        for (const width of [1440, 909, 702, 390]) {
          await page.setViewportSize({ width, height: 900 });
          await page.locator(".diagram").scrollIntoViewIfNeeded();
          await expect
            .poll(() =>
              page.evaluate(() => {
                const labels = [...document.querySelectorAll(".edge-tag")];
                const controls = [
                  ...document.querySelectorAll(
                    ".step-node,.output-link,.node-documents,.input-feed",
                  ),
                ].filter((element) => element.getClientRects().length);
                return labels.flatMap((label) => {
                  const a = label.getBoundingClientRect();
                  return controls
                    .filter((control) => {
                      const b = control.getBoundingClientRect();
                      return (
                        Math.min(a.right, b.right) - Math.max(a.left, b.left) >
                          2 &&
                        Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) >
                          2
                      );
                    })
                    .map(
                      (control) =>
                        `${label.textContent}: ${control.textContent}`,
                    );
                });
              }),
            )
            .toEqual([]);
          expect(
            await page.evaluate(() => document.documentElement.scrollWidth),
          ).toBeLessThanOrEqual(width);
          expect(
            await inputLane
              .locator(".input-card")
              .evaluateAll((cards) =>
                cards.every((card) => card.scrollWidth <= card.clientWidth + 1),
              ),
          ).toBe(true);
          if (!expandInputs && width > 520)
            expect((await inputLane.boundingBox())!.height).toBeLessThanOrEqual(
              175,
            );
          await expect
            .poll(() =>
              page.locator(".input-line[marker-end]").evaluate((element) => {
                const path = element as SVGPathElement;
                const end = path.getPointAtLength(path.getTotalLength());
                const diagram = document
                  .querySelector(".diagram")!
                  .getBoundingClientRect();
                const target = document
                  .querySelector(".step-block")!
                  .getBoundingClientRect();
                return (
                  Math.abs(
                    end.x + diagram.left - target.left - target.width / 2,
                  ) < 1 && Math.abs(end.y + diagram.top - target.top + 3) < 1
                );
              }),
            )
            .toBe(true);
          await expect(
            page.locator(".step-node .node-tool b").first(),
          ).toBeVisible();
          await page.locator(".edge-tag").first().click();
          await expect(
            detail.getByRole("heading", { name: "Transferred information" }),
          ).toBeVisible();
          await detail.getByRole("button", { name: "Close details" }).click();
          if (mode === "full_data")
            await page.screenshot({
              path: resolve(
                evidenceDir,
                `engineering-review-rows-${expandedRows.join("-") || "collapsed"}-${width}.png`,
              ),
              fullPage: true,
            });
          if (mode === "full_data" && width === 702) {
            await page
              .locator("#process-heading")
              .evaluate((element) =>
                element.scrollIntoView({ block: "start" }),
              );
            await page.screenshot({
              path: resolve(
                evidenceDir,
                `engineering-review-input-blocks-${expandInputs ? "expanded" : "compact"}-702.png`,
              ),
            });
          }
        }
      }
    }
    expect(requests).toEqual([]);
    expect(errors).toEqual([]);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

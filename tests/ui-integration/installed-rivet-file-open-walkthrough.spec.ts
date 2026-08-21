import { expect, test, type BrowserContext, type Page } from "@playwright/test";
import { copyFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

type StepState = "pass" | "blocked" | "pending";

interface EvidenceStep {
  id: string;
  state: StepState;
  label: string;
  summary: string;
  purpose: string;
  action: string;
  controls: string[];
  expected: string;
  actual: string;
  raw?: string;
  annotated?: string;
}

interface WalkthroughStatus {
  title: string;
  summary: string;
  overall: StepState;
  updated: string;
  manualSteps: Array<{ label: string; instruction: string }>;
  steps: EvidenceStep[];
}

const artifactRoot = process.env.WRIGHT_RIVET_FILE_WALKTHROUGH_ROOT;
const workspaceUrl =
  process.env.WRIGHT_RIVET_FILE_WORKSPACE_URL ||
  "/workspace/d2e3ecab-8406-4900-bfc3-e18c4984f203";
const workflowFilePath = "/workflows/rivet/workflow.rivet-project";

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

class WalkthroughEvidence {
  private diagnostics: string[] = [];
  private status: WalkthroughStatus;

  constructor(private readonly root: string) {
    for (const directory of [
      "playwright",
      "screenshots/raw",
      "screenshots/annotated",
      "trace",
    ]) {
      mkdirSync(path.join(root, directory), { recursive: true });
    }
    copyFileSync(
      __filename,
      path.join(root, "playwright", path.basename(__filename)),
    );
    writeFileSync(
      path.join(root, "progress.md"),
      "# Open a saved Rivet workflow from Workspace Files\n\n",
      "utf8",
    );
    this.status = {
      title: "Open a saved Rivet workflow from Workspace Files",
      summary: "The saved-workflow file-open path is under review.",
      overall: "pending",
      updated: new Date().toISOString(),
      manualSteps: [
        {
          label: "Open workspace files",
          instruction: "Click **Workspace Files** in the activity bar.",
        },
        {
          label: "Expand workflows",
          instruction: "Expand **workflows**, then expand **rivet**.",
        },
        {
          label: "Open workflow",
          instruction: "Double-click **workflow.rivet-project**.",
        },
        {
          label: "Confirm Rivet",
          instruction:
            "Confirm the Rivet graph canvas replaces the empty file viewer.",
        },
      ],
      steps: [],
    };
    this.flush();
  }

  watch(page: Page) {
    page.on("console", (message) => {
      if (message.type() === "error" || message.type() === "warning") {
        this.diagnostics.push(`console ${message.type()}: ${message.text()}`);
      }
    });
    page.on("pageerror", (error) => {
      this.diagnostics.push(`page error: ${error.message}`);
    });
    page.on("response", (response) => {
      if (response.status() >= 400) {
        this.diagnostics.push(
          `failed response: ${response.status()} ${response.url()}`,
        );
      }
    });
  }

  record(step: EvidenceStep, url: string) {
    this.status.steps.push(step);
    this.status.updated = new Date().toISOString();
    if (step.state === "blocked") {
      this.status.overall = "blocked";
      this.status.summary = step.summary;
    } else if (this.status.steps.every((item) => item.state === "pass")) {
      this.status.overall = "pass";
      this.status.summary =
        "The saved Rivet workflow opened in the graph canvas from Workspace Files.";
    }
    const diagnostics = this.diagnostics.length
      ? this.diagnostics.map((item) => `  - ${item}`).join("\n")
      : "  - No console errors, page errors, or failed responses recorded.";
    const images = step.raw
      ? `  - Raw: \`${step.raw}\`\n  - Annotated: \`${step.annotated}\``
      : "  - None.";
    writeFileSync(
      path.join(this.root, "progress.md"),
      [
        `## ${new Date().toLocaleString("en-US", { timeZoneName: "short" })} - ${step.state.toUpperCase()}`,
        "",
        `- Current URL: \`${url}\``,
        `- Action: ${step.action}`,
        `- Exact control: ${step.controls.join(", ")}`,
        "- Value: No value entered.",
        `- Expected: ${step.expected}`,
        `- Actual: ${step.actual}`,
        "- Diagnostics:",
        diagnostics,
        "- Screenshots:",
        images,
        `- Status: **${step.state.toUpperCase()}**`,
        "",
      ].join("\n"),
      { encoding: "utf8", flag: "a" },
    );
    this.flush();
  }

  async capture(
    page: Page,
    id: string,
    controls: Array<{ selector: string; label: string }>,
  ) {
    const raw = `screenshots/raw/${id}.png`;
    const annotated = `screenshots/annotated/${id}.png`;
    await page.screenshot({ path: path.join(this.root, raw), fullPage: true });
    await page.evaluate((items) => {
      const markerClass = "wright-rivet-file-walkthrough-marker";
      const legend = document.createElement("div");
      legend.className = markerClass;
      legend.style.cssText =
        "position:fixed;right:16px;top:16px;z-index:2147483647;max-width:340px;padding:14px;background:#111827;color:white;border:3px solid #fbbf24;border-radius:10px;font:14px/1.4 system-ui;box-shadow:0 8px 30px #0008";
      legend.innerHTML = `<strong>Controls</strong><ol style="margin:8px 0 0;padding-left:22px">${items
        .map((item) => `<li>${item.label}</li>`)
        .join("")}</ol>`;
      document.body.appendChild(legend);
      items.forEach((item, index) => {
        const element = document.querySelector<HTMLElement>(item.selector);
        if (!element) return;
        element.style.outline = "4px solid #f59e0b";
        element.style.outlineOffset = "3px";
        const rect = element.getBoundingClientRect();
        const marker = document.createElement("div");
        marker.className = markerClass;
        marker.textContent = String(index + 1);
        marker.style.cssText = `position:fixed;left:${Math.max(0, rect.left - 13)}px;top:${Math.max(0, rect.top - 13)}px;z-index:2147483647;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;background:#f59e0b;color:#111827;font:bold 15px system-ui;border:2px solid white`;
        document.body.appendChild(marker);
      });
    }, controls);
    await page.screenshot({
      path: path.join(this.root, annotated),
      fullPage: true,
    });
    await page.evaluate(() => {
      document
        .querySelectorAll(".wright-rivet-file-walkthrough-marker")
        .forEach((element) => element.remove());
      document
        .querySelectorAll<HTMLElement>("[style*='outline']")
        .forEach((element) => {
          element.style.outline = "";
          element.style.outlineOffset = "";
        });
    });
    return { raw, annotated };
  }

  private flush() {
    writeFileSync(
      path.join(this.root, "status.json"),
      `${JSON.stringify(this.status, null, 2)}\n`,
      "utf8",
    );
    const cards = this.status.steps
      .map(
        (step) => `<article class="card ${step.state}">
          <strong>${step.state.toUpperCase()}</strong><h2>${escapeHtml(step.label)}</h2>
          <p>${escapeHtml(step.summary)}</p>
          <p><b>Expected:</b> ${escapeHtml(step.expected)}</p>
          <p><b>Actual:</b> ${escapeHtml(step.actual)}</p>
          ${
            step.raw
              ? `<button class="image-button" data-image="${escapeHtml(step.raw)}">Open raw image</button><button class="image-button" data-image="${escapeHtml(step.annotated || "")}">Open annotated image</button>`
              : ""
          }</article>`,
      )
      .join("\n");
    const manual = this.status.manualSteps
      .map((step) => `<li>${escapeHtml(step.instruction)}</li>`)
      .join("");
    writeFileSync(
      path.join(this.root, "report.html"),
      `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(this.status.title)}</title><style>body{margin:0;background:#f5f7fb;color:#172033;font:16px/1.5 system-ui}main{max-width:1000px;margin:auto;padding:28px}.card,.hero{background:white;border:1px solid #d0d5dd;border-radius:14px;padding:20px;margin:16px 0}.pass{border-left:8px solid #079455}.blocked{border-left:8px solid #d92d20}.pending{border-left:8px solid #98a2b3}button{margin:4px;padding:9px 12px}dialog{max-width:95vw;border:0;border-radius:12px}dialog img{max-width:90vw;max-height:80vh}dialog::backdrop{background:#000b}.close{float:right}</style></head><body><main><section class="hero"><h1>${escapeHtml(this.status.title)}</h1><p><b>${this.status.overall.toUpperCase()}:</b> ${escapeHtml(this.status.summary)}</p></section>${cards}<section class="card"><h2>Manual repeat checklist</h2><ol>${manual}</ol></section></main><dialog id="viewer"><button class="close">Close</button><img alt="Full-size walkthrough evidence"></dialog><script>const d=document.getElementById('viewer'),i=d.querySelector('img');document.querySelectorAll('[data-image]').forEach(b=>b.addEventListener('click',()=>{i.src=b.dataset.image;d.showModal()}));d.querySelector('.close').addEventListener('click',()=>d.close());document.addEventListener('keydown',e=>{if(e.key==='Escape')d.close()});</script></body></html>`,
      "utf8",
    );
  }
}

test.describe("@installed-rivet-file walkthrough", () => {
  test.skip(!artifactRoot, "WRIGHT_RIVET_FILE_WALKTHROUGH_ROOT is required");

  test("opens a saved Rivet project from Workspace Files", async ({
    page,
    context,
  }) => {
    test.setTimeout(150_000);
    const evidence = new WalkthroughEvidence(artifactRoot!);
    evidence.watch(page);
    await startTrace(context);
    try {
      await page.goto("/");
      await page.waitForLoadState("domcontentloaded");
      await page.goto(workspaceUrl);
      await expect(page.getByTestId("page-workspace")).toBeVisible({
        timeout: 30_000,
      });
      const root = page.getByTestId("file-node-/");
      await expect(root).toBeAttached({ timeout: 30_000 });
      if (!(await root.isVisible().catch(() => false))) {
        await page.getByTestId("activity-bar-explorer-btn").click();
      }
      const file = page.getByTestId(`file-node-${workflowFilePath}`);
      if (!(await file.isVisible().catch(() => false))) {
        await expect(root).toBeVisible({ timeout: 30_000 });
        await root.click();
        const workflows = page.getByTestId("file-node-/workflows");
        await expect(workflows).toBeVisible({ timeout: 30_000 });
        await workflows.click();
        const rivet = page.getByTestId("file-node-/workflows/rivet");
        await expect(rivet).toBeVisible({ timeout: 30_000 });
        await rivet.click();
      }
      await expect(file).toBeVisible({ timeout: 30_000 });
      const before = await evidence.capture(page, "01-workflow-file", [
        {
          selector: `[data-testid="file-node-${workflowFilePath}"]`,
          label: "workflow.rivet-project",
        },
        {
          selector: '[data-testid="workspace-surface-pane"]',
          label: "Workspace viewer",
        },
      ]);
      evidence.record(
        {
          id: "workflow-file-visible",
          state: "pass",
          label: "Locate the saved Rivet workflow",
          summary: "The saved workflow was visible in Workspace Files.",
          purpose: "Open the exact saved workflow reported by the user.",
          action: "Opened Workspace Files and expanded workflows/rivet.",
          controls: ["Workspace Files", "workflows", "rivet"],
          expected: "workflow.rivet-project is visible and selectable.",
          actual: "workflow.rivet-project was visible.",
          ...before,
        },
        page.url(),
      );

      await file.dblclick();
      try {
        await expect(page.getByTestId("direct-rivet-surface")).toBeVisible({
          timeout: 30_000,
        });
        await expect(page.getByTitle("Rivet graph canvas")).toBeVisible({
          timeout: 30_000,
        });
        const result = await evidence.capture(page, "02-rivet-opened", [
          {
            selector: '[data-testid="direct-rivet-toolbar"]',
            label: "Rivet editor toolbar",
          },
          {
            selector: 'iframe[title="Rivet graph canvas"]',
            label: "Rivet graph canvas",
          },
        ]);
        evidence.record(
          {
            id: "workflow-file-opened",
            state: "pass",
            label: "Open the saved Rivet workflow",
            summary: "The saved workflow opened in the Rivet graph canvas.",
            purpose:
              "Confirm explorer file-open routing reaches the managed Rivet application.",
            action: "Double-clicked workflow.rivet-project.",
            controls: ["workflow.rivet-project", "Rivet graph canvas"],
            expected:
              "The Rivet editor and graph canvas replace the empty viewer.",
            actual: "The managed Rivet editor and graph canvas were visible.",
            ...result,
          },
          page.url(),
        );
      } catch (error) {
        const result = await evidence.capture(page, "02-blank-viewer", [
          {
            selector: `[data-testid="editor-tab-${workflowFilePath}"]`,
            label: "workflow.rivet-project tab",
          },
          {
            selector: '[data-testid="viewer-container"]',
            label: "Blank file viewer",
          },
        ]);
        evidence.record(
          {
            id: "workflow-file-opened",
            state: "blocked",
            label: "Open the saved Rivet workflow",
            summary:
              "The workflow tab opened, but the viewer stayed blank instead of starting Rivet.",
            purpose:
              "Confirm explorer file-open routing reaches the managed Rivet application.",
            action: "Double-clicked workflow.rivet-project.",
            controls: ["workflow.rivet-project tab", "Blank file viewer"],
            expected:
              "The Rivet editor and graph canvas replace the empty viewer.",
            actual: `The managed Rivet surface did not appear: ${String(error)}`,
            ...result,
          },
          page.url(),
        );
      }
    } finally {
      await stopTrace(context, artifactRoot!);
    }
  });
});

async function startTrace(context: BrowserContext) {
  await context.tracing.start({
    screenshots: true,
    snapshots: true,
    sources: true,
  });
}

async function stopTrace(context: BrowserContext, root: string) {
  await context.tracing.stop({ path: path.join(root, "trace", "trace.zip") });
}

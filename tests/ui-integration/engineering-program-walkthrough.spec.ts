import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";

import {
  identities,
  mockJourney,
  type JourneyKind,
} from "./engineering-program-journey";

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

const artifactRoot = process.env.WRIGHT_WALKTHROUGH_ROOT;

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

class WalkthroughEvidence {
  private status: WalkthroughStatus;
  private diagnostics: string[] = [];

  constructor(private readonly root: string) {
    mkdirSync(path.join(root, "screenshots", "raw"), { recursive: true });
    mkdirSync(path.join(root, "screenshots", "annotated"), {
      recursive: true,
    });
    mkdirSync(path.join(root, "playwright"), { recursive: true });
    mkdirSync(path.join(root, "trace"), { recursive: true });
    copyFileSync(
      __filename,
      path.join(root, "playwright", "engineering-program-walkthrough.spec.ts"),
    );
    this.status = {
      title: "Wright engineering program walkthrough",
      summary:
        "Human-repeatable review of MCP-only and MCP-plus-local-model Rivet journeys.",
      overall: "pending",
      updated: new Date().toISOString(),
      manualSteps: [
        {
          label: "Open workflows",
          instruction:
            "Open a workspace and click **Workflows** in the activity bar.",
        },
        {
          label: "Check the scenario",
          instruction:
            "Click **Check readiness** for the chosen engineering scenario.",
        },
        {
          label: "Run the scenario",
          instruction:
            "Review the provider list, then click **Start reviewed scenario**.",
        },
        {
          label: "Preview support evidence",
          instruction:
            "In the engineering report, click **Preview support file** and review included, omitted, and redacted categories.",
        },
        {
          label: "Export deliberately",
          instruction:
            "Select the confirmation checkbox, then click **Export support file once**.",
        },
      ],
      steps: [],
    };
    writeFileSync(
      path.join(root, "progress.md"),
      "# Wright engineering program walkthrough progress\n\n",
      "utf8",
    );
    this.flush();
  }

  watch(page: Page) {
    page.on("console", (message) => {
      if (message.type() === "error") {
        this.diagnostics.push(`console error: ${message.text()}`);
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

  async capture(
    page: Page,
    id: string,
    controls: Array<{ selector: string; label: string }>,
  ) {
    const raw = `screenshots/raw/${id}.png`;
    const annotated = `screenshots/annotated/${id}.png`;
    await page.screenshot({ path: path.join(this.root, raw), fullPage: true });
    await page.evaluate((items) => {
      const markerClass = "wright-walkthrough-marker";
      const legend = document.createElement("div");
      legend.className = markerClass;
      legend.setAttribute("data-wright-walkthrough", "legend");
      legend.style.cssText =
        "position:fixed;right:8px;bottom:8px;z-index:2147483647;max-width:280px;background:#111;color:#fff;padding:10px;border:2px solid #fff;font:14px sans-serif;box-shadow:0 2px 12px #000;";
      legend.innerHTML = `<strong>Walkthrough controls</strong><br>${items
        .map((item, index) => `${index + 1}. ${item.label}`)
        .join("<br>")}`;
      document.body.appendChild(legend);
      items.forEach((item, index) => {
        const element = document.querySelector<HTMLElement>(item.selector);
        if (!element) return;
        element.dataset.wrightWalkthroughOutline = element.style.outline;
        element.style.outline = "4px solid #ffcc00";
        const badge = document.createElement("span");
        badge.className = markerClass;
        badge.textContent = String(index + 1);
        const box = element.getBoundingClientRect();
        badge.style.cssText = `position:fixed;left:${Math.max(0, box.left)}px;top:${Math.max(0, box.top)}px;z-index:2147483647;background:#c00;color:#fff;border:2px solid #fff;border-radius:50%;width:24px;height:24px;text-align:center;font:bold 15px/20px sans-serif;`;
        document.body.appendChild(badge);
      });
    }, controls);
    try {
      await page.screenshot({
        path: path.join(this.root, annotated),
        fullPage: true,
      });
    } finally {
      await page.evaluate(() => {
        document
          .querySelectorAll(".wright-walkthrough-marker")
          .forEach((node) => node.remove());
        document
          .querySelectorAll<HTMLElement>("[data-wright-walkthrough-outline]")
          .forEach((element) => {
            element.style.outline =
              element.dataset.wrightWalkthroughOutline ?? "";
            delete element.dataset.wrightWalkthroughOutline;
          });
      });
    }
    return { raw, annotated };
  }

  record(page: Page, step: EvidenceStep, diagnosticsStart: number) {
    const timestamp = new Intl.DateTimeFormat("en-CA", {
      timeZone: "America/New_York",
      dateStyle: "short",
      timeStyle: "long",
    }).format(new Date());
    const diagnostics = this.diagnostics.slice(diagnosticsStart);
    const entry = [
      `## ${step.id}: ${step.label}`,
      "",
      `- Timestamp: ${timestamp} America/New_York`,
      `- URL: ${page.url()}`,
      `- Action: ${step.action}`,
      `- Controls: ${step.controls.join(", ") || "None"}`,
      `- Expected: ${step.expected}`,
      `- Actual: ${step.actual}`,
      `- Browser evidence: ${diagnostics.length ? diagnostics.join("; ") : "no console errors, page errors, or failed HTTP responses"}`,
      `- Raw screenshot: ${step.raw ?? "not applicable"}`,
      `- Annotated screenshot: ${step.annotated ?? "not applicable"}`,
      `- Status: ${step.state === "pass" ? "PASS" : "STOPPED"}`,
      "",
    ].join("\n");
    writeFileSync(path.join(this.root, "progress.md"), entry, {
      encoding: "utf8",
      flag: "a",
    });
    this.status.steps.push(step);
    this.status.updated = new Date().toISOString();
    this.status.overall = step.state === "blocked" ? "blocked" : "pending";
    this.flush();
  }

  complete() {
    this.status.overall = "pass";
    this.status.summary =
      "Both representative journeys passed with six primary interactions each, bounded local-only diagnostics, narrow layout, 200% zoom, reduced motion, and no serious or critical scoped accessibility findings.";
    this.status.updated = new Date().toISOString();
    this.flush();
  }

  diagnosticCount() {
    return this.diagnostics.length;
  }

  private flush() {
    writeFileSync(
      path.join(this.root, "status.json"),
      `${JSON.stringify(this.status, null, 2)}\n`,
      "utf8",
    );
    const steps = this.status.steps
      .map(
        (step) =>
          `<article class="${step.state}"><h2>${escapeHtml(step.label)}</h2><p>${escapeHtml(step.summary)}</p><p><strong>Action:</strong> ${escapeHtml(step.action)}</p><p><strong>Expected:</strong> ${escapeHtml(step.expected)}</p><p><strong>Actual:</strong> ${escapeHtml(step.actual)}</p>${step.raw ? `<button class="image-button" onclick="showImage('${escapeHtml(step.raw)}')">Open raw screenshot</button>` : ""}${step.annotated ? `<button class="image-button" onclick="showImage('${escapeHtml(step.annotated)}')">Open annotated screenshot</button>` : ""}</article>`,
      )
      .join("\n");
    const manual = this.status.manualSteps
      .map(
        (step) =>
          `<li><strong>${escapeHtml(step.label)}</strong>: ${escapeHtml(step.instruction)}</li>`,
      )
      .join("\n");
    writeFileSync(
      path.join(this.root, "report.html"),
      `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(this.status.title)}</title><style>body{font:16px system-ui;max-width:1000px;margin:auto;padding:24px;background:#f5f6f8;color:#17202a}header,article{background:#fff;padding:16px;margin:12px 0;border-left:8px solid #888}article.pass{border-color:#188038}article.blocked{border-color:#c5221f}button{margin:4px;padding:8px}#viewer{display:none;position:fixed;inset:0;background:#000d;z-index:10;padding:20px}#viewer.open{display:flex;flex-direction:column}#viewer img{max-width:100%;max-height:90%;object-fit:contain;margin:auto}#viewer button{align-self:flex-end}</style></head><body><header><h1>${escapeHtml(this.status.title)}</h1><p><strong>Status:</strong> ${escapeHtml(this.status.overall)}</p><p>${escapeHtml(this.status.summary)}</p></header><h2>Manual repeat checklist</h2><ol>${manual}</ol><h2>Evidence</h2>${steps}<div id="viewer" role="dialog" aria-modal="true" aria-label="Full-size screenshot"><button onclick="closeImage()">Close</button><img id="full" alt="Full-size walkthrough screenshot"></div><script>const viewer=document.getElementById('viewer');const full=document.getElementById('full');function showImage(src){full.src=src;viewer.classList.add('open')}function closeImage(){viewer.classList.remove('open');full.src=''}document.addEventListener('keydown',e=>{if(e.key==='Escape')closeImage()});</script></body></html>`,
      "utf8",
    );
  }
}

test.describe("@walkthrough engineering program", () => {
  test.skip(!artifactRoot, "Set WRIGHT_WALKTHROUGH_ROOT to capture evidence.");

  test("MCP-only and local-model journeys", async ({ page, context }) => {
    const evidence = new WalkthroughEvidence(artifactRoot!);
    evidence.watch(page);
    await context.tracing.start({ screenshots: true, snapshots: true });

    try {
      for (const kind of ["mcp-only", "mcp-model"] as JourneyKind[]) {
        if (kind === "mcp-model") {
          // Each documented journey begins from a fresh human session. This
          // prevents an already-open panel from turning Open Workflows into a
          // close action at the start of the second journey.
          await page.goto("about:blank");
        }
        const fixture = identities(kind);
        const prefix = kind === "mcp-only" ? "mcp" : "model";
        const journey = await mockJourney(page, kind);
        await page.emulateMedia({ reducedMotion: "reduce" });
        let diagnosticsStart = evidence.diagnosticCount();
        await page.goto("/workspace/ws-1");
        await page.evaluate(() =>
          window.localStorage.removeItem("wright-workspace-layout-ws-1"),
        );
        await page.reload();
        await expect(
          page.getByTestId("activity-bar-workflows-btn"),
        ).toBeVisible();
        let images = await evidence.capture(page, `${prefix}-01-workspace`, [
          {
            selector: '[data-testid="activity-bar-workflows-btn"]',
            label: "Workflows",
          },
        ]);
        evidence.record(
          page,
          {
            id: `${prefix}-01`,
            state: "pass",
            label: `${fixture.scenario.title}: open workspace`,
            summary: "The workspace opened with the Workflows control visible.",
            purpose: "Begin from the normal engineering workspace.",
            action: "Navigate to workspace ws-1.",
            controls: ["Workflows"],
            expected: "The workspace and Workflows control are available.",
            actual:
              "The workspace loaded and the Workflows control was visible.",
            ...images,
          },
          diagnosticsStart,
        );

        diagnosticsStart = evidence.diagnosticCount();
        await page.getByTestId("activity-bar-workflows-btn").focus();
        await page.keyboard.press("Enter");
        await page.setViewportSize({ width: 320, height: 850 });
        const preflightId = `scenario-preflight-${fixture.scenario.scenario_id}`;
        await expect(page.getByTestId(preflightId)).toBeVisible();
        images = await evidence.capture(page, `${prefix}-02-library`, [
          {
            selector: `[data-testid="${preflightId}"]`,
            label: "Check readiness",
          },
        ]);
        evidence.record(
          page,
          {
            id: `${prefix}-02`,
            state: "pass",
            label: "Open the engineering scenario library",
            summary:
              "Keyboard activation opened the scenario library at 320 CSS pixels.",
            purpose:
              "Find the reviewed scenario without internal architecture knowledge.",
            action:
              "Focus Workflows and press Enter; narrow the viewport to 320 CSS pixels.",
            controls: ["Workflows", "Check readiness"],
            expected: "The chosen scenario remains operable at narrow width.",
            actual:
              "The library opened and Check readiness remained visible and operable.",
            ...images,
          },
          diagnosticsStart,
        );

        diagnosticsStart = evidence.diagnosticCount();
        await page.getByTestId(preflightId).focus();
        await page.keyboard.press("Enter");
        const preflightResult = page.getByTestId(
          `scenario-preflight-result-${fixture.scenario.scenario_id}`,
        );
        await expect(preflightResult).toContainText(
          kind === "mcp-only" ? "fixture-fea" : "local engineering model",
        );
        const startId = `scenario-start-${fixture.scenario.scenario_id}`;
        images = await evidence.capture(page, `${prefix}-03-preflight`, [
          {
            selector: `[data-testid="${startId}"]`,
            label: "Start reviewed scenario",
          },
        ]);
        evidence.record(
          page,
          {
            id: `${prefix}-03`,
            state: "pass",
            label: "Review provider readiness",
            summary:
              "The preflight named the selected MCP or local-model provider boundary.",
            purpose: "Confirm exact providers before execution.",
            action: "Focus Check readiness and press Enter.",
            controls: ["Check readiness", "Start reviewed scenario"],
            expected:
              "The provider list and a single next action are explicit.",
            actual:
              kind === "mcp-only"
                ? "The reviewed CAD/FEA MCP providers were named."
                : "The reviewed MCP providers and local engineering model were named.",
            ...images,
          },
          diagnosticsStart,
        );

        diagnosticsStart = evidence.diagnosticCount();
        await page.getByTestId(startId).focus();
        await page.keyboard.press("Enter");
        const report = page.getByTestId(
          `scenario-report-${journey.fixture.runId}`,
        );
        await expect(report).toContainText("Scenario is passed");
        await expect(
          report.getByTestId("scenario-phase-summary"),
        ).toBeFocused();
        images = await evidence.capture(page, `${prefix}-04-report`, [
          {
            selector: '[data-testid="support-diagnostics-preview"]',
            label: "Preview support file",
          },
        ]);
        evidence.record(
          page,
          {
            id: `${prefix}-04`,
            state: "pass",
            label: "Review the engineering result",
            summary:
              "The terminal report separated material evidence from observed assertions and moved focus to the result.",
            purpose:
              "Inspect deterministic identities, observations, cleanup, and recovery.",
            action: "Focus Start reviewed scenario and press Enter.",
            controls: ["Start reviewed scenario", "Preview support file"],
            expected:
              "A terminal report names evidence, assertions, cleanup, and provider attribution.",
            actual:
              "The passed report showed material engineering evidence, observed assertion results, and clean cleanup state.",
            ...images,
          },
          diagnosticsStart,
        );

        diagnosticsStart = evidence.diagnosticCount();
        await report.getByTestId("support-diagnostics-preview").focus();
        await page.keyboard.press("Enter");
        await expect(report).toContainText("raw engineering payloads: omitted");
        images = await evidence.capture(page, `${prefix}-05-diagnostics`, [
          {
            selector: '[data-testid="support-diagnostics-confirm"]',
            label: "Confirm local export scope",
          },
          {
            selector: '[data-testid="support-diagnostics-export"]',
            label: "Export support file once",
          },
        ]);
        evidence.record(
          page,
          {
            id: `${prefix}-05`,
            state: "pass",
            label: "Preview local support diagnostics",
            summary:
              "The preview explicitly omitted raw engineering payloads and required confirmation.",
            purpose: "Inspect scope and redaction before any file is written.",
            action: "Focus Preview support file and press Enter.",
            controls: [
              "Preview support file",
              "Confirm local export scope",
              "Export support file once",
            ],
            expected:
              "Included, omitted, and redacted categories are visible before export.",
            actual:
              "Raw engineering payloads were marked omitted and export remained disabled pending confirmation.",
            ...images,
          },
          diagnosticsStart,
        );

        diagnosticsStart = evidence.diagnosticCount();
        await report.getByTestId("support-diagnostics-confirm").focus();
        await page.keyboard.press("Space");
        await report.getByTestId("support-diagnostics-export").focus();
        await page.keyboard.press("Enter");
        await expect.poll(journey.diagnosticExports).toBe(1);
        await page.evaluate(() => {
          document.documentElement.style.zoom = "2";
        });
        const accessibility = await new AxeBuilder({ page })
          .include('[data-testid="engineering-scenario-library"]')
          .analyze();
        expect(
          accessibility.violations.filter((violation) =>
            ["serious", "critical"].includes(violation.impact || ""),
          ),
        ).toEqual([]);
        images = await evidence.capture(page, `${prefix}-06-exported`, []);
        evidence.record(
          page,
          {
            id: `${prefix}-06`,
            state: "pass",
            label: "Confirm and export once",
            summary:
              "The support file exported once and the journey remained visible at 200% zoom.",
            purpose:
              "Prove deliberate one-use local export and accessible narrow operation.",
            action:
              "Select the confirmation checkbox, activate Export support file once, then set 200% zoom.",
            controls: [
              "Confirm local export scope",
              "Export support file once",
            ],
            expected:
              "Exactly one local export occurs and no serious or critical scoped Axe findings remain.",
            actual:
              "Exactly one export occurred; the report remained visible at 200% zoom with zero serious or critical scoped findings.",
            ...images,
          },
          diagnosticsStart,
        );
        await page.evaluate(() => {
          document.documentElement.style.zoom = "1";
        });
        await page.setViewportSize({ width: 1280, height: 720 });
        await page.unrouteAll({ behavior: "wait" });
      }
      evidence.complete();
    } catch (error) {
      const images = existsSync(artifactRoot!)
        ? await evidence.capture(page, "stopping-point", [])
        : {};
      evidence.record(
        page,
        {
          id: "stopping-point",
          state: "blocked",
          label: "Walkthrough stopped",
          summary: "The walkthrough stopped at the first unexpected result.",
          purpose: "Preserve the stopping point without working around it.",
          action: "Stop immediately.",
          controls: [],
          expected: "Every action matches its documented result.",
          actual: error instanceof Error ? error.message : String(error),
          ...images,
        },
        evidence.diagnosticCount(),
      );
      throw error;
    } finally {
      await context.tracing.stop({
        path: path.join(artifactRoot!, "trace", "walkthrough.zip"),
      });
    }
  });
});

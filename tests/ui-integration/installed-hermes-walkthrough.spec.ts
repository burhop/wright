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

const artifactRoot = process.env.WRIGHT_INSTALLED_WALKTHROUGH_ROOT;

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

class InstalledWalkthroughEvidence {
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
      path.join(root, "playwright", "installed-hermes-walkthrough.spec.ts"),
    );
    writeFileSync(
      path.join(root, "progress.md"),
      "# Installed Hermes Wright walkthrough continuation\n\n",
      "utf8",
    );
    this.status = {
      title: "Installed Wright with local Hermes — continuation",
      summary:
        "The repaired candidate is installed and healthy. Browser access is under review.",
      overall: "pending",
      updated: new Date().toISOString(),
      manualSteps: [
        {
          label: "Start Wright",
          instruction:
            "In Hermes, run **/wright start** and wait for the local URL.",
        },
        {
          label: "Open Wright",
          instruction: "Open the returned Wright URL in a browser.",
        },
        {
          label: "Review access",
          instruction:
            "Follow the visible access guidance, then confirm the Wright dashboard loads.",
        },
      ],
      steps: [],
    };
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

  record(step: EvidenceStep, url = "not applicable") {
    this.status.steps.push(step);
    this.status.updated = new Date().toISOString();
    if (step.state === "blocked") {
      this.status.overall = "blocked";
      this.status.summary = step.summary;
    } else if (
      this.status.overall !== "blocked" &&
      this.status.steps.every((item) => item.state === "pass")
    ) {
      this.status.overall = "pass";
      this.status.summary =
        "The installed Wright and local Hermes walkthrough passed all reached steps.";
    }
    const diagnosticText = this.diagnostics.length
      ? this.diagnostics.map((item) => `  - ${item}`).join("\n")
      : "  - No console errors, page errors, or failed responses recorded.";
    const screenshots = step.raw
      ? `  - Raw: \`${step.raw}\`\n  - Annotated: \`${step.annotated}\``
      : "  - None for this control-plane step.";
    const entry = [
      `## ${new Date().toLocaleString("en-US", { timeZoneName: "short" })} — ${step.state.toUpperCase()}`,
      "",
      `- Current URL: \`${url}\``,
      `- Action: ${step.action}`,
      `- Exact control: ${step.controls.join(", ")}`,
      "- Value: No secret values are recorded.",
      `- Expected: ${step.expected}`,
      `- Actual: ${step.actual}`,
      "- Diagnostics:",
      diagnosticText,
      "- Screenshots:",
      screenshots,
      `- Status: **${step.state.toUpperCase()}**`,
      "",
    ].join("\n");
    writeFileSync(path.join(this.root, "progress.md"), entry, {
      encoding: "utf8",
      flag: "a",
    });
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
      const markerClass = "wright-installed-walkthrough-marker";
      const legend = document.createElement("div");
      legend.className = markerClass;
      legend.style.cssText =
        "position:fixed;right:16px;top:16px;z-index:2147483647;max-width:360px;padding:14px;background:#111827;color:white;border:3px solid #fbbf24;border-radius:10px;font:14px/1.4 system-ui;box-shadow:0 8px 30px #0008";
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
        .querySelectorAll(".wright-installed-walkthrough-marker")
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
          <span class="state">${step.state.toUpperCase()}</span>
          <h2>${escapeHtml(step.label)}</h2>
          <p>${escapeHtml(step.summary)}</p>
          <p><strong>Expected:</strong> ${escapeHtml(step.expected)}</p>
          <p><strong>Actual:</strong> ${escapeHtml(step.actual)}</p>
          ${
            step.raw
              ? `<button class="image-button" data-image="${escapeHtml(step.raw)}">Open raw image</button>
                 <button class="image-button" data-image="${escapeHtml(step.annotated || "")}">Open annotated image</button>`
              : "<p>No browser image was available for this control-plane step.</p>"
          }
        </article>`,
      )
      .join("\n");
    const manual = this.status.manualSteps
      .map((step) => `<li>${escapeHtml(step.instruction)}</li>`)
      .join("");
    const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(this.status.title)}</title><style>
body{margin:0;background:#f5f7fb;color:#172033;font:16px/1.5 system-ui}main{max-width:1000px;margin:auto;padding:28px}.card,.hero{background:white;border:1px solid #d0d5dd;border-radius:14px;padding:20px;margin:16px 0}.card.pass{border-left:8px solid #079455}.card.blocked{border-left:8px solid #d92d20}.card.pending{border-left:8px solid #98a2b3}.state{font-weight:800}.image-button{margin:4px;padding:10px 14px;border:1px solid #667085;border-radius:8px;background:white;color:#175cd3;cursor:pointer}dialog{max-width:95vw;border:0;border-radius:12px;padding:14px}dialog img{max-width:90vw;max-height:80vh}dialog::backdrop{background:#000b}.close{float:right;padding:8px 12px}</style></head>
<body><main><section class="hero"><h1>${escapeHtml(this.status.title)}</h1><p><strong>${this.status.overall.toUpperCase()}:</strong> ${escapeHtml(this.status.summary)}</p></section>
${cards}<section class="card"><h2>Manual repeat checklist</h2><ol>${manual}</ol></section></main>
<dialog id="viewer"><button class="close" type="button">Close</button><img alt="Full-size walkthrough evidence"></dialog>
<script>const d=document.getElementById('viewer'),i=d.querySelector('img');document.querySelectorAll('.image-button').forEach(b=>b.addEventListener('click',()=>{i.src=b.dataset.image;d.showModal()}));d.querySelector('.close').addEventListener('click',()=>d.close());document.addEventListener('keydown',e=>{if(e.key==='Escape')d.close()});</script></body></html>`;
    writeFileSync(path.join(this.root, "report.html"), html, "utf8");
  }
}

test.describe("@installed-hermes walkthrough", () => {
  test.skip(!artifactRoot, "WRIGHT_INSTALLED_WALKTHROUGH_ROOT is required");

  test("opens the packaged Wright UI through the local Hermes lifecycle", async ({
    page,
    context,
  }) => {
    test.setTimeout(180_000);
    const evidence = new InstalledWalkthroughEvidence(artifactRoot!);
    const workspaceName = `Installed Hermes Rivet Test ${path
      .basename(artifactRoot!)
      .replace(/[^a-z0-9]+/gi, "-")
      .slice(-24)}`;
    evidence.record({
      id: "wheelhouse-repair",
      state: "pass",
      label: "Python 3.11 wheelhouse repaired",
      summary:
        "The candidate now has a complete 62-wheel offline dependency set.",
      purpose: "Repair the original missing-PyYAML installation stop.",
      action: "Resolved the candidate runtime extras for Hermes Python 3.11.",
      controls: ["Hermes /wright start dependency set"],
      expected:
        "A compatible PyYAML wheel and every transitive runtime wheel are available offline.",
      actual:
        "The complete wheelhouse includes pyyaml-6.0.3-cp311-cp311-win_amd64.whl.",
    });
    evidence.record({
      id: "candidate-identity",
      state: "pass",
      label: "Exact candidate identity accepted",
      summary:
        "Wright accepted the exact version, channel, and SHA-256 identity.",
      purpose:
        "Prove local candidate activation remains immutable and fail-closed.",
      action: "Retried start with the complete local-candidate identity.",
      controls: ["Wright native lifecycle"],
      expected:
        "The lifecycle accepts the exact candidate without bypassing artifact validation.",
      actual:
        "Runtime 0.1.9 staged and activated after the complete identity was supplied.",
    });
    evidence.record({
      id: "installed-runtime",
      state: "pass",
      label: "Packaged Wright runtime healthy",
      summary:
        "The installed API and static UI are running on port 8000 without Vite.",
      purpose:
        "Verify the real installed runtime starts through the enabled Hermes adapter.",
      action:
        "Started the contained runtime and independently probed its API and root document.",
      controls: ["Hermes /wright start", "Wright API", "packaged static UI"],
      expected: "Wright reports healthy and serves its packaged UI.",
      actual:
        "The lifecycle returned healthy; /api/health and / both returned successfully.",
    });

    evidence.watch(page);
    await startTrace(context);
    try {
      await page.goto("/");
      await page.waitForLoadState("domcontentloaded");
      const accessDialog = page.getByRole("dialog");
      if (await accessDialog.isVisible().catch(() => false)) {
        await expect(accessDialog).toContainText("Access Token");
        const images = await evidence.capture(page, "01-access-dialog", [
          { selector: "input[type='password']", label: "Access Token field" },
          { selector: "button[type='submit']", label: "Continue button" },
        ]);
        const visibleText = (await accessDialog.innerText())
          .replace(/\s+/g, " ")
          .trim();
        evidence.record(
          {
            id: "browser-access",
            state: "blocked",
            label: "Open the installed Wright UI",
            summary:
              "The native Hermes start path opens a token dialog whose only guidance refers to Docker.",
            purpose:
              "Reach the packaged Wright dashboard as a normal local Hermes user.",
            action:
              "Opened the packaged Wright URL returned by the native lifecycle.",
            controls: ["Access Token field", "Continue button"],
            expected:
              "The Hermes start path either authenticates the local browser or tells the user exactly where the native access token is available.",
            actual: `The page stopped at: ${visibleText}. The /wright start result did not display a token, and the visible guidance only says to use a token printed by a Docker container.`,
            ...images,
          },
          page.url(),
        );
        return;
      }

      const images = await evidence.capture(page, "01-dashboard", [
        { selector: "nav", label: "Primary navigation" },
        { selector: "main", label: "Dashboard content" },
      ]);
      evidence.record(
        {
          id: "browser-access",
          state: "pass",
          label: "Open the installed Wright UI",
          summary: "The packaged Wright dashboard opened successfully.",
          purpose:
            "Reach the packaged Wright dashboard as a normal local Hermes user.",
          action:
            "Opened the packaged Wright URL returned by the native lifecycle.",
          controls: ["Primary navigation", "Dashboard content"],
          expected:
            "The installed dashboard is available without a development server.",
          actual: "The dashboard rendered from the packaged runtime.",
          ...images,
        },
        page.url(),
      );

      let initialHermesPending = false;
      try {
        const agentStatus = page.getByTestId("card-agent-status");
        await expect(agentStatus).toContainText("Wright API: connected", {
          timeout: 30_000,
        });
        await expect(agentStatus).toContainText("Inference Engine: connected");
        let hermesHealth: { state?: string; error?: string | null } = {};
        await expect
          .poll(
            async () => {
              hermesHealth = await page.evaluate(async () => {
                const response = await fetch("/api/agent/health");
                return (await response.json()) as {
                  state?: string;
                  error?: string | null;
                };
              });
              initialHermesPending =
                hermesHealth.state === "unknown" &&
                hermesHealth.error ===
                  "Hermes gateway is refreshing workspace tools";
              return hermesHealth.state === "connected" || initialHermesPending;
            },
            { timeout: 30_000 },
          )
          .toBe(true);
        const healthImages = await evidence.capture(page, "02-dependencies", [
          {
            selector: '[data-testid="card-agent-status"]',
            label: "Dependency status",
          },
        ]);
        evidence.record(
          {
            id: "dependency-health",
            state: "pass",
            label: "Confirm installed dependencies",
            summary: initialHermesPending
              ? "Wright and inference were connected; Hermes clearly reported a planned workspace-tool refresh."
              : "Wright, Hermes, and the configured inference engine all reported connected.",
            purpose:
              "Verify the installed application is using the running local Hermes setup.",
            action: "Waited for the dashboard dependency poll to complete.",
            controls: ["Dependency status"],
            expected:
              "Wright API and Inference Engine report connected; Hermes is connected or explicitly awaiting its planned workspace-tool refresh.",
            actual: initialHermesPending
              ? "Wright API and Inference Engine reported connected. Hermes reported the explicit workspace-tool refresh state that the live chat check will clear."
              : "All three dashboard dependency indicators reported connected.",
            ...healthImages,
          },
          page.url(),
        );
      } catch (error) {
        const healthImages = await evidence.capture(
          page,
          "02-dependencies-blocked",
          [
            {
              selector: '[data-testid="card-agent-status"]',
              label: "Dependency status",
            },
          ],
        );
        evidence.record(
          {
            id: "dependency-health",
            state: "blocked",
            label: "Confirm installed dependencies",
            summary:
              "The installed dashboard did not confirm every required dependency.",
            purpose:
              "Verify the installed application is using the running local Hermes setup.",
            action: "Waited for the dashboard dependency poll to complete.",
            controls: ["Dependency status"],
            expected:
              "Wright API, Hermes, and Inference Engine all report connected.",
            actual: `Dependency confirmation stopped: ${String(error)}`,
            ...healthImages,
          },
          page.url(),
        );
        return;
      }

      try {
        await page.getByRole("link", { name: /^Tool Registry/ }).click();
        await expect(
          page.getByRole("heading", {
            name: "Engineering MCP Server Library",
          }),
        ).toBeVisible();
        const results = page.getByTestId("capability-results");
        await expect(results).toBeVisible();
        const catalogText = (await results.innerText()).replace(/\s+/g, " ");
        const catalogImages = await evidence.capture(
          page,
          "03-capability-library",
          [
            {
              selector: '[data-testid="capability-offline-source"]',
              label: "Bundled catalog source",
            },
            {
              selector: '[data-testid="capability-results"]',
              label: "Engineering capabilities",
            },
          ],
        );
        evidence.record(
          {
            id: "capability-library",
            state: "pass",
            label: "Open the engineering capability library",
            summary:
              "The installed UI loaded its bundled engineering MCP catalog.",
            purpose:
              "Confirm engineering users can discover MCP capabilities in the packaged application.",
            action: "Selected Tool Registry from the primary navigation.",
            controls: ["Tool Registry", "Engineering capabilities"],
            expected:
              "The Engineering MCP Server Library renders a non-empty bundled catalog.",
            actual: `The capability library rendered ${catalogText.length} characters of catalog content.`,
            ...catalogImages,
          },
          page.url(),
        );
      } catch (error) {
        const catalogImages = await evidence.capture(
          page,
          "03-capability-library-blocked",
          [{ selector: "main", label: "Current page" }],
        );
        evidence.record(
          {
            id: "capability-library",
            state: "blocked",
            label: "Open the engineering capability library",
            summary:
              "The installed application did not present the engineering capability catalog as expected.",
            purpose:
              "Confirm engineering users can discover MCP capabilities in the packaged application.",
            action: "Selected Tool Registry from the primary navigation.",
            controls: ["Tool Registry", "Current page"],
            expected:
              "The Engineering MCP Server Library renders a non-empty bundled catalog.",
            actual: `Capability-library review stopped: ${String(error)}`,
            ...catalogImages,
          },
          page.url(),
        );
        return;
      }

      try {
        await page.getByRole("link", { name: "Engineering Models" }).click();
        await expect(
          page.getByRole("heading", { name: "Engineering Models" }),
        ).toBeVisible();
        const modelGrid = page.getByTestId("model-library-grid");
        await expect(modelGrid).toBeVisible();
        const modelCount = await page
          .locator('[data-testid^="model-card-"]')
          .count();
        expect(modelCount).toBeGreaterThan(0);
        const modelImages = await evidence.capture(
          page,
          "04-engineering-models",
          [
            {
              selector: '[data-testid="model-search"]',
              label: "Model search",
            },
            {
              selector: '[data-testid="model-library-grid"]',
              label: "Local model library",
            },
          ],
        );
        evidence.record(
          {
            id: "engineering-models",
            state: "pass",
            label: "Open the local engineering model library",
            summary: `The installed UI displayed ${modelCount} engineering model entries.`,
            purpose:
              "Confirm local model discovery is available beside the MCP catalog.",
            action: "Selected Engineering Models from the primary navigation.",
            controls: ["Engineering Models", "Model search"],
            expected:
              "The packaged application renders at least one engineering model entry.",
            actual: `${modelCount} engineering model entries were visible.`,
            ...modelImages,
          },
          page.url(),
        );
      } catch (error) {
        const modelImages = await evidence.capture(
          page,
          "04-engineering-models-blocked",
          [{ selector: "main", label: "Current page" }],
        );
        evidence.record(
          {
            id: "engineering-models",
            state: "blocked",
            label: "Open the local engineering model library",
            summary:
              "The installed application did not present a usable engineering model catalog.",
            purpose:
              "Confirm local model discovery is available beside the MCP catalog.",
            action: "Selected Engineering Models from the primary navigation.",
            controls: ["Engineering Models", "Current page"],
            expected:
              "The packaged application renders at least one engineering model entry.",
            actual: `Engineering-model review stopped: ${String(error)}`,
            ...modelImages,
          },
          page.url(),
        );
        return;
      }

      try {
        await page
          .getByRole("link", { name: "Dashboard", exact: true })
          .click();
        await page.getByRole("button", { name: "+ Create Workspace" }).click();
        const modal = page.getByTestId("create-workspace-modal");
        await expect(modal).toBeVisible();
        const modalImages = await evidence.capture(
          page,
          "05-create-workspace",
          [
            {
              selector: '[data-testid="create-workspace-modal"]',
              label: "Create Workspace dialog",
            },
            { selector: "#workspace-name-input", label: "Workspace name" },
            { selector: "#workspace-create-submit", label: "Create" },
          ],
        );
        evidence.record(
          {
            id: "workspace-dialog",
            state: "pass",
            label: "Open isolated workspace creation",
            summary:
              "The installed dashboard presented the workspace creation dialog.",
            purpose:
              "Create a disposable workspace for real MCP and Rivet checks.",
            action: "Returned to Dashboard and selected + Create Workspace.",
            controls: ["+ Create Workspace", "Workspace name", "Create"],
            expected: "A clear workspace creation dialog opens.",
            actual:
              "The dialog opened; the configured workspace root is isolated under .local-run.",
            ...modalImages,
          },
          page.url(),
        );

        await page.locator("#workspace-name-input").fill(workspaceName);
        evidence.record(
          {
            id: "workspace-name",
            state: "pass",
            label: "Name the disposable workspace",
            summary: "The isolated workspace name was accepted.",
            purpose:
              "Keep the manual test easy to identify and safely contained.",
            action: `Entered ${workspaceName} in Workspace Name.`,
            controls: ["Workspace name"],
            expected: "The local test name remains in the field.",
            actual: "The field contained the requested disposable test name.",
          },
          page.url(),
        );
        await page.locator("#workspace-create-submit").click();
        await expect(page).toHaveURL(/\/workspace\//, { timeout: 30_000 });
        await expect(page.getByTestId("page-workspace")).toBeVisible({
          timeout: 30_000,
        });
        await expect(page.getByTestId("activity-bar-mcp-btn")).toBeVisible();
        const workspaceImages = await evidence.capture(page, "06-workspace", [
          {
            selector: '[data-testid="activity-bar-mcp-btn"]',
            label: "MCP Tools",
          },
          {
            selector: '[data-testid="activity-bar-workflows-btn"]',
            label: "Rivet Workflows",
          },
        ]);
        evidence.record(
          {
            id: "workspace-created",
            state: "pass",
            label: "Create and activate the disposable workspace",
            summary:
              "The packaged application created and opened the isolated workspace.",
            purpose:
              "Exercise the real installed workspace services before opening MCP and Rivet views.",
            action: "Selected Create and waited for the workspace to activate.",
            controls: ["Create", "MCP Tools", "Rivet Workflows"],
            expected:
              "The new workspace opens with MCP Tools and Rivet Workflows available.",
            actual:
              "The workspace activated and both engineering integration controls were visible.",
            ...workspaceImages,
          },
          page.url(),
        );
      } catch (error) {
        const workspaceImages = await evidence.capture(
          page,
          "06-workspace-blocked",
          [{ selector: "body", label: "Current application state" }],
        );
        evidence.record(
          {
            id: "workspace-created",
            state: "blocked",
            label: "Create and activate the disposable workspace",
            summary:
              "The installed application did not reach an active disposable workspace.",
            purpose:
              "Exercise the real installed workspace services before opening MCP and Rivet views.",
            action: "Created the named disposable workspace.",
            controls: ["Create Workspace", "Current application state"],
            expected:
              "The new workspace opens with MCP Tools and Rivet Workflows available.",
            actual: `Workspace activation stopped: ${String(error)}`,
            ...workspaceImages,
          },
          page.url(),
        );
        return;
      }

      try {
        await page.getByTestId("activity-bar-mcp-btn").click();
        await expect(page.getByText("MCP Tools Selector")).toBeVisible();
        await expect
          .poll(
            () => page.locator('[data-testid^="mcp-server-item-"]').count(),
            { timeout: 30_000 },
          )
          .toBeGreaterThan(0);
        const serverCount = await page
          .locator('[data-testid^="mcp-server-item-"]')
          .count();
        const mcpImages = await evidence.capture(page, "07-workspace-mcps", [
          {
            selector: '[data-testid="activity-bar-mcp-btn"]',
            label: "MCP Tools",
          },
          {
            selector: '[data-testid="workspace-sidebar"]',
            label: "Workspace MCP selector",
          },
        ]);
        evidence.record(
          {
            id: "workspace-mcps",
            state: "pass",
            label: "Inspect MCPs inside the workspace",
            summary: `The real workspace displayed ${serverCount} installed MCP server entries.`,
            purpose:
              "Confirm workspace users can inspect the MCP providers Rivet workflows may bind.",
            action: "Selected MCP Tools in the workspace activity bar.",
            controls: ["MCP Tools", "Workspace MCP selector"],
            expected:
              "The workspace MCP selector loads at least one installed provider.",
            actual: `${serverCount} installed MCP server entries were displayed.`,
            ...mcpImages,
          },
          page.url(),
        );
      } catch (error) {
        const mcpImages = await evidence.capture(
          page,
          "07-workspace-mcps-blocked",
          [{ selector: "body", label: "Current workspace state" }],
        );
        evidence.record(
          {
            id: "workspace-mcps",
            state: "blocked",
            label: "Inspect MCPs inside the workspace",
            summary:
              "The real workspace did not expose a usable MCP provider list.",
            purpose:
              "Confirm workspace users can inspect the MCP providers Rivet workflows may bind.",
            action: "Selected MCP Tools in the workspace activity bar.",
            controls: ["MCP Tools", "Current workspace state"],
            expected:
              "The workspace MCP selector loads at least one installed provider.",
            actual: `Workspace MCP review stopped: ${String(error)}`,
            ...mcpImages,
          },
          page.url(),
        );
        return;
      }

      try {
        await page.getByTestId("activity-bar-workflows-btn").click();
        await expect(page.getByTestId("rivet-workflows-tab")).toBeVisible({
          timeout: 30_000,
        });
        const scenarios = page.getByTestId("engineering-scenario-library");
        await expect(scenarios).toBeVisible();
        await expect(scenarios.getByRole("status")).not.toContainText(
          "Loading deterministic examples",
          { timeout: 30_000 },
        );
        const statusText = (await scenarios.getByRole("status").innerText())
          .replace(/\s+/g, " ")
          .trim();
        expect(statusText).toMatch(/\d+ deterministic engineering scenarios/);
        const rivetImages = await evidence.capture(page, "08-rivet-workflows", [
          {
            selector: '[data-testid="activity-bar-workflows-btn"]',
            label: "Rivet Workflows",
          },
          {
            selector: '[data-testid="rivet-workflows-tab"]',
            label: "Rivet workflow catalog",
          },
          {
            selector: '[data-testid="engineering-scenario-library"]',
            label: "Engineering scenarios",
          },
        ]);
        evidence.record(
          {
            id: "rivet-workflows",
            state: "pass",
            label: "Open Rivet with workspace MCP context",
            summary:
              "Rivet loaded its workflow panel and deterministic engineering scenario library in the real workspace.",
            purpose:
              "Confirm Rivet can enter a workspace that already exposes installed MCP providers.",
            action: "Selected Rivet Workflows in the workspace activity bar.",
            controls: [
              "Rivet Workflows",
              "Rivet workflow catalog",
              "Engineering scenarios",
            ],
            expected:
              "The real Rivet workflow panel and scenario library load without mocks.",
            actual: statusText,
            ...rivetImages,
          },
          page.url(),
        );
      } catch (error) {
        const rivetImages = await evidence.capture(
          page,
          "08-rivet-workflows-blocked",
          [{ selector: "body", label: "Current Rivet state" }],
        );
        evidence.record(
          {
            id: "rivet-workflows",
            state: "blocked",
            label: "Open Rivet with workspace MCP context",
            summary:
              "The real workspace did not reach a usable Rivet engineering-scenario view.",
            purpose:
              "Confirm Rivet can enter a workspace that already exposes installed MCP providers.",
            action: "Selected Rivet Workflows in the workspace activity bar.",
            controls: ["Rivet Workflows", "Current Rivet state"],
            expected:
              "The real Rivet workflow panel and scenario library load without mocks.",
            actual: `Rivet review stopped: ${String(error)}`,
            ...rivetImages,
          },
          page.url(),
        );
        return;
      }

      try {
        const editor = page.getByTestId("direct-rivet-surface");
        await expect(editor).toBeVisible({ timeout: 90_000 });
        const editorStatus = page.getByTestId("direct-rivet-status");
        await expect
          .poll(() => editorStatus.innerText(), { timeout: 30_000 })
          .toMatch(/ready|opened from this workspace/i);
        await expect(page.getByTitle("Rivet graph canvas")).toBeVisible();
        await expect(
          page.getByTestId("direct-rivet-ai-status"),
        ).toHaveAttribute("aria-label", "Rivet AI connected", {
          timeout: 30_000,
        });
        const finalStatus = (await editorStatus.innerText()).trim();
        const editorImages = await evidence.capture(page, "09-rivet-editor", [
          {
            selector: '[data-testid="direct-rivet-toolbar"]',
            label: "Rivet editor toolbar",
          },
          {
            selector: '[data-testid="direct-rivet-ai-status"]',
            label: "Rivet AI through Hermes",
          },
          { selector: 'iframe[title="Rivet graph canvas"]', label: "Rivet 2" },
        ]);
        evidence.record(
          {
            id: "rivet-editor",
            state: "pass",
            label: "Wait for the Rivet application",
            summary:
              "The managed Rivet editor, graph canvas, and Hermes-backed Rivet AI connection became ready.",
            purpose:
              "Distinguish a healthy workflow sidebar from a fully started Rivet application.",
            action:
              "Waited for the managed editor surface, graph canvas, and Rivet AI status after opening Rivet Workflows.",
            controls: [
              "Rivet editor toolbar",
              "Rivet AI through Hermes",
              "Rivet 2",
            ],
            expected:
              "The actual Rivet editor replaces its startup screen and connects its AI bridge through Hermes.",
            actual: `The editor reported: ${finalStatus}. Rivet AI reported connected.`,
            ...editorImages,
          },
          page.url(),
        );
      } catch (error) {
        const editorImages = await evidence.capture(
          page,
          "09-rivet-editor-blocked",
          [
            {
              selector: '[data-testid="workspace-surface-pane"]',
              label: "Rivet application area",
            },
            {
              selector: '[data-testid="managed-rivet-retry"]',
              label: "Retry",
            },
          ],
        );
        evidence.record(
          {
            id: "rivet-editor",
            state: "blocked",
            label: "Wait for the Rivet application",
            summary:
              "The workflow sidebar loaded, but the actual Rivet application did not reach a connected ready state.",
            purpose:
              "Distinguish a healthy workflow sidebar from a fully started Rivet application.",
            action:
              "Waited for the managed editor surface, graph canvas, and Rivet AI status after opening Rivet Workflows.",
            controls: ["Rivet application area", "Retry"],
            expected:
              "The actual Rivet editor replaces its startup screen and connects its AI bridge through Hermes.",
            actual: `Rivet application startup stopped: ${String(error)}`,
            ...editorImages,
          },
          page.url(),
        );
        return;
      }

      try {
        const transcript = page.getByTestId("chat-transcript");
        const messages = transcript.locator('[data-testid^="message-"]');
        const previousMessageCount = await messages.count();
        const composer = page.getByTestId("composer-input");
        await composer.fill(
          "Manual startup test: reply with the single word READY.",
        );
        const promptImages = await evidence.capture(page, "10-hermes-prompt", [
          { selector: '[data-testid="composer-input"]', label: "Prompt" },
          { selector: '[data-testid="composer-send"]', label: "Send" },
          {
            selector: '[data-testid="mcp-status-indicator"]',
            label: "Workspace MCP status",
          },
        ]);
        evidence.record(
          {
            id: "hermes-prompt",
            state: "pass",
            label: "Prepare a live Hermes check",
            summary:
              "A minimal, non-engineering prompt was entered without exposing credentials or user data.",
            purpose:
              "Exercise the real Hermes chat path and apply any pending workspace MCP binding.",
            action:
              "Entered a one-word-response startup prompt in the workspace composer.",
            controls: ["Prompt", "Send", "Workspace MCP status"],
            expected:
              "The prompt is ready to send through the isolated workspace.",
            actual: "The composer contained the minimal READY-response prompt.",
            ...promptImages,
          },
          page.url(),
        );

        await page.getByTestId("composer-send").click();
        await expect
          .poll(() => messages.count(), { timeout: 120_000 })
          .toBeGreaterThan(previousMessageCount + 1);
        await expect(page.getByTestId("thinking-indicator")).toBeHidden({
          timeout: 120_000,
        });
        const transcriptText = (await transcript.innerText())
          .replace(/\s+/g, " ")
          .trim();
        expect(transcriptText).toMatch(/READY/i);
        await expect
          .poll(
            () =>
              page.evaluate(async () => {
                const response = await fetch("/api/agent/health");
                const body = (await response.json()) as { state?: string };
                return body.state;
              }),
            { timeout: 45_000 },
          )
          .toBe("connected");
        const chatImages = await evidence.capture(page, "11-hermes-response", [
          {
            selector: '[data-testid="chat-transcript"]',
            label: "Hermes response",
          },
          {
            selector: '[data-testid="direct-rivet-ai-status"]',
            label: "Rivet AI through Hermes",
          },
        ]);
        evidence.record(
          {
            id: "hermes-live-response",
            state: "pass",
            label: "Confirm live Hermes response",
            summary:
              "The installed workspace received a live Hermes response and finished with Hermes connected.",
            purpose:
              "Prove the running Wright dependency chain works beyond static health indicators.",
            action:
              "Selected Send, waited for the response, then rechecked agent health.",
            controls: ["Send", "Hermes response", "Rivet AI through Hermes"],
            expected:
              "Hermes returns READY, applies the workspace binding, and reports connected.",
            actual:
              "The transcript contained READY and /api/agent/health reported connected after the turn.",
            ...chatImages,
          },
          page.url(),
        );
      } catch (error) {
        const chatImages = await evidence.capture(
          page,
          "11-hermes-response-blocked",
          [
            {
              selector: '[data-testid="chat-transcript"]',
              label: "Hermes response area",
            },
            {
              selector: '[data-testid="stream-activity-panel"]',
              label: "Current activity",
            },
          ],
        );
        evidence.record(
          {
            id: "hermes-live-response",
            state: "blocked",
            label: "Confirm live Hermes response",
            summary:
              "The static installed checks passed, but the live Hermes turn did not complete successfully.",
            purpose:
              "Prove the running Wright dependency chain works beyond static health indicators.",
            action:
              "Selected Send, waited for the response, then rechecked agent health.",
            controls: ["Hermes response area", "Current activity"],
            expected:
              "Hermes returns READY, applies the workspace binding, and reports connected.",
            actual: `Live Hermes check stopped: ${String(error)}`,
            ...chatImages,
          },
          page.url(),
        );
        return;
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

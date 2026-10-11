import { chromium } from "@playwright/test";
import {
  mkdirSync,
  readFileSync,
  writeFileSync,
  appendFileSync,
} from "node:fs";
import path from "node:path";
const artifactRoot = path.resolve(process.argv[2]);
const privateContext = JSON.parse(readFileSync(process.argv[3], "utf8"));
const workspace = JSON.parse(readFileSync(process.argv[4], "utf8"))[0];
const runLabel =
  "instruction-input-transfer-" +
  new Date().toISOString().replace(/\D/g, "").slice(0, 14);
for (const dir of [
  "playwright",
  "screenshots/raw",
  "screenshots/annotated",
  "trace",
])
  mkdirSync(path.join(artifactRoot, dir), { recursive: true });
writeFileSync(
  path.join(artifactRoot, "playwright/capture.mjs"),
  readFileSync(import.meta.filename),
);
const status = {
  title: "Request input, scoped instructions and workflow transfer",
  summary:
    "Approved isolated UI proof in progress; no process execution or external action is submitted.",
  overall: "pending",
  updated: new Date().toISOString(),
  manualSteps: [],
  steps: [],
};
const diagnostics = [];
writeFileSync(
  path.join(artifactRoot, "progress.md"),
  "# Instruction authoring and workflow transfer\n\nStarted " +
    status.updated +
    " UTC. Isolated workspace. No existing run is resumed or approved.\n",
);
const esc = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll('"', "&quot;");
function report() {
  status.updated = new Date().toISOString();
  writeFileSync(
    path.join(artifactRoot, "status.json"),
    JSON.stringify(status, null, 2),
  );
  writeFileSync(
    path.join(artifactRoot, "report.html"),
    '<!doctype html><meta charset="utf-8"><title>Wright authoring and transfer</title><style>body{font:16px system-ui;max-width:1100px;margin:30px auto;background:#101624;color:#eee}article{padding:18px;border:1px solid #556;margin:12px 0}.pass{border-color:#5c9}.blocked{border-color:#e65}img{max-width:95%}a{color:#6de}</style><h1>' +
      esc(status.title) +
      "</h1><p>" +
      esc(status.summary) +
      "</p><h2>Manual repeat</h2><ol>" +
      status.manualSteps
        .map((s) => "<li>" + esc(s.instruction) + "</li>")
        .join("") +
      "</ol>" +
      status.steps
        .map(
          (s) =>
            '<article class="' +
            s.state +
            '"><h2>' +
            esc(s.label + " — " + s.state) +
            "</h2><p>Purpose: " +
            esc(s.purpose) +
            "</p><p>Action: " +
            esc(s.action) +
            "</p><p>Expected: " +
            esc(s.expected) +
            "</p><p>Observed: " +
            esc(s.actual) +
            "</p>" +
            [s.raw, s.annotated]
              .filter(Boolean)
              .map(
                (p) =>
                  '<a href="' +
                  p +
                  '" target="_blank"><img src="' +
                  p +
                  '"></a>',
              )
              .join("") +
            "</article>",
        )
        .join(""),
  );
}
report();
let browser;
try {
  browser = await chromium.launch({ headless: true });
} catch (error) {
  status.overall = "blocked";
  status.summary = "Browser could not start; no UI action was performed.";
  status.steps.push({
    id: "00-browser",
    state: "blocked",
    label: "Start browser",
    summary: status.summary,
    purpose: "Begin isolated walkthrough.",
    action: "Start installed test browser.",
    controls: [],
    expected: "Browser starts.",
    actual: String(error.message).slice(0, 2000),
  });
  appendFileSync(
    path.join(artifactRoot, "progress.md"),
    "\nBrowser launch blocked. No workspace changes.\n" + error.message,
  );
  report();
  throw error;
}
const context = await browser.newContext({
  viewport: { width: 1350, height: 1000 },
  acceptDownloads: true,
});
const base = new URL(workspace.url).origin;
const auth = await context.request.post(base + "/api/auth/session", {
  data: { token: privateContext.api_token },
});
if (auth.status() !== 204)
  throw Error("Browser session unavailable: HTTP " + auth.status());
await context.tracing.start({ screenshots: true, snapshots: true });
const page = await context.newPage();
const ui = {
  getByTestId: (id) => page.getByTestId(id).filter({ visible: true }),
  getByLabel: (...args) => page.getByLabel(...args).filter({ visible: true }),
};
page.on("pageerror", (e) =>
  diagnostics.push({ kind: "pageerror", message: e.message }),
);
page.on("console", (e) => {
  if (e.type() === "error")
    diagnostics.push({ kind: "console", message: e.text().slice(0, 1000) });
});
page.on("response", (r) => {
  if (r.status() >= 400)
    diagnostics.push({ kind: "http", status: r.status(), url: r.url() });
});
async function capture(id) {
  const raw = "screenshots/raw/" + id + ".png",
    annotated = "screenshots/annotated/" + id + ".png";
  await page.screenshot({ path: path.join(artifactRoot, raw) });
  await page.evaluate(() => {
    const holder = document.createElement("aside");
    holder.id = "walkthrough-overlays";
    holder.style.cssText =
      "position:fixed;bottom:8px;right:8px;z-index:2147483647;padding:10px;max-width:650px;background:#fff;color:#111;font:12px sans-serif";
    const selectors = [
      '[data-testid="activity-bar-workflows-btn"]',
      '[data-testid="workflow-recovery-create-group-input"]',
      '[data-testid="workflow-recovery-create-template-human-input"]',
      '[data-testid="workflow-human-input-instructions"]',
      '[data-testid="workflow-human-input-apply"]',
      '[data-testid="workflow-step-instructions-toggle"]',
      '[data-testid="workflow-step-instructions-policy"]',
      '[data-testid="workflow-step-instructions-apply"]',
      '[data-testid="workflow-recovery-save"]',
      '[data-testid="workflow-transfer-open"]',
      '[data-testid="workflow-transfer-export"]',
      '[data-testid="workflow-transfer-upload"]',
      '[data-testid="workflow-transfer-inspect"]',
      '[data-testid="workflow-transfer-import"]',
    ];
    const labels = [];
    for (const [index, selector] of selectors.entries()) {
      const el = document.querySelector(selector);
      if (!el) continue;
      const box = el.getBoundingClientRect();
      if (!box.width || box.top < 0 || box.top > innerHeight) continue;
      const n = index + 1;
      labels.push(
        n +
          " " +
          (el.getAttribute("aria-label") ||
            el.textContent?.trim().slice(0, 65) ||
            selector),
      );
      const marker = document.createElement("span");
      marker.textContent = String(n);
      marker.style.cssText =
        "position:fixed;z-index:2147483647;background:#168be5;color:white;border:2px solid white;border-radius:20px;padding:3px;left:" +
        Math.min(innerWidth - 25, box.right) +
        "px;top:" +
        box.top +
        "px";
      holder.append(marker);
    }
    holder.append(document.createTextNode(labels.join(" · ")));
    document.body.append(holder);
  });
  await page.screenshot({ path: path.join(artifactRoot, annotated) });
  await page.evaluate(() =>
    document.getElementById("walkthrough-overlays")?.remove(),
  );
  return { raw, annotated };
}
async function step(id, label, action, expected, operation) {
  const row = {
    id,
    state: "pending",
    label,
    summary: label,
    purpose: expected,
    action,
    controls: [],
    expected,
    actual: "Not reached",
  };
  status.steps.push(row);
  status.manualSteps.push({ label, instruction: action });
  report();
  const start = diagnostics.length;
  try {
    if (id !== "01-entry") Object.assign(row, await capture(id + "-before"));
    await operation();
    Object.assign(row, await capture(id + "-after"));
    row.controls = await page
      .locator("button:visible,input:visible,select:visible,textarea:visible")
      .evaluateAll((es) =>
        es.map((e) => ({
          role: e.tagName.toLowerCase(),
          name:
            e.getAttribute("aria-label") ||
            e.getAttribute("title") ||
            e.textContent?.trim().slice(0, 100) ||
            "",
        })),
      );
    row.state = "pass";
    row.actual = "Expected state verified.";
  } catch (error) {
    row.state = "blocked";
    row.actual = String(error.message).slice(0, 3000);
    Object.assign(row, await capture(id + "-stopped"));
    status.overall = "blocked";
    status.summary =
      "Stopped at " +
      label +
      ". Earlier evidence retained; repair is authorized by the saved goal.";
    throw error;
  } finally {
    appendFileSync(
      path.join(artifactRoot, "progress.md"),
      "\n## " +
        new Date().toISOString() +
        " UTC — " +
        id +
        " " +
        label +
        "\nURL: " +
        page.url() +
        "\nAction: " +
        action +
        "\nExpected: " +
        expected +
        "\nActual: " +
        row.actual +
        "\nDiagnostics: " +
        JSON.stringify(diagnostics.slice(start)) +
        "\nRaw: " +
        row.raw +
        "\nAnnotated: " +
        row.annotated +
        "\nStatus: " +
        (row.state === "pass" ? "PASS" : "STOPPED") +
        "\n",
    );
    report();
  }
}
try {
  await step(
    "01-entry",
    "Open ordinary workspace",
    "Open " + workspace.url + ". Click Workflows.",
    "The accepted workflow editor opens from the ordinary workspace control.",
    async () => {
      await page.goto(workspace.url);
      await ui
        .getByTestId("activity-bar-workflows-btn")
        .waitFor({ timeout: 30000 });
      await ui.getByTestId("activity-bar-workflows-btn").click();
      await ui.getByTestId("workflow-file-menu").waitFor({ timeout: 30000 });
    },
  );
  await step(
    "02-blank",
    "Create an isolated blank workflow",
    "Open Workflow files. Click New workflow. Enter " +
      runLabel +
      ". Click Create workflow.",
    "A new empty workflow opens without modifying earlier processes.",
    async () => {
      await ui.getByTestId("workflow-file-menu").click();
      await ui.getByTestId("workflow-file-new").click();
      await ui.getByLabel("Workflow name").fill(runLabel);
      await ui.getByTestId("workflow-file-create").click();
      await page
        .getByRole("heading", { name: "Untitled workflow", exact: true })
        .waitFor({ timeout: 20000 });
      if (await page.locator(".react-flow__node").count())
        throw Error("Unexpected blocks in new workflow");
    },
  );
  await step(
    "03-request",
    "Add a declared input step",
    "Click Input. Choose Request input.",
    "The inspector presents instructions, answer fields and an explicit always/conditional choice.",
    async () => {
      await ui.getByTestId("workflow-recovery-create-group-input").click();
      await ui
        .getByTestId("workflow-recovery-create-template-human-input")
        .click();
      await ui.getByTestId("workflow-human-input-editor").waitFor();
      await ui.getByLabel("Ask for input").waitFor();
    },
  );
  await step(
    "04-fields",
    "Define numeric answer fields",
    "Enter instructions “Specify the width before processing.” Add answer field. Name it width, label Width (mm), choose Number, minimum 1. Apply response declaration.",
    "The friendly editor saves a first-step numeric schema without inventing a response.",
    async () => {
      await ui
        .getByLabel("Instructions for the user")
        .fill("Specify the width before processing.");
      await page
        .getByRole("button", { name: "Add answer field", exact: true })
        .click();
      await ui.getByLabel("Field name", { exact: true }).fill("width");
      await ui.getByLabel("Field label", { exact: true }).fill("Width (mm)");
      await ui.getByLabel("Answer type").selectOption("number");
      await ui.getByLabel("Minimum value", { exact: true }).fill("1");
      await ui.getByTestId("workflow-human-input-apply").click();
      await page
        .getByText("This step is a draft.", { exact: false })
        .waitFor({ state: "hidden" });
      if (await page.getByRole("alert").count())
        throw Error(await page.getByRole("alert").allTextContents());
    },
  );
  await step(
    "05-task",
    "Add an AI report step",
    "Click AI prompt. Choose AI prompt. Enter “Create a short design assumptions report.”",
    "An ordinary AI task exposes per-step instructions inherited from the embedded profile.",
    async () => {
      await ui.getByTestId("workflow-recovery-create-group-document").click();
      await ui
        .getByTestId("workflow-recovery-create-template-ai-prompt")
        .click();
      await ui
        .getByTestId("workflow-recovery-prompt-editor")
        .locator(".recovery-prompt-editor__prompt textarea")
        .fill("Create a short design assumptions report.");
      await ui.getByTestId("workflow-step-instructions-toggle").waitFor();
    },
  );
  await step(
    "06-override",
    "Set a scoped step policy",
    "Expand Step instruction settings. Choose Document reasonable assumptions. Enter “Record finish assumptions separately.” Apply step instructions.",
    "The override changes only this task and uses the normal workflow commands.",
    async () => {
      await ui.getByTestId("workflow-step-instructions-toggle").click();
      await ui
        .getByLabel("Step assumption policy")
        .selectOption("document_reasonable");
      await ui
        .getByLabel("Additional step guidance")
        .fill("Record finish assumptions separately.");
      await ui.getByTestId("workflow-step-instructions-apply").click();
      if (await page.getByRole("alert").count())
        throw Error(await page.getByRole("alert").allTextContents());
    },
  );
  await step(
    "07-save",
    "Save the portable process",
    "Click Save.",
    "The accepted source contains the input declaration and scoped instruction override.",
    async () => {
      await ui.getByTestId("workflow-recovery-save").click();
      await ui.getByTestId("workflow-recovery-save").waitFor();
      await page.waitForFunction(
        () =>
          document.querySelector('[data-testid="workflow-recovery-save"]')
            ?.disabled === true,
      );
      await ui.getByTestId("workflow-recovery-view-code").click();
      const source = await ui
        .getByTestId("workflow-recovery-source-editor")
        .inputValue();
      if (
        !source.includes('"instruction_override"') ||
        !source.includes('"version":2') ||
        !source.includes('"minimum":1')
      )
        throw Error("Portable declaration/override missing from source");
      writeFileSync(path.join(artifactRoot, "accepted.workflow.wflow"), source);
    },
  );
  let transferPath;
  let exportedLayout;
  await step(
    "08-export",
    "Export an instruction-complete transfer",
    "Click Export / import workflow. Choose Bundle with selected reference files and interfaces. Leave optional assets unselected. Download workflow transfer.",
    "An accepted bundle contains source instructions, saved layout and a dependency manifest without copying run authority.",
    async () => {
      await ui.getByTestId("workflow-transfer-open").click();
      await ui.getByTestId("workflow-transfer-dialog").waitFor();
      await ui.getByTestId("workflow-transfer-mode").selectOption("bundle");
      const download = page.waitForEvent("download");
      await ui.getByTestId("workflow-transfer-export").click();
      const file = await download;
      transferPath = path.join(artifactRoot, "workflow-transfer.json");
      await file.saveAs(transferPath);
      await page
        .getByText("Workflow transfer downloaded.", { exact: false })
        .waitFor();
      const data = JSON.parse(readFileSync(transferPath));
      if (!data.bundle?.source?.includes("instructions:"))
        throw Error("Exported source lacks instructions");
      if (data.bundle.mode !== "bundle" || !data.bundle.layout)
        throw Error("Bundle did not preserve saved layout");
      exportedLayout = data.bundle.layout;
    },
  );
  await step(
    "09-inspect",
    "Inspect import dependencies",
    "Choose the downloaded transfer file. Set destination workflows/" +
      runLabel +
      "-import.workflow.wflow. Click Inspect before importing.",
    "The backend checks definition/dependencies without claiming readiness or execution.",
    async () => {
      await ui
        .getByTestId("workflow-transfer-upload")
        .setInputFiles(transferPath);
      await ui
        .getByTestId("workflow-transfer-destination")
        .fill("workflows/" + runLabel + "-import.workflow.wflow");
      await ui.getByTestId("workflow-transfer-inspect").click();
      await page
        .getByText("Definition can be imported", { exact: true })
        .waitFor({ timeout: 30000 });
      await page
        .getByText(
          "Running this workflow still requires local setup and readiness checks.",
          { exact: true },
        )
        .waitFor();
    },
  );
  await step(
    "10-import",
    "Import the inspected definition",
    "Click Import inspected definition.",
    "A distinct accepted workflow opens in a Wright workspace tab without starting a run.",
    async () => {
      await ui.getByTestId("workflow-transfer-import").click();
      await ui
        .getByTestId("workflow-transfer-dialog")
        .waitFor({ state: "hidden", timeout: 30000 });
      await ui.getByTestId("workflow-recovery-view-code").click();
      const source = await ui
        .getByTestId("workflow-recovery-source-editor")
        .inputValue();
      if (
        !source.includes('"instruction_override"') ||
        !source.includes("instructions:")
      )
        throw Error("Imported instructions missing");
      if (await page.getByText("Workflow running", { exact: true }).count())
        throw Error("Import unexpectedly started a run");
      writeFileSync(path.join(artifactRoot, "imported.workflow.wflow"), source);
    },
  );
  await step(
    "11-layout", "Inspect imported block positions",
    "Click Diagram in the imported workflow. Compare the input and report block positions to the exported layout.",
    "The distinct imported definition preserves both saved block positions in the normal diagram.",
    async () => {
      await ui.getByTestId("workflow-recovery-view-diagram").click();
      for(const [id, position] of Object.entries(exportedLayout.positions)) {
        const node = page.locator(`.react-flow__node[data-id="${id}"]`).filter({visible:true});
        await node.waitFor();
        const transform = await node.evaluate(element => element.style.transform);
        const match = /^translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)$/.exec(transform);
        if(!match || Number(match[1]) !== position.x || Number(match[2]) !== position.y)
          throw Error(`Imported position differs for ${id}: ${transform}`);
      }
    }
  );
  status.overall = "pass";
  status.summary =
    "Ordinary workspace authoring, friendly declared input, scoped task instructions and inspected definition transfer are verified. No AI/tool run or review decision was submitted.";
  report();
} catch (error) {
  process.exitCode = 2;
  console.log(
    JSON.stringify({
      status: "stopped",
      reason: String(error.message).slice(0, 1000),
      report: path.join(artifactRoot, "report.html"),
    }),
  );
} finally {
  writeFileSync(
    path.join(artifactRoot, "playwright/diagnostics.json"),
    JSON.stringify(diagnostics, null, 2),
  );
  await context.tracing.stop({
    path: path.join(artifactRoot, "trace/trace.zip"),
  });
  await browser.close();
  report();
}

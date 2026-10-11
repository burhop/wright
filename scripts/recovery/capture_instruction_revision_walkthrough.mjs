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
  "instruction-revisions-" +
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
  title:
    "Saved instruction updates, legacy migration, copies and concurrent edits",
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
let savedB, savedA, copiedSource, activePath;
const currentSource = async (target = page) => {
  const visible = (id) => target.getByTestId(id).filter({ visible: true });
  await visible("workflow-recovery-view-code").click();
  return visible("workflow-recovery-source-editor").inputValue();
};
const editSource = async (source, target = page) => {
  const visible = (id) => target.getByTestId(id).filter({ visible: true });
  await visible("workflow-recovery-view-code").click();
  await visible("workflow-recovery-source-editor").fill(source);
  await visible("workflow-recovery-source-apply").click();
};
const save = async (target = page) => {
  const response = target.waitForResponse(
    (r) =>
      r.request().method() === "PUT" &&
      new URL(r.url()).pathname === "/api/workspace/workflow-sources",
  );
  await target
    .getByTestId("workflow-recovery-save")
    .filter({ visible: true })
    .click();
  const result = await response;
  if (!result.ok()) throw Error("Save rejected: HTTP " + result.status());
  return result.json();
};
try {
  await step(
    "01-entry",
    "Create a separate workflow",
    "Open the ordinary workspace. Click Workflows, Workflow files, New workflow. Name it " +
      runLabel +
      ".",
    "A separate empty accepted definition snapshots current defaults A.",
    async () => {
      await page.goto(workspace.url);
      await ui.getByTestId("activity-bar-workflows-btn").click();
      await ui.getByTestId("workflow-file-menu").click();
      await ui.getByTestId("workflow-file-new").click();
      await ui.getByLabel("Workflow name").fill(runLabel);
      await ui.getByTestId("workflow-file-create").click();
      await page
        .getByRole("heading", { name: runLabel, exact: true })
        .waitFor();
      activePath = new URL(page.url()).searchParams.get("workflowPath");
    },
  );
  await step(
    "02-old-profile",
    "Save a distinct older instruction profile",
    "Open Instructions, Saved instruction resources, task.response. Append Previous profile B marker. Apply workflow instructions and Save.",
    "The altered saved profile B has its own accepted source revision; global defaults remain untouched.",
    async () => {
      const source = await currentSource();
      const profile = JSON.parse(source.match(/^  instructions: (.+)$/m)[1]);
      const asset = profile.assets.find((a) => a.role === "workflow-task");
      await ui.getByTestId("workflow-recovery-instructions").click();
      await ui.getByTestId("workflow-instructions-resources-toggle").click();
      await ui
        .getByTestId("workflow-instructions-resource-" + asset.id)
        .click();
      await ui
        .getByTestId("workflow-instructions-resource-body-" + asset.id)
        .fill(asset.body + "\nPrevious profile B marker.");
      await ui.getByTestId("workflow-instructions-apply").click();
      await page
        .getByText("Instructions applied to the draft.", { exact: false })
        .waitFor();
      await ui.getByTestId("workflow-recovery-modal-close").click();
      savedB = await save();
      if (!savedB.source.includes("Previous profile B marker."))
        throw Error("Older profile was not saved");
    },
  );
  await step(
    "03-diff",
    "Review current defaults before changing the workflow",
    "Open Instructions. Click Update from current defaults. Compare Current instructions and Proposed instructions.",
    "The visible comparison contains B only in the old collection and does not modify the accepted source.",
    async () => {
      await ui.getByTestId("workflow-recovery-instructions").click();
      await page
        .getByRole("button", {
          name: "Update from current defaults…",
          exact: true,
        })
        .click();
      const proposed = await ui
        .getByTestId("workflow-instructions-proposed-collection")
        .inputValue();
      const current = await ui.getByLabel("Current instructions").inputValue();
      if (
        !current.includes("Previous profile B marker.") ||
        proposed.includes("Previous profile B marker.")
      )
        throw Error("Old/new instruction comparison is not distinct");
    },
  );
  await step(
    "04-explicit-update",
    "Apply and save the reviewed update",
    "Click Apply reviewed instruction update. Close Instructions and Save.",
    "Only the explicit reviewed update replaces B with defaults A and creates a new storage revision.",
    async () => {
      await ui.getByTestId("workflow-instructions-apply-update").click();
      await page
        .getByText("Instructions applied to the draft.", { exact: false })
        .waitFor();
      await ui.getByTestId("workflow-recovery-modal-close").click();
      savedA = await save();
      if (
        savedA.storage_revision <= savedB.storage_revision ||
        savedA.source.includes("Previous profile B marker.")
      )
        throw Error(
          "Explicit update did not create a distinct accepted revision",
        );
      writeFileSync(
        path.join(artifactRoot, "instruction-revisions.json"),
        JSON.stringify({ before: savedB, after: savedA }, null, 2),
      );
    },
  );
  await step(
    "05-roundtrip",
    "Switch source and diagram without rewriting instructions",
    "Read Source. Click Diagram, then Source.",
    "The accepted source and exact saved instruction text are unchanged by switching views.",
    async () => {
      const before = await currentSource();
      await ui.getByTestId("workflow-recovery-view-diagram").click();
      if ((await currentSource()) !== before)
        throw Error("Source changed during diagram round trip");
      copiedSource = before;
    },
  );
  for (const [id, action, suffix] of [
    ["06-save-as", "save-as", "saved-copy"],
    ["07-clone", "clone", "clone"],
  ]) {
    await step(
      id,
      action === "clone"
        ? "Clone the accepted definition"
        : "Save the accepted definition as a new file",
      "Open Workflow files. Choose " +
        action +
        ". Name the new file " +
        runLabel +
        "-" +
        suffix +
        ". Submit.",
      "A separate workspace tab preserves exact source instructions without copying execution history or modifying the original.",
      async () => {
        await ui.getByTestId("workflow-file-menu").click();
        await ui.getByTestId("workflow-file-" + action).click();
        await ui.getByLabel("Workflow name").fill(runLabel + "-" + suffix);
        await ui.getByTestId("workflow-file-create").click();
        await page.waitForURL((url) =>
          url.searchParams.get("workflowPath")?.includes(suffix),
        );
        if ((await currentSource()) !== copiedSource)
          throw Error("Copied source/instructions differ");
      },
    );
  }
  await step(
    "08-legacy",
    "Retain an unmigrated legacy definition",
    "In this fresh clone's Source remove only its workflow instructions field. Apply source and Save. Open Instructions.",
    "The saved legacy revision stays unmigrated on open and requires an explicit instruction comparison.",
    async () => {
      await editSource(copiedSource.replace(/^  instructions: .+\n/m, ""));
      await save();
      await ui.getByTestId("workflow-recovery-instructions").click();
      await page
        .getByRole("button", {
          name: "Make instructions explicit…",
          exact: true,
        })
        .waitFor();
      if (await ui.getByTestId("workflow-instructions-policy").count())
        throw Error("Legacy instructions were silently injected");
    },
  );
  await step(
    "09-migration-diff",
    "Review legacy migration explicitly",
    "Click Make instructions explicit. Review current missing instructions and proposed defaults. Apply the reviewed update, close Instructions, and Save.",
    "Legacy migration shows the old/new comparison and only the explicit save embeds the selected collection.",
    async () => {
      await page
        .getByRole("button", {
          name: "Make instructions explicit…",
          exact: true,
        })
        .click();
      if (
        !(await ui.getByLabel("Current instructions").inputValue()).includes(
          "Instruction text was not saved.",
        )
      )
        throw Error("Missing legacy evidence was not disclosed");
      await ui
        .getByTestId("workflow-instructions-proposed-collection")
        .waitFor();
      await ui.getByTestId("workflow-instructions-apply-update").click();
      await page
        .getByText("Instructions applied to the draft.", { exact: false })
        .waitFor();
      await ui.getByTestId("workflow-recovery-modal-close").click();
      const saved = await save();
      if (!saved.source.includes("  instructions:"))
        throw Error("Explicit migration did not save instructions");
      copiedSource = saved.source;
    },
  );
  let other;
  await step(
    "10-concurrent",
    "Keep two editors on the same accepted revision",
    "Open the same copied workflow in a second browser tab. In the first Source change the purpose to Local draft. In the second change it to Concurrent saved change and Save.",
    "The second editor accepts its revision while the first retains its distinct unsaved source.",
    async () => {
      other = await context.newPage();
      await other.goto(page.url());
      await other
        .getByTestId("workflow-recovery-view-code")
        .filter({ visible: true })
        .waitFor();
      const change = (text) =>
        copiedSource.replace(/^  purpose: .+$/m, `  purpose: "${text}"`);
      await editSource(change("Local draft"));
      await editSource(change("Concurrent saved change"), other);
      await save(other);
    },
  );
  await step(
    "11-cas",
    "Reject a conflicting save while retaining both versions",
    "In the original editor click Save. Click Compare stored file.",
    "The stale save returns a conflict; the comparison shows Local draft and Concurrent saved change without overwriting either.",
    async () => {
      const response = page.waitForResponse(
        (r) =>
          r.request().method() === "PUT" &&
          new URL(r.url()).pathname === "/api/workspace/workflow-sources",
      );
      await ui.getByTestId("workflow-recovery-save").click();
      if ((await response).status() !== 409)
        throw Error("Concurrent save did not fail CAS");
      await ui.getByTestId("workflow-recovery-conflict-compare").click();
      if (
        !(
          await ui
            .getByTestId("workflow-recovery-source-comparison-local")
            .inputValue()
        ).includes("Local draft")
      )
        throw Error("Local source lost");
      if (
        !(
          await ui
            .getByTestId("workflow-recovery-source-comparison-stored")
            .inputValue()
        ).includes("Concurrent saved change")
      )
        throw Error("Stored version not displayed");
      await other.close();
    },
  );
  status.overall = "pass";
  status.summary =
    "Explicit default update and legacy migration, exact accepted definition copies, source/diagram round trips and conflicting edits verified through ordinary workspace UI. No process execution or global-default mutation occurred.";
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

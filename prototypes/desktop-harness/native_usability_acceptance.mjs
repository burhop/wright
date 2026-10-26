// Promoted from the preserved 0.20 acceptance supplement; real owners, bounded disposable writes.
// Uses the same MCP Apps fixture as native_navigation_acceptance.mjs, never a native-host claim.
// Served Home -> editor -> working/history navigation with the real MCP/source owner.
// The desktop host is simulated; this is not Windows acceptance. No engineering runs.
// Usage: node prototypes/desktop-harness/native_navigation_acceptance.mjs STATE INPUT.json OUTPUT
// INPUT: { scope:{workspace_id,session_id,path}, edit_copy?:true, run_id?:string }
// edit_copy explicitly permits saving only the supplied disposable source and its drafts.
import { createServer } from "node:http";
import {
  createWriteStream,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
import { chromium, expect } from "@playwright/test";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const state = resolve(process.argv[2]);
const input = JSON.parse(readFileSync(process.argv[3], "utf8"));
const output = resolve(process.argv[4]);
if (
  input.phases?.includes("files-preview-upload-download") &&
  !/^[a-f0-9]{64}$/.test(input.preview_sha256 ?? "")
)
  throw Error("File journey requires the exact retained image digest");
mkdirSync(output); // Never overwrite an earlier receipt.
const scope = input.scope;
if (
  !scope?.workspace_id ||
  !scope.session_id ||
  !scope.path ||
  (input.edit_copy && input.run_id)
)
  throw Error(
    "Supply one exact source; source editing and historical inspection are separate.",
  );
const mcp = new Client({
  name: "wright-navigation-qualification",
  version: "0.1.0",
});
const bridge = resolve(
  process.env.WRIGHT_PROBE_BRIDGE ?? "prototypes/desktop-harness/mcp_bridge.py",
);
const transport = new StdioClientTransport({
  command:
    process.env.WRIGHT_PROBE_PYTHON ??
    resolve(
      process.platform === "win32"
        ? ".venv/Scripts/python.exe"
        : ".venv/bin/python",
    ),
  args: [
    bridge,
    "--state-dir",
    state,
    "--native-editor",
    "--native-working-view",
  ],
  stderr: "pipe",
});
const privateDiagnostics = createWriteStream(resolve(output, "transport.log"), {
  flags: "wx",
  mode: 0o600,
});
transport.stderr?.pipe(privateDiagnostics);
await mcp.connect(transport);
const calls = [];
const errors = [];
const checks = [];
const read = async (name, args) => {
  const result = await mcp.callTool({ name, arguments: args });
  if (result.isError) throw Error(`Owner rejected ${name}`);
  return result.structuredContent ?? JSON.parse(result.content[0].text);
};
const before = await read("wright_workflow_read", scope);
const opened = await read("wright_workflow_open", scope);
const workspace = opened.workspace;
const historyBefore = await read("wright_workflow_history", scope);
const bundlePath = resolve("prototypes/desktop-harness/native-editor.html");
const originalBundle = readFileSync(bundlePath, "utf8");
const bundle = originalBundle.replace(
  "<head>",
  "<head><script>window.openai={widgetState:parent.fixtureWidgetState??{},setWidgetState(value){this.widgetState=value;parent.fixtureWidgetState=value;}};</script>",
);
const safe = (value) => JSON.stringify(value).replaceAll("<", "\\u003c");
const fixture = `<!doctype html><html><meta charset="utf-8"><body style="margin:0;background:#181818;color:#ddd;font:12px system-ui"><div style="height:28px;padding:0 12px;display:flex;align-items:center">Wright prototype · simulated desktop host · actual saved workflow${input.run_id ? " and recorded results · read only" : input.edit_copy ? " · isolated source copy · no engineering run" : " · read-only workspace navigation"}</div><iframe id="panel" title="Wright" style="border:0;width:100%;height:calc(100vh - 28px)"></iframe><script>
const frame=document.getElementById('panel');
window.addEventListener('message',async event=>{
 if(event.source!==frame.contentWindow)return;
 const m=event.data, send=data=>frame.contentWindow.postMessage({jsonrpc:'2.0',...data},'*');
 if(m.method==='ui/initialize')send({id:m.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'wright-navigation-fixture',version:'1'},hostCapabilities:{serverTools:{},updateModelContext:{}},hostContext:{theme:'dark'}}});
 if(m.method==='ui/notifications/initialized'){
  send({method:'ui/notifications/tool-input',params:{arguments:${safe({ workspace_id: scope.workspace_id, session_id: scope.session_id })}}});
  send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:{view:'home',selection:${safe(workspace)}}}});
 }
 if(m.method==='ui/update-model-context'){window.lastContext=m.params;send({id:m.id,result:{}});}
 if(m.method==='tools/call'){
  try {const r=await fetch('/tool',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(m.params)});send({id:m.id,result:await r.json()});}
  catch {send({id:m.id,error:{code:-32000,message:'Qualification transport unavailable'}});}
 }
});frame.srcdoc=${safe(bundle)};
</script></body></html>`;

const title =
  input.disposable_title ?? "Desktop usability " + new Date().toISOString();
const importPath =
  input.import_path ??
  "workflows/usability-import-" + Date.now() + ".workflow.wflow";
const uploadFilename = "desktop-usability-" + Date.now() + ".txt";
const uploadText =
  "Wright Codex UI acceptance test, 23 October 2026. Nonsecret disposable text.\n";
let created,
  importDone = false,
  uploadDone = false;
const safeReads = new Set([
  "wright_recorded_run_read",
  "wright_workspace_list",
  "wright_workspace_files",
  "wright_workflow_read",
  "wright_workflow_open",
  "wright_editor_drafts_read",
  "wright_workflow_history",
  "wright_workspace_file_preview",
  "wright_workspace_file_download",
  "wright_connections_list",
  "wright_connection_plans",
  "wright_connection_plan_read",
  "wright_workflow_import_inspect",
  "wright_workflow_export",
]);
const server = createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/") {
      res.writeHead(200, { "Content-Type": "text/html;charset=utf-8" });
      res.end(fixture);
      return;
    }
    if (req.method !== "POST" || req.url !== "/tool")
      throw Error("Route denied");
    let body = "";
    for await (const chunk of req) body += chunk;
    const { name, arguments: args } = JSON.parse(body);
    const r = args.request ?? args;
    if (
      name !== "wright_workspace_list" &&
      (r.workspace_id !== scope.workspace_id ||
        r.session_id !== scope.session_id)
    )
      throw Error("Workspace denied");
    if (name === "wright_workflow_create") {
      if (
        created ||
        !r.source.includes(title) ||
        !/^workflows\/untitled-workflow-[a-f0-9-]+\.workflow\.wflow$/.test(
          r.path,
        )
      )
        throw Error("Creation denied");
      created = { path: r.path, pending: true };
    } else if (
      ["wright_workflow_save", "wright_editor_draft_save"].includes(name)
    ) {
      if (!created || r.path !== created.path)
        throw Error("Only disposable source may be edited");
    } else if (name === "wright_workflow_import") {
      if (
        importDone ||
        r.destination_path !== importPath ||
        !r.bundle?.source?.includes(title)
      )
        throw Error("Import denied");
      importDone = true;
    } else if (name === "wright_workspace_file_upload") {
      if (
        uploadDone ||
        r.filename !== uploadFilename ||
        r.content_base64 !== Buffer.from(uploadText).toString("base64")
      )
        throw Error("Upload denied");
      uploadDone = true;
    } else if (!safeReads.has(name)) throw Error("Operation denied: " + name);
    if (
      ["wright_workflow_export", "wright_workflow_import_inspect"].includes(
        name,
      ) &&
      (!created ||
        (name === "wright_workflow_export"
          ? r.path !== created.path
          : r.destination_path !== importPath))
    )
      throw Error("Transfer subject denied");
    const result = await mcp.callTool({ name, arguments: args });
    const data =
      result.structuredContent ??
      (result.content[0]?.type === "text"
        ? JSON.parse(result.content[0].text)
        : null);
    if (name === "wright_workflow_create" && !result.isError) created = data;
    calls.push({
      name,
      path: r.path ?? r.destination_path ?? null,
      is_error: !!result.isError,
    });
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(result));
  } catch (error) {
    errors.push(String(error));
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        isError: true,
        content: [{ type: "text", text: "Acceptance harness denied request." }],
      }),
    );
  }
});
await new Promise((done) => server.listen(0, "127.0.0.1", done));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 1080, height: 900 },
  acceptDownloads: true,
});
page.on("pageerror", (e) => errors.push(e.message));
const frame = page.frameLocator("#panel");
const observations = {
  host: {
    platform: process.platform,
    architecture: process.arch,
    node: process.version,
  },
  boundary:
    "Compiled Wright UI with actual MCP/backend/storage; simulated desktop host, not native OpenAI desktop acceptance",
  checks,
  errors,
  calls,
};
async function shot(name) {
  await page.screenshot({ path: resolve(output, name + ".png") });
}
async function record(name, fn) {
  if (input.phases && !input.phases.includes(name)) return;
  try {
    await fn();
    checks.push({ name, status: "PASS" });
  } catch (e) {
    checks.push({ name, status: "FAIL", error: String(e) });
    await shot(name.replace(/[^a-z0-9]+/gi, "-") + "-failure");
    writeFileSync(
      resolve(output, name.replace(/[^a-z0-9]+/gi, "-") + "-dom.txt"),
      await frame.locator("body").innerText(),
    );
  }
}
try {
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await expect(
    frame.getByRole("button", { name: "New workflow", exact: true }),
  ).toBeVisible();
  await record("workspace-list-density", async () => {
    await page.setViewportSize({ width: 480, height: 820 });
    await expect(frame.getByText("Reading saved workflow names…")).toHaveCount(0);
    const workflows = frame.getByRole("region", { name: "Workflows", exact: true }).locator("ul");
    await expect(workflows.locator("li")).not.toHaveCount(0);
    await shot("workflow-list-density");
    const workflowHeight = await workflows.evaluate((el) => el.clientHeight);
    expect(workflowHeight).toBeLessThanOrEqual(360);
    await workflows.focus();
    await workflows.press("End");
    await expect(workflows.locator("li").last()).toBeInViewport();
    await frame.getByRole("button", { name: "Files", exact: true }).click();
    const files = frame.getByRole("region", { name: "Files", exact: true }).locator(":scope > ul");
    const total = await files.locator("li").count();
    expect(total).toBeGreaterThan(20);
    await expect(files.locator("li").first()).toBeInViewport({ ratio: 1 });
    await expect(frame.getByLabel("Choose input file")).not.toBeVisible();
    await shot("file-list-density");
    const bounds = await files.evaluate((el) => ({ height: el.clientHeight, scrollHeight: el.scrollHeight, overflow: getComputedStyle(el).overflowY }));
    expect(bounds.height).toBeLessThanOrEqual(360);
    expect(bounds.scrollHeight).toBeGreaterThan(bounds.height);
    expect(bounds.overflow).toBe("auto");
    await files.focus();
    await files.press("End");
    await expect(files.locator("li").last()).toBeInViewport();
    await shot("file-list-keyboard-end");
    const search = frame.getByLabel("Find a file", { exact: true });
    await search.fill("block-isometric.png");
    await expect(files.locator("li")).not.toHaveCount(0);
    expect(await frame.locator("body").evaluate((el) => el.scrollWidth > el.clientWidth + 1)).toBe(false);
    await shot("file-list-filtered");
    const unchanged = await read("wright_workflow_read", scope);
    const historyAfter = await read("wright_workflow_history", scope);
    expect(unchanged.storage_digest).toBe(before.storage_digest);
    expect(historyAfter).toEqual(historyBefore);
    observations.list_density = { workflow_height: workflowHeight, files: total, ...bounds, keyboard_last_file_visible: true, source_and_history_unchanged: true };
    await page.setViewportSize({ width: 1080, height: 900 });
    await frame.getByRole("button", { name: "Workflows", exact: true }).click();
  });
  await record("friendly-search", async () => {
    const search = frame.getByLabel("Find a workflow", { exact: true });
    const nameLine = /^  name: (".*")$/m.exec(before.source);
    if (!nameLine) throw Error("Expected an accepted workflow title");
    const savedTitle = JSON.parse(nameLine[1]);
    const filename = scope.path
      .split("/")
      .at(-1)
      .replace(/(?:\.workflow)?\.wflow$/, "");
    for (const query of input.search_queries ?? [
      filename,
      filename.replace(/[-_]+/g, " "),
      savedTitle,
    ]) {
      await search.fill(query);
      await expect(
        frame.getByRole("button", { name: savedTitle, exact: true }),
      ).toBeVisible();
    }
    await shot("search-saved-title");
    await search.fill("");
  });
  await record("connections", async () => {
    await frame
      .getByRole("button", { name: "Connections", exact: true })
      .click();
    await expect(frame.getByText("Loading connections…")).toHaveCount(0);
    const catalog = frame.locator(".native-connections__items");
    await expect(catalog.locator("li").first()).toBeVisible();
    expect(await catalog.evaluate((el) => el.clientHeight)).toBeLessThanOrEqual(520);
    await catalog.focus();
    await catalog.press("End");
    await expect(catalog.locator("li").last()).toBeInViewport();
    await shot("connections-catalog-bounded");
    await frame.getByLabel("Find an MCP").fill("SteveCAD");
    await frame
      .getByRole("button", { name: "Search / refresh", exact: true })
      .click();
    await expect(frame.getByText(/Current readiness:/)).toBeVisible();
    await expect(frame.getByText(/^Authentication: (?:not checked here|credentials needed)\.$/)).toBeVisible();
    await page.setViewportSize({ width: 480, height: 820 });
    const card = frame.locator(".native-connections__items > li");
    await expect(card).toHaveCount(1);
    await shot("connections-default-narrow");
    const cardHeight = await card.evaluate((el) => el.getBoundingClientRect().height);
    expect(cardHeight).toBeLessThanOrEqual(380);
    observations.connections_card_height = cardHeight;
    await page.setViewportSize({ width: 1080, height: 900 });
    await shot("connections-current-readiness");
    await expect(frame.getByText("Manage connection", { exact: true })).toBeVisible();
    await expect(frame.getByRole("button", { name: /^Disable SteveCAD.* in this workspace$/i })).not.toBeVisible();
    await frame.getByText("Manage connection", { exact: true }).click();
    await expect(frame.getByRole("button", { name: /^Disable SteveCAD.* in this workspace$/i })).toBeVisible();
    await frame.getByText("Manage connection", { exact: true }).click();
    await frame.getByText("Readiness details", { exact: true }).click();
    await shot("connections-readiness");
    observations.connections = await frame
      .getByRole("region", { name: "Connections", exact: true })
      .innerText();
    await frame
      .getByRole("button", { name: /Saved setup for SteveCAD/i })
      .click();
    await frame
      .getByRole("button", { name: /Open completed setup/ })
      .first()
      .click();
    await expect(
      frame.getByText("Plan state: completed.", { exact: true }),
    ).toBeVisible();
    await expect(
      frame.getByRole("button", { name: /^Connect SteveCAD/ }),
    ).not.toBeVisible();
    await expect(
      frame.getByRole("region", { name: "Setup plan", exact: true }),
    ).toBeFocused();
    await expect(frame.getByRole("checkbox")).toHaveCount(0);
    await shot("connections-saved-setup");
    await page.setViewportSize({ width: 480, height: 820 });
    await shot("connections-narrow");
    expect(
      await frame
        .locator("body")
        .evaluate((e) => e.scrollWidth > e.clientWidth + 1),
    ).toBe(false);
    await page.setViewportSize({ width: 1080, height: 900 });
    await frame.getByRole("button", { name: "Workflows", exact: true }).click();
  });
  await record("narrow-file-preview", async () => {
    await frame.getByRole("button", { name: "Files", exact: true }).click();
    await page.setViewportSize({ width: 480, height: 820 });
    await frame
      .getByRole("button", { name: "inspection.json", exact: true })
      .click();
    const preview = frame.getByRole("region", {
      name: "File preview",
      exact: true,
    });
    await expect(preview.locator("pre")).toBeVisible();
    await expect(preview.locator("pre")).toBeInViewport();
    await expect(preview).toBeFocused();
    expect(
      await frame
        .locator("body")
        .evaluate((e) => e.scrollWidth > e.clientWidth + 1),
    ).toBe(false);
    await shot("file-preview-narrow");
    await frame
      .getByRole("button", { name: "Close preview", exact: true })
      .click();
    await expect(
      frame.getByRole("button", { name: "inspection.json", exact: true }),
    ).toBeFocused();
    await page.setViewportSize({ width: 1080, height: 900 });
  });
  await record("create-edit-undo-redo-save-reopen", async () => {
    await frame.getByRole("button", { name: "Workflows", exact: true }).click();
    await frame
      .getByRole("button", { name: "New workflow", exact: true })
      .click();
    await frame.getByLabel("Workflow name", { exact: true }).fill(title);
    await frame
      .getByRole("button", { name: "Create workflow", exact: true })
      .click();
    await expect(frame.getByTestId("workflow-recovery-save")).toBeVisible();
    await frame.getByTestId("workflow-recovery-view-code").click();
    const editor = frame.getByTestId("workflow-recovery-source-editor");
    const original = await editor.inputValue();
    const step =
      'input acceptance_note\n  name: "Acceptance test note"\n  purpose: "Disposable UI check; do not run"\n  step_type: "work"\n  provided_by: "engineer"\n  group: null\n  inputs: []\n  outputs: []\n  instructions: "Nonsecret UI acceptance text only."\n  settings: {"input_mode":"text","input_text":"Initial note"}\n  tool: null\n  reusable_step: null\nend\n';
    await editor.fill(original + "\n" + step);
    await frame.getByTestId("workflow-recovery-source-apply").click();
    await frame.getByTestId("workflow-recovery-view-diagram").click();
    await shot("editor-added-step");
    await frame.getByRole("button", { name: "Undo", exact: true }).click();
    await frame.getByTestId("workflow-recovery-view-code").click();
    await expect(editor).not.toHaveValue(/input acceptance_note/);
    await frame.getByRole("button", { name: "Redo", exact: true }).click();
    await expect(editor).toHaveValue(/input acceptance_note/);
    await editor.fill(
      (await editor.inputValue()).replace("Initial note", "Edited note"),
    );
    await frame.getByTestId("workflow-recovery-source-apply").click();
    await frame.getByTestId("workflow-recovery-view-diagram").click();
    await frame.getByTestId("workflow-recovery-save").click();
    await expect(frame.getByTestId("workflow-recovery-save-status")).toHaveText(
      "Saved",
    );
    await shot("editor-saved");
    await frame
      .getByRole("button", { name: "← Workspace home", exact: true })
      .click();
    await frame.getByLabel("Find a workflow", { exact: true }).fill(title);
    await expect(
      frame.getByRole("button", { name: title, exact: true }),
    ).toBeVisible();
    await shot("created-workflow-list");
    observations.created_path = created.path;
    await frame.getByRole("button", { name: title, exact: true }).click();
    await frame.getByTestId("workflow-recovery-view-code").click();
    await expect(editor).toHaveValue(/Edited note/);
    await shot("editor-reopened-source");
  });
  await record("export-import-disposable", async () => {
    if (!created?.storage_digest)
      throw Error("Creation not confirmed; skip transfer");
    await frame
      .getByRole("button", { name: "Export / import workflow", exact: true })
      .click();
    await expect(frame.getByTestId("workflow-transfer-dialog")).toBeVisible();
    await frame.getByTestId("workflow-transfer-mode").selectOption("source");
    const downloadEvent = page.waitForEvent("download");
    await frame.getByTestId("workflow-transfer-export").click();
    const download = await downloadEvent;
    const exportedPath = resolve(output, download.suggestedFilename());
    await download.saveAs(exportedPath);
    observations.export_path = exportedPath;
    await frame
      .getByTestId("workflow-transfer-upload")
      .setInputFiles(exportedPath);
    await frame.getByTestId("workflow-transfer-destination").fill(importPath);
    await frame.getByTestId("workflow-transfer-inspect").click();
    await expect(
      frame.getByText("Definition can be imported", { exact: true }),
    ).toBeVisible();
    await shot("import-inspected");
    await frame.getByTestId("workflow-transfer-import").click();
    await expect(frame.getByTestId("workflow-transfer-dialog")).toHaveCount(0);
    await expect(frame.getByTestId("workflow-recovery-save")).toBeVisible();
    await shot("imported-workflow");
  });
  await record("files-preview-upload-download", async () => {
    if (
      await frame
        .getByRole("button", { name: "← Workspace home", exact: true })
        .count()
    )
      await frame
        .getByRole("button", { name: "← Workspace home", exact: true })
        .click();
    await frame.getByRole("button", { name: "Files", exact: true }).click();
    const list = frame.getByRole("region", { name: "Files", exact: true });
    await list
      .getByRole("button", { name: "inspection.json", exact: true })
      .click();
    const preview = frame.getByRole("region", {
      name: "File preview",
      exact: true,
    });
    await expect(preview.locator("pre")).toBeVisible();
    observations.file_preview_position = await preview.evaluate((e) => ({
      top: e.getBoundingClientRect().top,
      bottom: e.getBoundingClientRect().bottom,
      viewport: innerHeight,
      scrollY,
    }));
    expect(observations.file_preview_position.top).toBeGreaterThanOrEqual(-1);
    await expect(preview.getByRole("heading")).toBeInViewport();
    await expect(preview.locator("pre")).toBeInViewport();
    await expect(preview).toBeFocused();
    await shot("file-preview-visible");
    await frame
      .getByRole("button", { name: "Close preview", exact: true })
      .click();
    await expect(
      list.getByRole("button", { name: "inspection.json", exact: true }),
    ).toBeFocused();
    await frame
      .getByLabel("Find a file", { exact: true })
      .fill("block-isometric.png");
    await list
      .getByRole("button", { name: "block-isometric.png", exact: true })
      .click();
    const pngEvent = page.waitForEvent("download");
    await preview
      .getByRole("button", { name: "Download file", exact: true })
      .click();
    const png = await pngEvent;
    const pngPath = resolve(output, "block-isometric.png");
    await png.saveAs(pngPath);
    observations.download = {
      path: pngPath,
      sha256: createHash("sha256").update(readFileSync(pngPath)).digest("hex"),
      windows_browser_delivery: process.platform === "win32",
      native_host_delivery: false,
    };
    expect(observations.download.sha256).toBe(input.preview_sha256);
    await shot("image-download");
    const uploadPath = resolve(output, uploadFilename);
    writeFileSync(uploadPath, uploadText);
    await frame.getByText("Upload a file", { exact: true }).click();
    await frame.getByLabel("Choose input file").setInputFiles(uploadPath);
    await frame
      .getByRole("button", { name: "Upload file", exact: true })
      .click();
    await expect(
      frame.getByText(
        `Saved ${uploadFilename} in uploads. Existing files are unchanged.`,
        { exact: true },
      ),
    ).toBeVisible();
    await list
      .getByRole("button", { name: uploadFilename, exact: true })
      .click();
    await expect(preview.locator("pre")).toHaveText(uploadText);
    await expect(preview).toBeFocused();
    await shot("uploaded-text-preview");
    await page.setViewportSize({ width: 480, height: 820 });
    await expect(preview.locator("pre")).toBeInViewport({ ratio: 1 });
    await expect(preview).toBeFocused();
    expect(
      await frame
        .locator("body")
        .evaluate((e) => e.scrollWidth > e.clientWidth + 1),
    ).toBe(false);
    await shot("files-narrow");
    const search = frame.getByLabel("Find a file", { exact: true });
    await search.focus();
    await page.setViewportSize({ width: 520, height: 820 });
    await expect(search).toBeFocused();
    await expect(search).toBeInViewport({ ratio: 1 });
    observations.preview_resize = {
      active_preview_text_visible: true,
      preserves_file_search_focus_and_visibility: true,
    };
    observations.upload_filename = uploadFilename;
  });
} finally {
  observations.status =
    checks.some((c) => c.status === "FAIL") || errors.length ? "FAIL" : "PASS";
  observations.bundle_sha256 = createHash("sha256")
    .update(originalBundle)
    .digest("hex");
  observations.created = created
    ? { path: created.path, confirmed: !!created.storage_digest }
    : null;
  writeFileSync(
    resolve(output, "report.json"),
    JSON.stringify(observations, null, 2),
  );
  if (observations.status === "FAIL") process.exitCode = 1;
  await browser.close();
  server.closeAllConnections();
  await new Promise((done) => server.close(done));
  await mcp.close();
  console.log(output);
}

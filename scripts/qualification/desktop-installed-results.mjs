// Installed MCP + actual bundled UI + copied retained state. Host is simulated.
// Retained history stays read-only; authoring uses a separate disposable workspace.
import { createServer } from "node:http";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { chromium, expect } from "@playwright/test";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
const [receiptPath, output] = process.argv.slice(2);
const receipt = JSON.parse(readFileSync(receiptPath, "utf8"));
const fixture = receipt.retained.scope;
const scope = {
  workspace_id: fixture.workspace_id,
  session_id: fixture.session_id,
};
const disposable = receipt.workspace_result;
const authoring = new Set([
  "wright_workflow_save",
  "wright_editor_draft_save",
  "wright_workflow_export",
  "wright_workflow_import_inspect",
  "wright_workflow_import",
  "wright_workflow_transfer_assets",
]);
mkdirSync(output);
const calls = [],
  errors = [],
  checks = [];
const mcp = new Client({
  name: "wright-installed-results-check",
  version: "1",
});
const transport = new StdioClientTransport({
  command: receipt.python,
  args: [
    "-I",
    "-m",
    "wright_engineering.cli",
    "mcp",
    "desktop",
    "--api-url",
    process.env.WRIGHT_DESKTOP_API_URL,
  ],
  env: { WRIGHT_HOME: receipt.home },
  cwd: receipt.home,
  stderr: "pipe",
});
transport.stderr?.on("data", () => {});
await mcp.connect(transport);
const call = async (name, args) => {
  const result = await mcp.callTool({ name, arguments: args });
  if (result.isError) throw Error(`Owner rejected ${name}`);
  return result.structuredContent ?? JSON.parse(result.content[0].text);
};
const tools = await mcp.listTools();
const uri = tools.tools.find((t) => t.name === "wright_home")._meta.ui
  .resourceUri;
const html = (await mcp.readResource({ uri })).contents[0].text;
const home = await call("wright_home", {});
const safe = (x) => JSON.stringify(x).replaceAll("<", "\\u003c");
const shim =
  "<head><script>window.openai={get widgetState(){return parent.savedState??{}},setWidgetState(x){parent.savedState=x}};</script>";
const host = `<!doctype html><html><meta charset="utf-8"><body style="margin:0;background:#191919;color:white;font:12px system-ui"><header style="height:28px">SIMULATED desktop host · installed Wright · copied history · no engineering run</header><iframe id="panel" title="Wright" style="border:0;width:100%;height:calc(100vh - 28px)"></iframe><script>
const f=document.querySelector('iframe');window.openRequests=[];
addEventListener('message',async e=>{if(e.source!==f.contentWindow)return;const m=e.data;const send=x=>f.contentWindow.postMessage({jsonrpc:'2.0',...x},'*');
if(m.method==='ui/initialize')send({id:m.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'installed-browser-fixture',version:'1'},hostCapabilities:{serverTools:{},updateModelContext:{},experimental:{'openai/files':{},'openai/resource':{}}},hostContext:{theme:'dark',platform:'desktop'}}});
else if(m.method==='ui/notifications/initialized'){send({method:'ui/notifications/tool-input',params:{arguments:{}}});send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:${safe(home)}}});}
else if(m.method==='tools/call'){const r=await fetch('/tool',{method:'POST',body:JSON.stringify(m.params)});send({id:m.id,result:await r.json()});}
else if(m.method==='openai/files/open'){window.openRequests.push(m.params);send({id:m.id,result:{}});}
else if(m.method==='ui/update-model-context'){window.context=m.params;send({id:m.id,result:{}});}
else if(m.id)send({id:m.id,result:{}});});f.srcdoc=${safe(html.replace("<head>", shim))};</script></body></html>`;
const allowed = new Set([
  "wright_workspace_pending",
  "wright_workflow_editor_tools",
  "wright_workflow_editor_options",
  "wright_workspace_list",
  "wright_workspace_files",
  "wright_workflow_read",
  "wright_workflow_open",
  "wright_workflow_history",
  "wright_editor_drafts_read",
  "wright_workspace_file_describe",
  "wright_recorded_run_read",
  "wright_process_ui_read",
  "wright_workspace_file_preview",
  "wright_workspace_file_download",
]);
const server = createServer(async (req, res) => {
  if (req.method === "GET" && req.url === "/favicon.ico") {
    res.writeHead(204).end();
    return;
  }
  if (req.method === "GET" && req.url === "/") {
    res.setHeader("Content-Type", "text/html");
    res.end(host);
    return;
  }
  try {
    if (req.method !== "POST" || req.url !== "/tool")
      throw Error(`Unknown test route: ${req.method} ${req.url}`);
    let text = "";
    for await (const part of req) {
      text += part;
      if (text.length > 1048576) throw Error("Oversized test request");
    }
    const { name, arguments: args } = JSON.parse(text),
      body = args.request ?? args;
    const isDisposable =
      body.workspace_id === disposable.workspace_id &&
      body.session_id === disposable.session_id;
    if (!allowed.has(name) && !(isDisposable && authoring.has(name)))
      throw Error(`Action denied by read-only fixture: ${name}`);
    if (
      name !== "wright_workspace_list" &&
      !isDisposable &&
      (body.workspace_id !== scope.workspace_id ||
        body.session_id !== scope.session_id)
    )
      throw Error("Foreign scope");
    if (
      name === "wright_process_ui_read" &&
      !["snapshot", "representation", "navigation", "reasoning"].includes(
        body.operation,
      )
    )
      throw Error("Mutation denied");
    if (body.run_id && body.run_id !== fixture.run_id)
      throw Error("Different run");
    if (name === "wright_workflow_editor_options" && body.include_resources)
      throw Error(
        "Live resource enumeration is outside this retained-results test",
      );
    const result = await mcp.callTool({ name, arguments: args });
    calls.push({
      name,
      arguments: args,
      isError: !!result.isError,
      ...(result.structuredContent?.ok === false
        ? { rejection: result.structuredContent }
        : {}),
    });
    res.end(JSON.stringify(result));
  } catch (error) {
    errors.push(String(error));
    res.end(
      JSON.stringify({
        isError: true,
        content: [
          { type: "text", text: "Read-only fixture rejected the request." },
        ],
      }),
    );
  }
});
await new Promise((done) => server.listen(0, "127.0.0.1", done));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
page.setDefaultTimeout(20000);
page.on("pageerror", (e) => errors.push(String(e)));
const f = page.frameLocator("#panel");
let status = "FAIL";
try {
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await f
    .getByLabel("Workspace", { exact: true })
    .selectOption(scope.workspace_id);
  const title = "Inspect existing block and recover preview";
  const row = f.getByRole("button", { name: title, exact: true });
  await expect(row).toBeVisible();
  const technical = f
    .locator("details.native-home__file-options")
    .filter({ hasText: /^Technical run records/ });
  await expect(technical).not.toHaveAttribute("open");
  const fileList = f.getByRole("list", {
    name: "Workspace files",
    exact: true,
  });
  const previews = fileList.getByRole("button", {
    name: /^block-isometric\.png — /,
  });
  await expect(previews).toHaveCount(3);
  const names = await previews.evaluateAll((nodes) =>
    nodes.map((node) => node.getAttribute("aria-label")),
  );
  if (new Set(names).size !== 3)
    throw Error("Duplicate result files remain indistinguishable");
  await expect(
    fileList.getByRole("button", { name: /^inspection\.json — / }),
  ).toHaveCount(3);
  await page.screenshot({ path: resolve(output, "workspace-files.png") });
  await page.setViewportSize({ width: 480, height: 820 });
  await expect(previews.first()).toBeInViewport();
  const kind = previews.first().locator(".native-home__file-kind");
  await expect(kind).toHaveText("PNG");
  const kindFits = await kind.evaluate((node) => {
    const range = document.createRange();
    range.selectNodeContents(node);
    return range.getClientRects().length === 1;
  });
  if (!kindFits) throw Error("File type wraps across lines in the narrow panel");
  const fileOverflow = await f
    .locator("body")
    .evaluate((node) => node.scrollWidth > node.clientWidth + 1);
  if (fileOverflow) throw Error("Workspace files overflow the narrow panel");
  await page.screenshot({
    path: resolve(output, "workspace-files-narrow.png"),
  });
  await page.setViewportSize({ width: 1100, height: 900 });
  await f
    .getByLabel("Find a file", { exact: true })
    .fill("block preview recovery");
  await expect(row).toBeInViewport();
  await page.screenshot({ path: resolve(output, "workspace.png") });
  await row.click();
  await expect
    .poll(() => page.evaluate(() => window.openRequests.length))
    .toBe(1);
  await expect(f.getByText(/If you see text, use/)).toBeVisible();
  await f.getByLabel(`File details for ${title}`, { exact: true }).click();
  await f
    .getByRole("button", { name: "Open workflow here", exact: true })
    .click();
  await expect(f.getByTestId("workflow-recovery-save")).toBeVisible();
  await expect
    .poll(() => page.evaluate(() => window.openRequests.length))
    .toBe(1);
  checks.push(
    "Workspace title search and explicit editor fallback work after acknowledged native open; no rendering claim from acknowledgement",
  );
  await f.getByTestId("workflow-recovery-view-code").click();
  await expect(f.getByTestId("workflow-recovery-source-editor")).toHaveValue(
    receipt.retained.source.source.replace(/\r\n?/g, "\n"),
  );
  await f.getByTestId("workflow-recovery-view-diagram").click();
  await page.screenshot({ path: resolve(output, "workflow.png") });
  await f.getByRole("button", { name: "Run workflow", exact: true }).click();
  await f.getByRole("button", { name: "Previous runs", exact: true }).click();
  const run = f.getByRole("listitem").filter({ hasText: fixture.run_id });
  await run
    .getByRole("button", { name: "Open working view", exact: true })
    .click();
  const result = f
    .locator(".wp-result")
    .filter({ hasText: "block-isometric.png" });
  await expect(result).toBeVisible();
  await result.getByRole("button", { name: "Open file", exact: true }).click();
  const image = f.getByRole("img", {
    name: "block-isometric.png",
    exact: true,
  });
  await expect(image).toBeInViewport();
  await expect
    .poll(() => image.evaluate((el) => el.naturalWidth))
    .toBeGreaterThan(0);
  const digest = await image.evaluate(async (el) =>
    Array.from(
      new Uint8Array(
        await crypto.subtle.digest(
          "SHA-256",
          await (await fetch(el.src)).arrayBuffer(),
        ),
      ),
    )
      .map((n) => n.toString(16).padStart(2, "0"))
      .join(""),
  );
  expect(digest).toBe(fixture.image_sha256);
  await page.screenshot({ path: resolve(output, "retained-preview.png") });
  await f.getByRole("button", { name: "Back to results", exact: true }).click();
  await expect(
    result.getByRole("button", { name: "Open file", exact: true }),
  ).toBeFocused();
  await result
    .getByRole("button", { name: "Open producing step", exact: true })
    .click();
  const inspector = f.getByTestId("workflow-recovery-inspector");
  await expect(inspector).toContainText("block-isometric.png");
  await expect(inspector).not.toContainText(
    "different saved workflow or an edited draft",
  );
  await expect(
    f.getByRole("button", { name: /Results · 1\/1 available/ }),
  ).toBeVisible();
  await page.screenshot({ path: resolve(output, "producing-step.png") });
  await f.getByRole("button", { name: "View run", exact: true }).click();
  await expect
    .poll(() =>
      page.evaluate(() => window.context?.structuredContent?.workflow?.run_id),
    )
    .toBe(fixture.run_id);
  await page.setViewportSize({ width: 480, height: 820 });
  expect(
    await f
      .locator("body")
      .evaluate((el) => el.scrollWidth > el.clientWidth + 1),
  ).toBe(false);
  await page.screenshot({ path: resolve(output, "results-narrow.png") });
  expect(errors).toEqual([]);
  checks.push(
    "Exact retained image visibly rendered and hashed; producing step shows available output without false mismatch; return retains selected run; narrow layout has no body overflow",
  );
  await page.setViewportSize({ width: 1100, height: 900 });
  await f.getByRole("button", { name: "Workspace home", exact: false }).click();
  await f
    .getByRole("button", { name: "Change workspace", exact: true })
    .click();
  await f
    .getByLabel("Workspace", { exact: true })
    .selectOption(disposable.workspace_id);
  await f
    .getByLabel("File details for Installed artifact check", { exact: true })
    .click();
  await f
    .getByRole("button", { name: "Open workflow here", exact: true })
    .click();
  const name = f.getByRole("textbox", { name: "Workflow name", exact: true });
  await name.fill("Engineering authoring check");
  await name.press("Enter");
  await f.getByTestId("workflow-recovery-undo").click();
  await expect(name).toHaveValue("Installed artifact check");
  await f.getByTestId("workflow-recovery-redo").click();
  await expect(name).toHaveValue("Engineering authoring check");
  await f.getByTestId("workflow-recovery-save").click();
  await expect(f.getByTestId("workflow-recovery-save")).toBeDisabled();
  await f.getByRole("button", { name: "Workspace home", exact: false }).click();
  await f
    .getByLabel("Find a file", { exact: true })
    .fill("Engineering authoring check");
  await expect(
    f.getByRole("button", { name: "Engineering authoring check", exact: true }),
  ).toBeVisible();
  await f
    .getByLabel("File details for Engineering authoring check", { exact: true })
    .click();
  await f
    .getByRole("button", { name: "Open workflow here", exact: true })
    .click();
  await expect(name).toHaveValue("Engineering authoring check");
  await f.getByText("Workflow details", { exact: true }).click();
  await f
    .getByRole("button", { name: "Export / import workflow", exact: true })
    .click();
  const downloadPromise = page.waitForEvent("download");
  await f.getByTestId("workflow-transfer-export").click();
  const download = await downloadPromise;
  const transferPath = resolve(output, "disposable-transfer.json");
  await download.saveAs(transferPath);
  await f.getByTestId("workflow-transfer-upload").setInputFiles(transferPath);
  await f
    .getByTestId("workflow-transfer-destination")
    .fill("workflows/imported-authoring-check.workflow.wflow");
  await f.getByTestId("workflow-transfer-inspect").click();
  await f
    .getByRole("button", { name: "Import inspected definition", exact: true })
    .click();
  await expect
    .poll(() =>
      page.evaluate(() => window.context?.structuredContent?.workflow?.path),
    )
    .toBe("workflows/imported-authoring-check.workflow.wflow");
  await expect(name).toHaveValue("Engineering authoring check");
  await f.getByTestId("workflow-recovery-view-code").click();
  await expect(f.getByTestId("workflow-recovery-source-editor")).toHaveValue(
    /name: "Engineering authoring check"/,
  );
  const original = await call("wright_workflow_read", {
    workspace_id: disposable.workspace_id,
    session_id: disposable.session_id,
    path: "workflows/installed-check.workflow.wflow",
  });
  const imported = await call("wright_workflow_read", {
    workspace_id: disposable.workspace_id,
    session_id: disposable.session_id,
    path: "workflows/imported-authoring-check.workflow.wflow",
  });
  expect(imported.source).toBe(original.source);
  await page.screenshot({ path: resolve(output, "authoring-imported.png") });
  expect(errors).toEqual([]);
  checks.push(
    "Separate disposable workspace: rename, Undo/Redo, save, title search, reopen, browser download of portable definition, inspect/import and reopened source. No Windows file-delivery claim.",
  );
  status = "PASS";
} finally {
  if (status !== "PASS")
    await page.screenshot({ path: resolve(output, "failure.png") });
  writeFileSync(
    resolve(output, "receipt.json"),
    JSON.stringify(
      {
        status,
        host: "Linux Chromium simulated desktop",
        resource: uri,
        checks,
        errors,
        calls,
        engineering_runs: 0,
      },
      null,
      2,
    ),
  );
  await browser.close();
  await mcp.close();
  server.close();
}

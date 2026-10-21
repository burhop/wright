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
  command: process.env.WRIGHT_PROBE_PYTHON ?? resolve(".venv/bin/python"),
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
const fixture = `<!doctype html><html><meta charset="utf-8"><body style="margin:0;background:#181818;color:#ddd;font:12px system-ui"><div style="height:28px;padding:0 12px;display:flex;align-items:center">Wright prototype · simulated desktop host · actual saved workflow${input.run_id ? " and recorded results · read only" : " · isolated source copy · no engineering run"}</div><iframe id="panel" title="Wright" style="border:0;width:100%;height:calc(100vh - 28px)"></iframe><script>
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
const allowed = new Set([
  "wright_workspace_list",
  "wright_workspace_files",
  "wright_workflow_read",
  "wright_workflow_open",
  "wright_editor_drafts_read",
  "wright_workflow_history",
  "wright_process_view",
  "wright_process_ui_read",
  "wright_recorded_run_read",
  "wright_workspace_file_preview",
  "wright_workspace_file_download",
]);
const server = createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/") {
      res.writeHead(200, { "Content-Type": "text/html;charset=utf-8" });
      res.end(fixture);
      return;
    }
    if (req.method !== "POST" || req.url !== "/tool")
      throw Error("Qualification route denied");
    let body = "";
    for await (const chunk of req) body += chunk;
    const { name, arguments: args } = JSON.parse(body);
    const request = args.request ?? args;
    if (
      !allowed.has(name) &&
      !(
        input.edit_copy &&
        ["wright_workflow_save", "wright_editor_draft_save"].includes(name)
      )
    )
      throw Error(`Operation denied: ${name}`);
    if (
      name !== "wright_workspace_list" &&
      (request.workspace_id !== scope.workspace_id ||
        request.session_id !== scope.session_id)
    )
      throw Error("Qualification workspace/session differs");
    if (
      name !== "wright_workspace_list" &&
      name !== "wright_workspace_files" &&
      !name.startsWith("wright_workspace_file_") &&
      request.path !== scope.path
    )
      throw Error("Qualification source differs");
    if (name.startsWith("wright_process_")) {
      if (
        !["snapshot", "navigation", "representation", "reasoning"].includes(
          request.operation,
        )
      )
        throw Error("Only process reads are qualified");
      if (request.run_id && request.run_id !== input.run_id)
        throw Error("Qualification run differs");
    }
    if (name === "wright_recorded_run_read" && request.run_id !== input.run_id)
      throw Error("Qualification saved run differs");
    const result = await mcp.callTool({ name, arguments: args });
    calls.push({ name, arguments: args, is_error: !!result.isError });
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(result));
  } catch (error) {
    errors.push(String(error));
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        isError: true,
        content: [
          {
            type: "text",
            text: "Qualification did not forward the operation.",
          },
        ],
      }),
    );
  }
});
await new Promise((done) => server.listen(0, "127.0.0.1", done));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1080, height: 900 } });
page.on("pageerror", (error) => errors.push(error.message));
const frame = page.frameLocator("#panel");
try {
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await frame
    .getByRole("button", { name: scope.path.split("/").at(-1), exact: true })
    .click();
  await expect(frame.getByTestId("workflow-recovery-save")).toBeVisible();
  await frame.getByTestId("workflow-recovery-view-code").click();
  const editor = frame.getByTestId("workflow-recovery-source-editor");
  await expect(editor).toHaveValue(before.source);
  checks.push("Workflows entry opens exact accepted source in shared editor");
  let accepted = before;
  if (input.edit_copy) {
    const title = /^  name: "([^"]+)"/m.exec(before.source)?.[1];
    if (!title) throw Error("Expected a named disposable example");
    const revised = before.source.replace(
      /^  name: "[^"]+"/m,
      `  name: ${JSON.stringify(title + " · navigation check")}`,
    );
    await editor.fill(revised);
    await frame.getByTestId("workflow-recovery-source-apply").click();
    await frame
      .getByRole("button", { name: "Workspaces", exact: true })
      .click();
    await expect(frame.locator("#notice")).toHaveText(/draft is kept/);
    await expect(frame.getByTestId("workflow-recovery-save")).toBeEnabled();
    await frame.getByTestId("workflow-recovery-save").click();
    await expect(frame.getByTestId("workflow-recovery-save-status")).toHaveText(
      "Saved",
    );
    await expect(frame.locator("#notice")).toBeEmpty();
    accepted = await read("wright_workflow_read", scope);
    expect(accepted.source).toContain(title + " · navigation check");
    expect(accepted.storage_revision).toBeGreaterThan(before.storage_revision);
    checks.push(
      "Dirty draft guards Home; explicit save records source/layout through actual MCP and owning service",
    );
  }
  await frame.getByTestId("workflow-recovery-view-diagram").click();
  await page.screenshot({ path: resolve(output, "workflow.png") });
  await frame
    .getByRole("button", { name: "Run and results", exact: true })
    .click();
  await expect(frame.getByTestId("common-process-view")).toBeVisible();
  await frame.getByRole("button", { name: "Run history", exact: true }).click();
  await expect
    .poll(
      () => calls.filter((c) => c.name === "wright_workflow_history").length,
    )
    .toBeGreaterThan(0);
  if (input.run_id) {
    const row = frame.getByRole("listitem").filter({ hasText: input.run_id });
    await row
      .getByRole("button", { name: "Read saved evidence", exact: true })
      .click();
    await expect(
      frame.getByRole("region", { name: "Saved run evidence" }),
    ).toContainText("Recorded state:");
    await page.screenshot({ path: resolve(output, "saved-results.png") });
    await row
      .getByRole("button", { name: "Open working view", exact: true })
      .click();
    await expect(frame.getByTestId("common-process-view")).toBeVisible();
    await expect
      .poll(() =>
        page.evaluate(
          () => window.lastContext?.structuredContent?.workflow?.run_id,
        ),
      )
      .toBe(input.run_id);
    await page.screenshot({ path: resolve(output, "run-results.png") });
    if (input.preview_filename) {
      const result = frame
        .locator(".wp-result")
        .filter({ hasText: input.preview_filename });
      await result
        .getByRole("button", { name: "Open file", exact: true })
        .click();
      const bitmap = frame.getByRole("img", {
        name: input.preview_filename,
        exact: true,
      });
      await expect(bitmap).toBeVisible();
      await expect
        .poll(() => bitmap.evaluate((element) => element.naturalWidth))
        .toBeGreaterThan(0);
      const displayedHash = await bitmap.evaluate(async (element) => {
        const bytes = await (await fetch(element.src)).arrayBuffer();
        return Array.from(
          new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
        )
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");
      });
      expect(displayedHash).toBe(input.preview_sha256);
      await page.screenshot({ path: resolve(output, "recorded-image.png") });
      await frame
        .getByRole("button", { name: "Close file", exact: true })
        .click();
      await result
        .getByRole("button", { name: "Open producing step", exact: true })
        .click();
      await expect(
        frame.getByTestId("workflow-recovery-inspector"),
      ).toBeVisible();
      await expect(frame.getByTestId("workflow-recovery-save")).toBeVisible();
      await page.screenshot({ path: resolve(output, "producing-step.png") });
      await frame
        .getByRole("button", { name: "Run and results", exact: true })
        .click();
      await expect(frame.getByTestId("common-process-view")).toBeVisible();
      checks.push(
        "Actual retained PNG displayed with matching byte hash; result links to producing-step inspector and back to the same run",
      );
    }
    checks.push(
      "Selected workflow history reads recorded evidence and attaches only the exact runtime-confirmed run",
    );
  } else {
    await expect(
      frame.getByText("No recorded runs for this workflow."),
    ).toBeVisible();
    await frame
      .getByRole("button", { name: "Back to current view", exact: true })
      .click();
    checks.push(
      "Selected workflow history reports actual empty state without selecting another workflow",
    );
  }
  await frame
    .getByRole("button", { name: "Open workflow", exact: true })
    .click();
  await frame.getByTestId("workflow-recovery-view-code").click();
  await expect(editor).toHaveValue(accepted.source);
  await frame.getByRole("button", { name: "Workspaces", exact: true }).click();
  const reopen = frame.getByRole("button", { name: /^Reopen / });
  await expect(reopen).toHaveCount(1);
  await page.locator("#panel").evaluate((element) => {
    element.srcdoc = element.srcdoc;
  });
  await expect(reopen).toHaveCount(1);
  await reopen.click();
  await frame.getByTestId("workflow-recovery-view-code").click();
  await expect(editor).toHaveValue(accepted.source);
  if (input.run_id)
    await expect
      .poll(() =>
        page.evaluate(
          () => window.lastContext?.structuredContent?.workflow?.run_id,
        ),
      )
      .toBe(input.run_id);
  checks.push(
    "Home and supported widget remount retain exact source/run target; explicit reopen rereads owner without replay",
  );
  await frame.getByTestId("workflow-recovery-view-diagram").click();
  await page.setViewportSize({ width: 480, height: 820 });
  await page.screenshot({ path: resolve(output, "workflow-narrow.png") });
  await frame.getByRole("button", { name: "Workspaces", exact: true }).click();
  await expect(frame.getByLabel("Workspace", { exact: true })).toHaveValue(
    scope.workspace_id,
  );
  await expect(
    frame.getByRole("button", {
      name: scope.path.split("/").at(-1),
      exact: true,
    }),
  ).toBeVisible();
  await expect(frame.getByText("Loading...", { exact: true })).toHaveCount(0);
  await expect(reopen).toBeVisible();
  await page.screenshot({ path: resolve(output, "home-narrow.png") });
  const overflow = await frame
    .locator("body")
    .evaluate((el) => el.scrollWidth > el.clientWidth + 1);
  expect(overflow).toBe(false);
  const after = await read("wright_workflow_read", scope);
  expect(after.storage_digest).toBe(accepted.storage_digest);
  const historyAfter = await read("wright_workflow_history", scope);
  expect(historyAfter).toEqual(historyBefore);
  expect(calls.some((c) => c.name === "wright_process_ui_update")).toBe(false);
  expect(errors).toEqual([]);
  checks.push(
    "Narrow Home fits; recorded history unchanged; zero process mutations or engineering calls",
  );
  writeFileSync(
    resolve(output, "report.json"),
    JSON.stringify(
      {
        status: "passed",
        boundary:
          "Real Wright MCP/storage; simulated desktop host, not Windows acceptance",
        scope,
        run_id: input.run_id ?? null,
        bridge,
        bridge_sha256: createHash("sha256")
          .update(readFileSync(bridge))
          .digest("hex"),
        bundle_sha256: createHash("sha256")
          .update(originalBundle)
          .digest("hex"),
        before_digest: before.storage_digest,
        after_digest: after.storage_digest,
        checks,
        calls,
        errors,
      },
      null,
      2,
    ),
  );
  console.log(output);
} catch (error) {
  await page.screenshot({ path: resolve(output, "failure.png") });
  writeFileSync(
    resolve(output, "failure.json"),
    JSON.stringify(
      {
        error: String(error),
        checks,
        calls,
        errors,
        dom: await frame.locator("body").innerText(),
      },
      null,
      2,
    ),
  );
  console.log(output);
  throw error;
} finally {
  await browser.close();
  await new Promise((done) => server.close(done));
  await mcp.close();
}

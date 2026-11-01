// Read-only native-file simulation using the built UI and actual Wright owners.
// Does not automate or establish acceptance in the OpenAI desktop application.
// Usage: node SCRIPT CLIENT_STATE PROBE_MANIFEST HTML OUTPUT [baseline]
import { createServer } from "node:http";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve, basename } from "node:path";
import { createHash } from "node:crypto";
import { chromium, expect } from "@playwright/test";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { CallToolResultSchema } from "@modelcontextprotocol/sdk/types.js";

const [state, manifestPath, htmlPath, outputPath, mode] = process.argv.slice(2);
const output = resolve(outputPath);
mkdirSync(output); // Preserve every previous attempt.
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const file = manifest.files.find((item) => item.kind === "workflow");
const html = readFileSync(htmlPath, "utf8");
const hash = (value) => createHash("sha256").update(value).digest("hex");
const sourceBefore = readFileSync(file.absolute_path);
const scope = {
  workspace_id: file.workspace_id,
  session_id: file.session_id,
  path: file.path,
};
const mcp = new Client({
  name: "wright-toolbar-qualification",
  version: "0.1.0",
});
const transport = new StdioClientTransport({
  command: process.env.WRIGHT_PROBE_PYTHON ?? ".venv/bin/python",
  args: [
    resolve(
      process.env.WRIGHT_PROBE_BRIDGE ??
        "prototypes/desktop-harness/mcp_bridge.py",
    ),
    "--state-dir",
    resolve(state),
    "--native-editor",
    "--native-working-view",
    ...(manifest.native_workspace_files
      ? ["--native-workspace-files"]
      : ["--native-file-tab-probe", resolve(manifestPath)]),
  ],
  stderr: "pipe",
});
transport.stderr?.on("data", () => {}); // Never emit private configuration.
await mcp.connect(transport);
const read = async (name, args) => {
  const result = await mcp.callTool({ name, arguments: args });
  if (result.isError) throw Error(`Owner rejected ${name}`);
  return result.structuredContent ?? JSON.parse(result.content[0].text);
};
const accepted = await read("wright_workflow_read", scope);
const history = await read("wright_workflow_history", scope);
const drafts = await read("wright_editor_drafts_read", { request: scope });
const calls = [],
  errors = [],
  measurements = [];
const safe = (value) => JSON.stringify(value).replaceAll("<", "\\u003c");
const fixture = `<!doctype html><html><meta charset="utf-8"><body style="margin:0;background:#181818;color:#ddd;font:12px system-ui"><div style="height:28px">SIMULATED desktop file host · actual Wright UI/owners · read only</div><iframe id="panel" title="Wright" style="border:0;width:100%;height:calc(100vh - 28px)"></iframe><script>
const frame=document.querySelector('#panel');
window.addEventListener('message',async e=>{
 if(e.source!==frame.contentWindow)return;
 const m=e.data,send=data=>frame.contentWindow.postMessage({jsonrpc:'2.0',...data},'*');
 if(m.method==='ui/initialize')send({id:m.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'toolbar-simulation',version:'1'},hostCapabilities:{serverTools:{},updateModelContext:{},experimental:{'openai/resource':{},'openai/files':{}}},hostContext:{theme:'dark',platform:'desktop'}}});
 if(m.method==='ui/notifications/initialized')send({method:'ui/notifications/tool-input',params:{arguments:{file:{name:${safe(basename(file.path))},resourceUri:'opaque://toolbar-test'}}}});
 if(m.method==='ui/update-model-context')send({id:m.id,result:{}});
 if(m.method==='tools/call'){const response=await fetch('/tool',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(m.params)});send({id:m.id,result:await response.json()});}
});frame.srcdoc=${safe(html)};</script></body></html>`;
const allowed = new Set([
  "wright_workflow_file_context",
  "wright_workflow_read",
  "wright_workflow_open",
  "wright_editor_drafts_read",
  "wright_workflow_history",
]);
const server = createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/") {
      res.writeHead(200, { "Content-Type": "text/html;charset=utf-8" });
      res.end(fixture);
      return;
    }
    if (req.method !== "POST" || req.url !== "/tool")
      throw Error("Unknown route");
    let body = "";
    for await (const chunk of req) body += chunk;
    const { name, arguments: args } = JSON.parse(body);
    const request = args.request ?? args;
    if (!allowed.has(name))
      throw Error(`Read-only qualification forbids ${name}`);
    if (
      name !== "wright_workflow_file_context" &&
      (request.workspace_id !== scope.workspace_id ||
        request.session_id !== scope.session_id ||
        request.path !== scope.path)
    )
      throw Error("Foreign document scope");
    const result = await mcp.request(
      {
        method: "tools/call",
        params: {
          name,
          arguments: args,
          _meta: { "openai/resource": { path: file.absolute_path } },
        },
      },
      CallToolResultSchema,
    );
    calls.push({ name, is_error: !!result.isError });
    if (result.isError) throw Error(`Owner rejected ${name}`);
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(result));
  } catch (error) {
    errors.push(String(error));
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        isError: true,
        content: [
          { type: "text", text: "Read-only qualification denied operation" },
        ],
      }),
    );
  }
});
await new Promise((done) => server.listen(0, "127.0.0.1", done));
const browser = await chromium.launch({ headless: true });
let status = "FAIL",
  failure;
try {
  for (const size of [
    { width: 1100, height: 900, scale: 1 },
    { width: 480, height: 820, scale: 1 },
    { width: 800, height: 700, scale: 1.5 },
  ]) {
    const context = await browser.newContext({
      viewport: { width: size.width, height: size.height },
      deviceScaleFactor: size.scale,
    });
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    const frame = page.frameLocator("#panel");
    await expect(frame.getByTestId("workflow-recovery-save")).toBeVisible();
    await expect(frame.locator(".react-flow__node").first()).toBeVisible();
    const bounds = await frame.locator(".recovery-workbench").evaluate((el) => {
      const r = el.getBoundingClientRect();
      return {
        top: r.top,
        height: r.height,
        width: r.width,
        viewport_height: innerHeight,
        horizontal_overflow: document.documentElement.scrollWidth > innerWidth,
      };
    });
    measurements.push({
      viewport_width: size.width,
      viewport_outer_height: size.height,
      device_scale_factor: size.scale,
      ...bounds,
    });
    await page.screenshot({
      path: resolve(output, `diagram-${size.width}-${size.scale}.png`),
    });
    if (mode !== "baseline") {
      await expect(frame.locator(".react-flow__node").first()).toBeInViewport({
        ratio: 0.25,
      });
      expect(bounds.top).toBeLessThanOrEqual(170);
      expect(bounds.height / bounds.viewport_height).toBeGreaterThan(0.7);
      expect(bounds.horizontal_overflow).toBe(false);
      await expect(
        frame.getByText("Native file tab test", { exact: false }),
      ).toHaveCount(0);
      await expect(
        frame.getByRole("button", { name: /^(Run workflow|View run|Run and results)$/, exact: true }),
      ).toBeVisible();
      await frame.locator(".native-workflow-details > summary").click();
      await expect(
        frame.locator(".native-workflow-details__content"),
      ).toBeInViewport();
      await expect(
        frame.locator(".native-workflow-details__content"),
      ).toContainText(scope.path);
      await expect(
        frame.getByRole("button", {
          name: "Export / import workflow",
          exact: true,
        }),
      ).toBeVisible();
      await expect(
        frame.locator(".native-editor-drafts > summary"),
      ).toBeVisible();
      await page.screenshot({
        path: resolve(output, `details-${size.width}-${size.scale}.png`),
      });
      await frame.locator(".native-workflow-details > summary").press("Escape");
      await expect(
        frame.locator(".native-workflow-details"),
      ).not.toHaveAttribute("open");
      await expect(
        frame.locator(".native-workflow-details > summary"),
      ).toBeFocused();
      if (mode === "instructions") {
        await frame.getByTestId("workflow-recovery-instructions").click();
        await expect(frame.getByRole("dialog", { name: "Workflow instructions" })).toBeVisible();
        await expect(frame.getByText(/Choose how AI handles missing design choices/)).toBeInViewport();
        await expect(frame.getByTestId("workflow-instructions-action-intent")).not.toBeVisible();
        await page.screenshot({ path: resolve(output, `instructions-${size.width}-${size.scale}.png`) });
        await frame.getByText("Instruction version and compatibility", { exact: true }).click();
        await expect(frame.getByTestId("workflow-instructions-action-intent")).toBeVisible();
        await frame.getByTestId("workflow-recovery-modal-close").click();
        await expect(frame.getByTestId("workflow-recovery-save")).toBeDisabled();
      }
    }
    const select = frame.getByTestId("workflow-recovery-view-select");
    if (await select.isVisible()) await select.selectOption("code");
    else await frame.getByTestId("workflow-recovery-view-code").click();
    await expect(
      frame.getByTestId("workflow-recovery-source-editor"),
    ).toHaveValue(accepted.source);
    if (await select.isVisible()) await select.selectOption("diagram");
    else await frame.getByTestId("workflow-recovery-view-diagram").click();
    await frame
      .getByRole("button", { name: "Report UI problem", exact: true })
      .click();
    await expect(
      frame.getByRole("textbox", { name: "Problem description" }),
    ).toBeInViewport();
    await expect(
      frame.getByRole("textbox", { name: "Problem description" }),
    ).toBeFocused();
    await frame.getByRole("button", { name: "Close report" }).click();
    await context.close();
  }
  expect(await read("wright_workflow_read", scope)).toEqual(accepted);
  expect(await read("wright_workflow_history", scope)).toEqual(history);
  expect(await read("wright_editor_drafts_read", { request: scope })).toEqual(
    drafts,
  );
  expect(readFileSync(file.absolute_path)).toEqual(sourceBefore);
  expect(errors).toEqual([]);
  status = "PASS";
} catch (error) {
  failure = String(error.stack ?? error);
} finally {
  writeFileSync(
    resolve(output, "report.json"),
    JSON.stringify(
      {
        status,
        boundary:
          "Simulated desktop file host; actual Wright owners. No actual native renderer acceptance.",
        html_sha256: hash(html),
        measurements,
        calls,
        errors,
        failure,
      },
      null,
      2,
    ) + "\n",
  );
  await browser.close();
  await new Promise((done) => server.close(done));
  await mcp.close();
}
console.log(JSON.stringify({ status, measurements, errors, failure, output }));
if (status !== "PASS") process.exitCode = 1;

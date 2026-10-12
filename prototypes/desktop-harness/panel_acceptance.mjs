// Browser protocol fixture only; it does not establish native desktop UI support.
import { createServer } from "node:http";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { chromium, expect } from "@playwright/test";

const folder = resolve("prototypes/desktop-harness/ui-concepts/2026-10-12");
const panel = readFileSync(resolve(folder, "panel.html"), "utf8");
const evidence = JSON.parse(readFileSync(resolve(folder, "panel-protocol-evidence.json"), "utf8"));
const scope = { workspace_id: evidence.workspace.workspace_id, session_id: evidence.workspace.session_id };
const safeJson = value => JSON.stringify(value).replaceAll("<", "\\u003c");
const html = `<!doctype html><html><head><meta charset="utf-8"><title>Wright panel protocol fixture</title></head>
<body style="margin:0;background:#181818;color:#eee;font:13px system-ui">
<p style="padding:12px;margin:0">GB10 browser protocol fixture · recorded MCP result · native desktop rendering unverified</p>
<iframe id="panel" title="Wright Workflows" style="border:0;width:100%;height:570px"></iframe>
<script>
const frame=document.getElementById('panel');window.calls=[];
const result=${safeJson(evidence.result)}, scope=${safeJson(scope)};
window.addEventListener('message',event=>{
 if(event.source!==frame.contentWindow)return;
 const message=event.data;
 if(message.method==='ui/initialize')frame.contentWindow.postMessage({jsonrpc:'2.0',id:message.id,result:{hostContext:{theme:'dark'}}},'*');
 if(message.method==='ui/notifications/initialized'){
  frame.contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-input',params:{arguments:scope}},'*');
  frame.contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:{structuredContent:result}},'*');
 }
 if(message.method==='tools/call'){
  window.calls.push(message.params);
  frame.contentWindow.postMessage({jsonrpc:'2.0',id:message.id,result:{structuredContent:result}},'*');
 }
});
frame.srcdoc=${safeJson(panel)};
</script></body></html>`;
const server = createServer((_request, response) => {
  response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
  response.end(html);
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const browser = await chromium.launch({ headless: true });
const output = resolve(folder, "panel-browser-evidence");
mkdirSync(output, { recursive: true });
try {
  const page = await browser.newPage({ viewport: { width: 1000, height: 640 } });
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  const frame = page.frameLocator("#panel");
  await expect(frame.getByRole("heading", { name: evidence.workspace.workspace_name })).toBeVisible();
  await expect(frame.locator("#state")).toHaveText("Connected");
  await expect(frame.locator("#model")).toContainText("unreported");
  await frame.getByRole("button", { name: "Refresh status" }).click();
  await expect.poll(() => page.evaluate(() => calls.length)).toBe(1);
  expect(await page.evaluate(() => calls[0])).toEqual({ name: "wright_workspace_panel", arguments: scope });
  await page.screenshot({ path: resolve(output, "dark.png") });
  await page.evaluate(() => document.getElementById("panel").contentWindow.postMessage({ jsonrpc: "2.0", method: "ui/notifications/host-context-changed", params: { theme: "light", styles: { variables: { "--color-background-primary": "#ffffff", "--color-text-primary": "#242424", "--color-text-secondary": "#595959", "--color-border-primary": "#cccccc" } } } }, "*"));
  await expect.poll(() => frame.locator("body").evaluate(el => getComputedStyle(el).backgroundColor)).toBe("rgb(255, 255, 255)");
  await page.setViewportSize({ width: 340, height: 640 });
  expect(await frame.locator("body").evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  await page.screenshot({ path: resolve(output, "light-narrow.png") });
  await page.evaluate(() => document.getElementById("panel").contentWindow.dispatchEvent(new MessageEvent("message", { source: null, data: { jsonrpc: "2.0", method: "ui/notifications/tool-result", params: { structuredContent: { connection: { connected: true }, workspace: { workspace_name: "Wrong frame" } } } } })));
  await expect(frame.locator("#workspace")).toHaveText(evidence.workspace.workspace_name);
  await page.evaluate(() => document.getElementById("panel").contentWindow.postMessage({ jsonrpc: "2.0", method: "ui/notifications/tool-result", params: { isError: true } }, "*"));
  await expect(frame.locator("#notice")).toContainText("no action was repeated");
  writeFileSync(resolve(output, "report.json"), JSON.stringify({ boundary: "GB10 browser with simulated MCP App host; real recorded Wright result", passed: ["initial result", "scoped refresh once", "theme notification", "narrow layout", "untrusted frame rejected", "error remains read-only"], native_desktop_verified: false }, null, 2));
  console.log("Six panel browser checks passed; native desktop rendering remains unverified.");
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}

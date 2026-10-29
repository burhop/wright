// Compiled native-panel readiness navigation with labeled fixture state.
// Usage: node prototypes/desktop-harness/native_readiness_acceptance.mjs OUTPUT
// No source mutation, model call, engineering operation or Windows acceptance.
import { createServer } from "node:http";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { createHash } from "node:crypto";
import {
  chromium,
  expect,
} from "../../node_modules/@playwright/test/index.mjs";
const output = process.argv[2];
if (!output) throw Error("Supply a fresh evidence directory");
mkdirSync(output, { recursive: false });
const html = readFileSync(
  "prototypes/desktop-harness/native-editor.html",
  "utf8",
);
const source = readFileSync(
  "prototypes/desktop-harness/engineering-experience/handle/replacement-handle-draft.workflow.wflow",
  "utf8",
);
const digest = createHash("sha256").update(source).digest("hex");
const scope = {
  workspace_id: "study-workspace",
  session_id: "study-session",
  path: "workflows/handle.wflow",
};
const processRef = {
  workspace_id: scope.workspace_id,
  source_path: scope.path,
  source_digest: digest,
};
const workspace = {
  ...scope,
  workspace_name: "Replacement handle · fixture",
  available: true,
  reason: null,
};
const document = {
  workspace_id: scope.workspace_id,
  path: scope.path,
  source,
  storage_digest: digest,
  storage_revision: 1,
  definition_revision: 1,
  metadata_authority: "wright_host",
  size_bytes: Buffer.byteLength(source),
};
const reason = {
  code: "READINESS_UNSUPPORTED",
  message: "Create the editable handle and exports needs an engineering tool.",
  correction: "Choose a tool in this step’s settings before starting.",
  navigation: { kind: "block", block_id: "cad" },
};
const calls = [];
const respond = (name, args) => {
  calls.push({ name, args });
  if (name === "wright_workflow_read") return document;
  if (name === "wright_editor_drafts_read") return { ...scope, drafts: [] };
  if (name === "wright_process_ui_read") {
    const r = args.request;
    if (r.operation === "snapshot")
      return { ok: false, http_status: 422, reason };
    if (r.operation === "navigation")
      return { ok: true, document: { process: processRef, target: r.target } };
  }
  throw Error("Unexpected tool: " + name);
};

const safe = (x) => JSON.stringify(x).replaceAll("<", "\\u003c");
const fixture = `<!doctype html><html><body style="margin:0;background:#181818;color:white;font:13px system-ui"><div style="height:28px">Compiled Wright UI · simulated host and data · no engineering work</div><iframe title="Wright" id="panel" sandbox="allow-scripts allow-same-origin" style="width:100%;height:calc(100vh - 28px);border:0"></iframe><script>const f=document.querySelector('#panel');window.addEventListener('message',async e=>{if(e.source!==f.contentWindow)return;const m=e.data;const send=d=>f.contentWindow.postMessage({jsonrpc:'2.0',...d},'*');if(m.method==='ui/initialize')send({id:m.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'navigation-study',version:'1'},hostCapabilities:{serverTools:{},updateModelContext:{},experimental:{'openai/files':{},'openai/resource':{}}},hostContext:{theme:'dark'}}});else if(m.method==='ui/notifications/initialized'){send({method:'ui/notifications/tool-input',params:{arguments:${safe(scope)}}});send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:{workspace:${safe(workspace)},working_view_enabled:true}}});}else if(m.method==='tools/call'){const r=await fetch('/tool',{method:'POST',body:JSON.stringify(m.params)});send({id:m.id,result:await r.json()});}else if(m.id)send({id:m.id,result:{}});});f.srcdoc=${safe(html)};</script></body></html>`;
const server = createServer(async (req, res) => {
  if (req.method === "GET") {
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.end(fixture);
    return;
  }
  let body = "";
  for await (const c of req) body += c;
  try {
    const { name, arguments: args } = JSON.parse(body);
    res.end(
      JSON.stringify({ content: [], structuredContent: respond(name, args) }),
    );
  } catch (e) {
    res.end(
      JSON.stringify({
        isError: true,
        content: [{ type: "text", text: String(e) }],
      }),
    );
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
try {
  await page.goto("http://127.0.0.1:" + server.address().port);
  const f = page.frameLocator("#panel");
  await expect(f.getByTestId("workflow-recovery-save")).toBeVisible();
  await f.getByRole("button", { name: "Run workflow", exact: true }).click();
  await expect(f.getByText(reason.message, { exact: true })).toBeVisible();
  await expect(
    f.getByRole("button", { name: "Open affected step", exact: true }),
  ).toBeInViewport();
  await page.screenshot({ path: output + "/blocked.png" });
  await f
    .getByRole("button", { name: "Open affected step", exact: true })
    .click();
  await expect(f.getByTestId("workflow-recovery-inspector")).toContainText(
    "Create the editable handle and exports",
  );
  await expect(f.getByTestId("workflow-recovery-inspector")).toBeInViewport();
  await page.screenshot({ path: output + "/affected-step.png" });
  const nav = calls.find(
    (c) =>
      c.name === "wright_process_ui_read" &&
      c.args.request.operation === "navigation",
  );
  expect(nav.args.request).toMatchObject({
    ...scope,
    expected_storage_digest: digest,
    target: { kind: "block", block_id: "cad" },
  });
  await f.getByRole("button", { name: "Run workflow", exact: true }).click();
  await expect(f.getByText(reason.message, { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 480, height: 900 });
  await expect(
    f.getByRole("button", { name: "Open affected step", exact: true }),
  ).toBeInViewport();
  await page.screenshot({ path: output + "/return-narrow.png" });
  expect(
    calls.every((c) =>
      [
        "wright_workflow_read",
        "wright_editor_drafts_read",
        "wright_process_ui_read",
      ].includes(c.name),
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
  writeFileSync(
    output + "/report.json",
    JSON.stringify(
      {
        status: "PASS",
        boundary:
          "compiled native UI; simulated host and blocked fixture; no source save, engineering tools or Windows acceptance",
        resource_sha256: createHash("sha256").update(html).digest("hex"),
        calls,
        errors,
      },
      null,
      2,
    ),
  );
} catch (error) {
  await page.screenshot({ path: output + "/failure.png" });
  writeFileSync(
    output + "/failure.txt",
    String(error) +
      "\n" +
      (await page.frameLocator("#panel").locator("body").innerText()),
  );
  throw error;
} finally {
  await browser.close();
  server.close();
}

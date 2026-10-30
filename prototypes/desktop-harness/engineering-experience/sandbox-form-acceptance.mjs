// Same public SDK iframe handshake as native_home_acceptance.mjs; fixture data only.
import { createServer } from "node:http";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { chromium, expect } from "@playwright/test";
const [resource, output] = process.argv.slice(2);
if (!resource || !output)
  throw Error("Supply compiled native HTML and a fresh output directory");
mkdirSync(output);
const html = readFileSync(resource, "utf8");
const scope = { workspace_id: "study-workspace", session_id: "study-session" };
const workspace = {
  ...scope,
  workspace_name: "Replacement handle",
  available: true,
  reason: null,
};
const connection = {
  capability_id: "cad",
  server_id: "cad",
  name: "Study CAD",
  description: "Fixture CAD provider.",
  installed: true,
  active: true,
  enabled_here: true,
  credentials_missing: false,
  process_status: "active",
  installed_version: null,
  compatibility: { status: "uncertain", reasons: [] },
  local_validation: {
    state: "stale",
    evidence_id: "fixture-check",
    observed_at: "2026-10-01",
    reason_codes: [],
  },
};
const calls = [];
let saved;
const respond = (name, args) => {
  calls.push(name);
  if (name === "wright_workspace_create") {
    workspace.workspace_name = args.name;
    return scope;
  }
  if (name === "wright_workflow_create") {
    saved = {
      ...scope,
      path: args.path,
      source: args.source,
      storage_digest: createHash("sha256").update(args.source).digest("hex"),
      storage_revision: 1,
      definition_revision: 1,
      size_bytes: Buffer.byteLength(args.source),
      metadata_authority: "wright_host",
    };
    return saved;
  }
  if (name === "wright_workflow_read") return saved;
  if (name === "wright_editor_drafts_read") return { ...scope, drafts: [] };
  if (name === "wright_workspace_list") return { workspaces: [workspace] };
  if (name === "wright_workspace_files")
    return {
      ...scope,
      tree: {
        type: "directory",
        children: [
          {
            type: "file",
            name: "Handle reference.png",
            path: "/uploads/reference.png",
          },
        ],
      },
    };
  if (name === "wright_connections_list")
    return {
      ...scope,
      next_cursor: null,
      connections: [
        connection,
        ...Array.from({ length: 35 }, (_, i) => ({
          ...connection,
          capability_id: "catalog-" + i,
          server_id: "catalog-" + i,
          name: "Catalog tool " + i,
          installed: false,
          enabled_here: false,
        })),
      ],
    };
  throw Error("Unexpected tool: " + name);
};
const safe = (x) => JSON.stringify(x).replaceAll("<", "\\u003c");
const fixture = `<!doctype html><html><body style="margin:0;background:#181818;color:white;font:13px system-ui"><div style="height:28px">Compiled Wright UI · simulated host and data · no engineering work</div><iframe title="Wright" id="panel" sandbox="allow-scripts allow-same-origin" style="width:100%;height:calc(100vh - 28px);border:0"></iframe><script>const f=document.querySelector('#panel');window.addEventListener('message',async e=>{if(e.source!==f.contentWindow)return;const m=e.data;const send=d=>f.contentWindow.postMessage({jsonrpc:'2.0',...d},'*');if(m.method==='ui/initialize')send({id:m.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'navigation-study',version:'1'},hostCapabilities:{serverTools:{},updateModelContext:{},experimental:{'openai/files':{},'openai/resource':{}}},hostContext:{theme:'dark'}}});else if(m.method==='ui/notifications/initialized'){send({method:'ui/notifications/tool-input',params:{arguments:{}}});send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:{view:'home',native_workspace_files_enabled:true}}});}else if(m.method==='tools/call'){const r=await fetch('/tool',{method:'POST',body:JSON.stringify(m.params)});send({id:m.id,result:await r.json()});}else if(m.id)send({id:m.id,result:{}});});f.srcdoc=${safe(html)};</script></body></html>`;
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
    console.error("Fixture request failed", e);
    res.setHeader("Content-Type", "application/json");
    res.end(
      JSON.stringify({
        isError: true,
        content: [{ type: "text", text: "Fixture request failed; inspect the local test log." }],
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
  await f.getByRole("button", { name: "New workspace", exact: true }).click();
  await f
    .getByLabel("Workspace name", { exact: true })
    .fill("Sandbox creation");
  await f
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await expect
    .poll(() => calls.filter((n) => n === "wright_workspace_create").length)
    .toBe(1);
  await expect(
    f.getByRole("heading", { name: "Sandbox creation", exact: true }),
  ).toBeVisible();
  await f.getByRole("button", { name: "New workflow", exact: true }).click();
  await f.getByText("Start with a blank workflow", { exact: true }).click();
  await f.getByLabel("Workflow name", { exact: true }).fill("Sandbox handle");
  await f.getByLabel("Workflow name", { exact: true }).press("Enter");
  await expect
    .poll(() => calls.filter((n) => n === "wright_workflow_create").length)
    .toBe(1);
  await expect(
    f.getByText(
      "Your workflow was saved. Opening the editor failed; try Open saved workflow.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    f.getByRole("button", { name: "Open saved workflow", exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: output + "/after-creation.png" });
  expect(saved.source).toContain("Sandbox handle");
  expect(
    calls.filter((n) => /process_(start|respond)|reasoning_action/.test(n)),
  ).toEqual([]);
  writeFileSync(
    output + "/report.json",
    JSON.stringify(
      {
        status: "PASS",
        boundary:
          "actual compiled UI; fixture writes; restrictive simulated host, not Windows acceptance",
        resource_sha256: createHash("sha256").update(html).digest("hex"),
        calls,
        errors,
        editor_open:
          "fixture deliberately rejects file describe; visible recovery verified",
        workspace_click_count: calls.filter(
          (n) => n === "wright_workspace_create",
        ).length,
        workflow_enter_count: calls.filter(
          (n) => n === "wright_workflow_create",
        ).length,
      },
      null,
      2,
    ),
  );
  console.log(JSON.stringify({ calls, errors }));
} finally {
  await browser.close();
  server.close();
}

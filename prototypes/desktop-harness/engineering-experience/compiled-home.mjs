// Same public SDK iframe handshake as native_home_acceptance.mjs; fixture data only.
import { createServer } from "node:http";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { chromium, expect } from "@playwright/test";
const output = process.argv[2];
if (!output) throw Error("Supply a fresh evidence directory");
mkdirSync(output);
const html = readFileSync(
  "prototypes/desktop-harness/native-editor.html",
  "utf8",
);
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
const respond = (name, args) => {
  calls.push(name);
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
const fixture = `<!doctype html><html><body style="margin:0;background:#181818;color:white;font:13px system-ui"><div style="height:28px">Compiled Wright UI · simulated host and data · no engineering work</div><iframe title="Wright" id="panel" sandbox="allow-scripts allow-same-origin" style="width:100%;height:calc(100vh - 28px);border:0"></iframe><script>const f=document.querySelector('#panel');window.addEventListener('message',async e=>{if(e.source!==f.contentWindow)return;const m=e.data;const send=d=>f.contentWindow.postMessage({jsonrpc:'2.0',...d},'*');if(m.method==='ui/initialize')send({id:m.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'navigation-study',version:'1'},hostCapabilities:{message:{text:{}},serverTools:{},updateModelContext:{},experimental:{'openai/files':{},'openai/resource':{}}},hostContext:{theme:'dark'}}});else if(m.method==='ui/notifications/initialized'){send({method:'ui/notifications/tool-input',params:{arguments:{}}});send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:{view:'home',native_workspace_files_enabled:true}}});}else if(m.method==='tools/call'){const r=await fetch('/tool',{method:'POST',body:JSON.stringify(m.params)});send({id:m.id,result:await r.json()});}else if(m.method==='ui/message'){window.lastHandoff=m.params;send({id:m.id,result:{}});}else if(m.id)send({id:m.id,result:{}});});f.srcdoc=${safe(html)};</script></body></html>`;
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
  await f
    .getByLabel("Workspace", { exact: true })
    .selectOption(scope.workspace_id);
  await expect(
    f.getByRole("heading", { name: "Replacement handle", exact: true }),
  ).toBeVisible();
  await expect(f.getByLabel("Workspace", { exact: true })).toHaveCount(0);
  await expect(
    f.getByRole("button", { name: "Handle reference.png", exact: true }),
  ).toBeInViewport();
  await page.screenshot({ path: output + "/workspace-1100.png" });
  await f.getByRole("button", { name: "New workflow", exact: true }).click();
  await f
    .getByRole("button", { name: "Plan in Codex chat", exact: true })
    .click();
  await expect(
    f.getByRole("status").filter({ hasText: "Workspace context sent" }),
  ).toBeInViewport();
  const handoff = await page.evaluate(() => window.lastHandoff);
  const context = JSON.parse(handoff.content[0].text.split("\n").at(-1));
  expect(context.workspace_id).toBe(scope.workspace_id);
  expect(context.session_id).toBe(scope.session_id);
  await page.screenshot({ path: output + "/chat-handoff-1100.png" });
  await f.getByRole("button", { name: "New workflow", exact: true }).click();
  await f
    .getByRole("button", { name: "Change workspace", exact: true })
    .click();
  await expect(
    f.getByRole("button", { name: "Handle reference.png", exact: true }),
  ).toBeHidden();
  await f
    .getByRole("button", { name: "Return to Replacement handle", exact: true })
    .click();
  await f.locator("summary").filter({ hasText: "Workspace tools" }).click();
  await f.getByRole("button", { name: "Connections", exact: true }).click();
  await expect(
    f.getByRole("heading", { name: "Added tools", exact: true }),
  ).toBeVisible();
  await expect(
    f.getByRole("list", { name: "Connection list" }).getByRole("listitem"),
  ).toHaveCount(1);
  await expect(f.getByText(/unverified — last check expired/)).toBeVisible();
  await page.screenshot({ path: output + "/connections-1100.png" });
  await page.setViewportSize({ width: 480, height: 900 });
  await page.screenshot({ path: output + "/connections-480.png" });
  const dimensions = await f
    .locator("body")
    .evaluate((el) => ({ width: el.clientWidth, scroll: el.scrollWidth }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width);
  await f
    .getByRole("button", { name: "Browse tool catalog", exact: true })
    .click();
  await expect(
    f.getByRole("list", { name: "Connection list" }).getByRole("listitem"),
  ).toHaveCount(36);
  expect(errors).toEqual([]);
  writeFileSync(
    output + "/report.json",
    JSON.stringify(
      {
        status: "PASS",
        boundary:
          "compiled UI, simulated host and data; not Windows acceptance",
        resource_sha256: createHash("sha256").update(html).digest("hex"),
        checks: [
          "chooser hides files; return retains workspace",
          "workspace files visible",
          "chat handoff visible and exact workspace sent through public host message",
          "added tools only by default",
          "expired check remains visible",
          "catalog reachable without mutation",
          "480px no horizontal overflow",
        ],
        dimensions,
        calls,
        errors,
      },
      null,
      2,
    ),
  );
} finally {
  await browser.close();
  server.close();
}

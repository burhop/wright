// Simulated native-file host; actual compiled Wright UI, MCP, API and storage.
// No OpenAI-application automation or engineering execution. Disposable sources only.
// Usage: node SCRIPT STATE FIXTURES.json RUNTIME.json OUTPUT
import { createServer } from "node:http";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve, basename } from "node:path";
import { createHash } from "node:crypto";
import { chromium, expect } from "@playwright/test";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { CallToolResultSchema } from "@modelcontextprotocol/sdk/types.js";
const [stateArg, fixturesArg, runtimeArg, outputArg] = process.argv.slice(2);
const state = resolve(stateArg),
  fixture = JSON.parse(readFileSync(fixturesArg, "utf8"));
const runtime = JSON.parse(readFileSync(runtimeArg, "utf8")),
  output = resolve(outputArg);
mkdirSync(output); // Preserve failed attempts.
if (fixture.status !== "PASS" || fixture.workflows.length !== 2)
  throw Error("Use completed isolated fixtures");
if (!fixture.files.some((file) => file.filename === "opaque-upload.wflow"))
  throw Error(
    "Use current fresh fixtures including the opaque-upload fallback case",
  );
const scope = {
  workspace_id: fixture.workspace.workspace_id,
  session_id: fixture.workspace.session_id,
};
const html = readFileSync(
  resolve(runtime.runtime, "native-editor.html"),
  "utf8",
);
const hash = (x) => createHash("sha256").update(x).digest("hex");
expect(hash(html)).toBe(runtime.native_html_sha256);
const mcp = new Client({
  name: "wright-general-workspace-files-qualification",
  version: "0.1.0",
});
const transport = new StdioClientTransport({
  command:
    process.env.WRIGHT_PROBE_PYTHON ??
    resolve(
      process.platform === "win32"
        ? ".venv/Scripts/python.exe"
        : ".venv/bin/python",
    ),
  args: [
    resolve(runtime.runtime, "mcp_bridge.py"),
    "--state-dir",
    state,
    "--native-editor",
    "--native-working-view",
    "--native-workspace-files",
  ],
  env: {
    ...process.env,
    PYTHONPATH: runtime.python_paths.join(
      process.platform === "win32" ? ";" : ":",
    ),
  },
  stderr: "pipe",
});
transport.stderr?.on("data", () => {});
await mcp.connect(transport);
const data = (result) =>
  result.structuredContent ?? JSON.parse(result.content[0].text);
const read = async (name, args) => {
  const result = await mcp.callTool({ name, arguments: args });
  if (result.isError) throw Error("Owner rejected " + name);
  return data(result);
};
const calls = [],
  errors = [],
  checks = [],
  measurements = [];
const docsBefore = await Promise.all(
  fixture.workflows.map((x) => read("wright_workflow_read", x)),
);
const beforeHistory = await Promise.all(
  fixture.workflows.map((x) => read("wright_workflow_history", x)),
);
const documents = [];
const homeResult = await read("wright_home", scope);
expect(homeResult.native_workspace_files_enabled).toBe(true);
for (const file of [
  ...fixture.workflows,
  ...fixture.files.filter((x) => x.filename.endsWith(".png")),
]) {
  const d = await read("wright_workspace_file_describe", {
    request: { ...scope, path: file.path },
  });
  if (!d.supported) throw Error("Expected qualified fixture file");
  documents.push(d);
}
const allowedPaths = new Set(
  [...fixture.workflows, ...fixture.files].map((x) => x.path),
);
const allowedTools = new Set([
  "wright_workspace_list",
  "wright_workspace_files",
  "wright_workflow_read",
  "wright_workflow_open",
  "wright_workspace_file_describe",
  "wright_workflow_file_context",
  "wright_workflow_history",
  "wright_editor_drafts_read",
  "wright_editor_draft_save",
  "wright_workflow_save",
  "wright_workspace_file_preview",
  "wright_workspace_file_download",
  "wright_workflow_create",
  "wright_workflow_export",
  "wright_workflow_import_inspect",
  "wright_workflow_import",
]);
const safe = (x) => JSON.stringify(x).replaceAll("<", "\\u003c");
const host = `<!doctype html><html><meta charset="utf-8"><style>body{margin:0;background:#181818;color:#ddd;font:12px system-ui}header{padding:6px 10px;height:22px}nav{display:flex;gap:4px;height:32px;padding:0 8px}button{color:#ddd;background:#292929;border:1px solid #444;border-radius:5px;font:inherit;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}button[aria-current=page]{border-color:#aaa}iframe{border:0;width:100%;height:calc(100vh - 66px)}iframe[hidden]{display:none}</style><header>SIMULATED host tabs · real Wright UI/MCP/storage · no engineering run</header><nav aria-label="Simulated host files"><button onclick="activate('home')" data-tab="home">Workspace</button></nav><main></main><script>
window.states={};window.openRequests=[];
const docs=${safe(documents)},scope=${safe(scope)};
function activate(id){for(const f of document.querySelectorAll('iframe'))f.hidden=f.dataset.id!==id;for(const b of document.querySelectorAll('[data-tab]'))b.setAttribute('aria-current',b.dataset.tab===id?'page':'false');}
function add(id,title){const f=document.createElement('iframe');f.dataset.id=id;f.title='Wright '+title;f.src='/view/'+id;document.querySelector('main').append(f);if(id!=='home'){const b=document.createElement('button');b.dataset.tab=id;b.textContent=title;b.onclick=()=>activate(id);document.querySelector('nav').append(b);}activate(id);}
window.closeFile=id=>{document.querySelector('iframe[data-id="'+id+'"]').remove();document.querySelector('[data-tab="'+id+'"]').remove();activate('home');};
window.addEventListener('message',async event=>{
 const frame=[...document.querySelectorAll('iframe')].find(x=>x.contentWindow===event.source);if(!frame)return;
 const id=frame.dataset.id,file=id==='home'?null:docs[Number(id)],m=event.data;
 const send=x=>frame.contentWindow.postMessage({jsonrpc:'2.0',...x},location.origin);
 if(m.method==='ui/initialize')send({id:m.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'simulated-workspace-file-host',version:'1'},hostCapabilities:{serverTools:{},updateModelContext:{},experimental:{'openai/files':{},'openai/resource':{}}},hostContext:{theme:'dark',platform:'desktop'}}});
 if(m.method==='ui/notifications/initialized'){
  if(file){send({method:'ui/notifications/tool-input',params:{arguments:{file:{name:file.filename,resourceUri:'opaque:fixture-'+id}}}});}else{
   send({method:'ui/notifications/tool-input',params:{arguments:scope}});
   send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:${safe(homeResult)}}});
  }
 }
 if(m.method==='ui/update-model-context')send({id:m.id,result:{}});
 if(m.method==='openai/files/open'){
  let index=docs.findIndex(x=>x.absolute_path===m.params.path);
  if(index<0){const response=await fetch('/documents');const latest=await response.json();docs.splice(0,docs.length,...latest);index=docs.findIndex(x=>x.absolute_path===m.params.path);}
  if(index<0){send({id:m.id,error:{code:-32000,message:'Unqualified test path'}});return;}
  window.openRequests.push({path:m.params.path});
  if(!document.querySelector('iframe[data-id="'+index+'"]'))add(String(index),docs[index].filename);else activate(String(index));
  send({id:m.id,result:{}});
 }
 if(m.method==='tools/call'){
  try{const response=await fetch('/tool/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(m.params)});send({id:m.id,result:await response.json()});}
  catch{send({id:m.id,error:{code:-32000,message:'Fixture bridge unavailable'}});}
 }
});add('home','Workspace');
</script></html>`;
let createdAccepted,
  importSubmitted = false;
const importedPath = "workflows/imported-native-copy.workflow.wflow";
const server = createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/") {
      res.writeHead(200, { "Content-Type": "text/html;charset=utf-8" });
      res.end(host);
      return;
    }
    if (req.method === "GET" && req.url === "/documents") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(documents));
      return;
    }
    const match = /^\/view\/(home|[0-9]+)$/.exec(req.url);
    if (req.method === "GET" && match) {
      const id = match[1],
        doc = id === "home" ? null : documents[Number(id)];
      res.writeHead(200, { "Content-Type": "text/html;charset=utf-8" });
      if (doc?.viewer === "image") {
        res.end(
          `<!doctype html><body style="margin:0;background:#202020"><img alt="Retained copied preview" src="/image/${id}" style="max-width:100%;max-height:100vh"></body>`,
        );
        return;
      }
      const shim = `<head><script>window.openai={get widgetState(){return parent.states[${safe(id)}]??{};},setWidgetState(value){parent.states[${safe(id)}]=value;}};<\/script>`;
      res.end(html.replace("<head>", shim));
      return;
    }
    const image = /^\/image\/([0-9]+)$/.exec(req.url);
    if (req.method === "GET" && image) {
      const doc = documents[Number(image[1])];
      if (doc?.viewer !== "image") throw Error("Not an image");
      const bytes = readFileSync(doc.absolute_path);
      expect(hash(bytes)).toBe(doc.sha256);
      res.writeHead(200, { "Content-Type": "image/png" });
      res.end(bytes);
      return;
    }
    const route = /^\/tool\/(home|[0-9]+)$/.exec(req.url);
    if (req.method !== "POST" || !route) throw Error("Unknown fixture route");
    let raw = "";
    for await (const chunk of req) {
      raw += chunk;
      if (raw.length > 2 * 1024 * 1024) throw Error("Fixture body too large");
    }
    const { name, arguments: args } = JSON.parse(raw),
      body = args.request ?? args;
    if (!allowedTools.has(name))
      throw Error("Engineering/mutation tool denied: " + name);
    if (
      name !== "wright_workspace_list" &&
      name !== "wright_workflow_file_context"
    ) {
      if (
        body.workspace_id !== scope.workspace_id ||
        body.session_id !== scope.session_id
      )
        throw Error("Foreign workspace/session");
      if (name === "wright_workflow_create") {
        if (
          documents.length !== 3 ||
          !/^workflows\/untitled-workflow-[a-f0-9-]+\.workflow\.wflow$/.test(
            body.path,
          ) ||
          !body.source?.includes('name: "Native file authoring"')
        )
          throw Error("Only one named disposable workflow creation is allowed");
      } else if (body.path && !allowedPaths.has(body.path))
        throw Error("Foreign source/file");
      if (
        name === "wright_workflow_export" &&
        (!createdAccepted ||
          body.path !== createdAccepted.path ||
          body.expected_storage_digest !== createdAccepted.storage_digest)
      )
        throw Error("Export source differs");
      if (
        name === "wright_workflow_import_inspect" ||
        name === "wright_workflow_import"
      ) {
        if (
          !createdAccepted ||
          body.destination_path !== importedPath ||
          body.bundle?.source !== createdAccepted.source
        )
          throw Error("Import destination/source differs");
        if (name === "wright_workflow_import") {
          if (importSubmitted) throw Error("Repeated import denied");
          importSubmitted = true;
        }
      }
      if (
        name === "wright_workflow_save" &&
        body.path !== fixture.workflows[0].path
      )
        throw Error("Only designated disposable source may change");
    }
    const file = route[1] === "home" ? null : documents[Number(route[1])];
    const result = await mcp.request(
      {
        method: "tools/call",
        params: {
          name,
          arguments: args,
          ...(file
            ? { _meta: { "openai/resource": { path: file.absolute_path } } }
            : {}),
        },
      },
      CallToolResultSchema,
    );
    calls.push({ name, path: body.path ?? null, is_error: !!result.isError });
    if (name === "wright_workflow_create" && !result.isError) {
      const accepted = data(result);
      createdAccepted = accepted;
      allowedPaths.add(accepted.path);
      documents.push(
        await read("wright_workspace_file_describe", {
          request: { ...scope, path: accepted.path },
        }),
      );
    }
    if (name === "wright_workflow_import" && data(result).ok) {
      const accepted = data(result).document.source;
      allowedPaths.add(accepted.path);
      documents.push(
        await read("wright_workspace_file_describe", {
          request: { ...scope, path: accepted.path },
        }),
      );
    }
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(result));
  } catch (error) {
    errors.push(String(error));
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        isError: true,
        content: [
          { type: "text", text: "Qualification boundary rejected operation" },
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
  const page = await browser.newPage({
    viewport: { width: 1100, height: 900 },
  });
  await page.goto("http://127.0.0.1:" + server.address().port);
  const home = page.frameLocator('iframe[data-id="home"]');
  await expect(
    home.getByRole("heading", { name: "Workspace files", exact: true }),
  ).toBeVisible();
  await expect(
    home.getByRole("navigation", { name: "Workspace views" }),
  ).toHaveCount(0);
  expect(
    await page.evaluate(
      () => window.states.home.privateContent.wrightNavigation.view,
    ),
  ).toBe("files");
  const firstTitle = /^  name: "([^"]+)"/m.exec(docsBefore[0].source)[1];
  const secondTitle = /^  name: "([^"]+)"/m.exec(docsBefore[1].source)[1];
  await expect(
    home.getByRole("button", { name: firstTitle, exact: true }),
  ).toBeVisible();
  await expect(
    home.getByRole("button", { name: firstTitle, exact: true }),
  ).toBeInViewport();
  await page.screenshot({ path: resolve(output, "workspace-files.png") });
  for (const size of [
    { width: 1100, height: 900 },
    { width: 480, height: 820 },
  ]) {
    await page.setViewportSize(size);
    const box = await home
      .getByRole("list", { name: "Workspace files", exact: true })
      .boundingBox();
    expect(box.height).toBeLessThanOrEqual(
      Math.min((size.height - 66) * 0.58, 520) + 2,
    );
    const overflow = await home
      .locator("body")
      .evaluate((el) => el.scrollWidth > el.clientWidth + 2);
    expect(overflow).toBe(false);
    await expect(
      home.getByRole("button", { name: firstTitle, exact: true }),
    ).toBeInViewport();
    measurements.push({
      ...size,
      list_height: box.height,
      horizontal_overflow: overflow,
    });
    await page.screenshot({ path: resolve(output, `files-${size.width}.png`) });
  }
  checks.push(
    "Unified compact file landing, bounded list, accepted titles, narrow panel and no category tab strip",
  );
  const scaled = await browser.newPage({
    viewport: { width: 800, height: 700 },
    deviceScaleFactor: 1.5,
  });
  await scaled.goto("http://127.0.0.1:" + server.address().port);
  const scaledHome = scaled.frameLocator('iframe[data-id="home"]');
  await expect(
    scaledHome.getByRole("button", { name: firstTitle, exact: true }),
  ).toBeInViewport();
  const scaledList = await scaledHome
    .getByRole("list", { name: "Workspace files", exact: true })
    .boundingBox();
  measurements.push({
    width: 800,
    height: 700,
    scale: 1.5,
    list_height: scaledList.height,
    horizontal_overflow: await scaledHome
      .locator("body")
      .evaluate((el) => el.scrollWidth > el.clientWidth + 2),
  });
  expect(measurements.at(-1).horizontal_overflow).toBe(false);
  await scaled.screenshot({ path: resolve(output, "files-800-scale150.png") });
  await scaled.close();
  await page.setViewportSize({ width: 1100, height: 900 });
  await home.getByRole("button", { name: firstTitle, exact: true }).click();
  const a = page.frameLocator('iframe[data-id="0"]');
  await expect(a.getByTestId("workflow-recovery-save")).toBeVisible();
  await a.getByTestId("workflow-recovery-view-code").click();
  const editor = a.getByTestId("workflow-recovery-source-editor");
  await expect(editor).toHaveValue(docsBefore[0].source);
  const revised = docsBefore[0].source.replace(
    /^  name: "[^"]+"/m,
    `  name: ${JSON.stringify(firstTitle + " · native file check")}`,
  );
  await editor.fill(revised);
  await a.getByTestId("workflow-recovery-source-apply").click();
  await expect(a.getByTestId("workflow-recovery-undo")).toBeEnabled();
  await a.getByTestId("workflow-recovery-undo").click();
  await a.getByTestId("workflow-recovery-redo").click();
  await expect(a.getByTestId("workflow-recovery-save")).toBeEnabled();
  await a.getByTestId("workflow-recovery-save").click();
  await expect(a.getByTestId("workflow-recovery-save-status")).toHaveText(
    "Saved",
  );
  const saved = await read("wright_workflow_read", fixture.workflows[0]);
  expect(saved.source).toContain(firstTitle + " · native file check");
  checks.push(
    "Ordinary accepted file opens through metadata/MCP in independent viewer; edit, Undo/Redo and save reach actual owner",
  );
  await page.locator('[data-tab="home"]').click();
  await home.getByRole("button", { name: secondTitle, exact: true }).click();
  const b = page.frameLocator('iframe[data-id="1"]');
  await expect(b.getByTestId("workflow-recovery-save")).toBeVisible();
  await b.getByTestId("workflow-recovery-view-code").click();
  await expect(b.getByTestId("workflow-recovery-source-editor")).toHaveValue(
    docsBefore[1].source,
  );
  await page.screenshot({ path: resolve(output, "robot-workflow-file.png") });
  expect(await read("wright_workflow_read", fixture.workflows[1])).toEqual(
    docsBefore[1],
  );
  expect(await read("wright_workflow_history", fixture.workflows[1])).toEqual(
    beforeHistory[1],
  );
  checks.push(
    "Substantially different Robot Tracking Diagnosis opens via same file path; its source/history are unchanged",
  );
  await page.locator('[data-tab="home"]').click();
  const png = fixture.files.find((x) => x.filename.endsWith(".png"));
  await home.getByLabel("Find a file").fill("retained preview");
  await expect(
    home.getByRole("button", { name: png.filename, exact: true }),
  ).toBeInViewport();
  await home.getByRole("button", { name: png.filename, exact: true }).click();
  const img = page
    .frameLocator('iframe[data-id="2"]')
    .getByRole("img", { name: "Retained copied preview" });
  await expect(img).toBeVisible();
  await expect
    .poll(() => img.evaluate((el) => el.naturalWidth))
    .toBeGreaterThan(0);
  await page.screenshot({ path: resolve(output, "image-tab.png") });
  checks.push(
    "PNG native-open request uses qualified bytes; simulated host image decoder displays retained copied image",
  );
  await page.evaluate(() => window.closeFile("0"));
  await home.getByRole("button", { name: "Refresh", exact: true }).click();
  await home
    .getByRole("button", {
      name: firstTitle + " · native file check",
      exact: true,
    })
    .click();
  const reopened = page.frameLocator('iframe[data-id="0"]');
  await expect(reopened.getByTestId("workflow-recovery-save")).toBeVisible();
  await reopened.getByTestId("workflow-recovery-view-code").click();
  await expect(
    reopened.getByTestId("workflow-recovery-source-editor"),
  ).toHaveValue(saved.source);
  await page.screenshot({ path: resolve(output, "saved-reopened.png") });
  checks.push(
    "Close/remount reopens current accepted revision using remembered exact scope; no fixed manifest pin prevents ordinary saves",
  );
  await page.evaluate((oldDigest) => {
    window.closeFile("0");
    window.states["0"].privateContent.wrightNavigation.workflow.source_digest =
      oldDigest;
  }, docsBefore[0].storage_digest);
  await home
    .getByRole("button", {
      name: firstTitle + " · native file check",
      exact: true,
    })
    .click();
  const stale = page.frameLocator('iframe[data-id="0"]');
  await expect(
    stale.getByRole("button", {
      name: "Open current saved revision",
      exact: true,
    }),
  ).toBeVisible();
  await expect(stale.getByTestId("workflow-recovery-save")).toHaveCount(0);
  await page.screenshot({ path: resolve(output, "changed-context-held.png") });
  await stale
    .getByRole("button", { name: "Open current saved revision", exact: true })
    .click();
  await expect(stale.getByTestId("workflow-recovery-save")).toBeVisible();
  await expect(stale.locator(".react-flow__node").first()).toBeVisible();
  await page.screenshot({
    path: resolve(output, "current-revision-diagram.png"),
  });
  await stale.getByTestId("workflow-recovery-view-code").click();
  await expect(
    stale.getByTestId("workflow-recovery-source-editor"),
  ).toHaveValue(saved.source);
  expect(await read("wright_workflow_read", fixture.workflows[0])).toEqual(
    saved,
  );
  checks.push(
    "A genuinely stale remembered digest holds before rendering; explicit current-revision open reconciles without rewriting source or replaying work",
  );
  await page.locator('[data-tab="home"]').click();
  const step = fixture.files.find((x) => x.filename.endsWith(".step"));
  const opensBefore = await page.evaluate(() => window.openRequests.length);
  await home.getByRole("button", { name: step.filename, exact: true }).click();
  await expect(
    home.getByRole("region", { name: "File preview" }),
  ).toBeVisible();
  expect(await page.evaluate(() => window.openRequests.length)).toBe(
    opensBefore,
  );
  await page.screenshot({
    path: resolve(output, "unsupported-step-fallback.png"),
  });
  checks.push(
    "Unqualified STEP stays in explicit existing preview/download fallback; no CAD renderer or native open is invented",
  );
  await home
    .getByRole("button", { name: "Close preview", exact: true })
    .click();
  const opaque = fixture.files.find(
    (x) => x.filename === "opaque-upload.wflow",
  );
  if (opaque) {
    await home.getByLabel("Find a file").fill("opaque upload");
    const opens = await page.evaluate(() => window.openRequests.length);
    await home
      .getByRole("button", { name: opaque.filename, exact: true })
      .click();
    await expect(
      home.getByRole("region", { name: "File preview" }),
    ).toBeInViewport();
    await expect(
      home.getByRole("region", { name: "File preview" }).locator("pre"),
    ).toContainText("Opaque file preview");
    expect(await page.evaluate(() => window.openRequests.length)).toBe(opens);
    await home
      .getByRole("button", { name: "Close preview", exact: true })
      .click();
    checks.push(
      "Uploaded .wflow retains an ordinary read-only file preview; it is not silently accepted or executed as a workflow",
    );
  }
  await home.getByRole("button", { name: "New workflow", exact: true }).click();
  await home
    .getByLabel("Workflow name", { exact: true })
    .fill("Native file authoring");
  await home
    .getByRole("button", { name: "Create workflow", exact: true })
    .click();
  const created = page.frameLocator('iframe[data-id="3"]');
  await expect(created.getByTestId("workflow-recovery-save")).toBeVisible();
  await created.getByTestId("workflow-recovery-view-code").click();
  await expect(
    created.getByTestId("workflow-recovery-source-editor"),
  ).toHaveValue(/name: "Native file authoring"/);
  await page.locator('[data-tab="home"]').click();
  await home.getByLabel("Find a file").fill("native file authoring");
  await expect(
    home.getByRole("button", { name: "Native file authoring", exact: true }),
  ).toBeInViewport();
  await expect(
    home.getByRole("button", { name: "New workflow", exact: true }),
  ).toBeEnabled();
  await page.screenshot({ path: resolve(output, "created-title-search.png") });
  await page.evaluate(() => window.closeFile("3"));
  await home
    .getByRole("button", { name: "Native file authoring", exact: true })
    .click();
  await expect(
    page
      .frameLocator('iframe[data-id="3"]')
      .getByTestId("workflow-recovery-save"),
  ).toBeVisible();
  checks.push(
    "Create/name through the visible workspace files UI, open the new native tab, search the accepted title and close/reopen without UUID labels or a stuck creation form",
  );
  const exportFrame = page.frameLocator('iframe[data-id="3"]');
  const originalCopy = await read("wright_workflow_read", {
    ...scope,
    path: documents[3].path,
  });
  const originalHistory = await read("wright_workflow_history", {
    ...scope,
    path: documents[3].path,
  });
  await exportFrame.locator(".native-workflow-details > summary").click();
  await exportFrame
    .getByRole("button", { name: "Export / import workflow", exact: true })
    .click();
  const downloadEvent = page.waitForEvent("download");
  await exportFrame.getByTestId("workflow-transfer-export").click();
  const download = await downloadEvent,
    transferFile = await download.path();
  const transferBytes = readFileSync(transferFile);
  writeFileSync(
    resolve(output, "exported-native-source.wright-workflow.json"),
    transferBytes,
  );
  expect(transferBytes.toString()).toContain("wright.workflow-instructions/1");
  await exportFrame.getByTestId("workflow-transfer-upload").setInputFiles({
    name: "native-workflow-transfer.json",
    mimeType: "application/json",
    buffer: transferBytes,
  });
  await exportFrame
    .getByTestId("workflow-transfer-destination")
    .fill(importedPath);
  await exportFrame.getByTestId("workflow-transfer-inspect").click();
  await expect(
    exportFrame.getByTestId("workflow-transfer-import"),
  ).toBeEnabled();
  await exportFrame.getByTestId("workflow-transfer-import").click();
  const imported = page.frameLocator('iframe[data-id="4"]');
  await expect(imported.getByTestId("workflow-recovery-save")).toBeVisible();
  await imported.getByTestId("workflow-recovery-view-code").click();
  await expect(
    imported.getByTestId("workflow-recovery-source-editor"),
  ).toHaveValue(originalCopy.source);
  expect(
    await read("wright_workflow_read", { ...scope, path: documents[3].path }),
  ).toEqual(originalCopy);
  expect(
    await read("wright_workflow_history", {
      ...scope,
      path: documents[3].path,
    }),
  ).toEqual(originalHistory);
  expect(calls.filter((x) => x.name === "wright_workflow_import")).toHaveLength(
    1,
  );
  await page.screenshot({
    path: resolve(output, "imported-copy-native-tab.png"),
  });
  checks.push(
    "Browser export/download and inspected one-time import preserve source/instructions; the accepted copy opens in a separate native-file view without replacing the original or replaying import",
  );
  expect(errors).toEqual([]);
  status = "PASS";
} catch (error) {
  failure = String(error);
} finally {
  const after = await Promise.all(
    fixture.workflows.map((x) => read("wright_workflow_read", x)),
  );
  writeFileSync(
    resolve(output, "report.json"),
    JSON.stringify(
      {
        status,
        failure,
        boundary:
          "SIMULATED host; real compiled Wright UI/MCP/API/storage, not actual OpenAI desktop or Windows acceptance",
        native_html_sha256: hash(html),
        checks,
        measurements,
        calls,
        errors,
        sources: fixture.workflows.map((x, i) => ({
          path: x.path,
          before: docsBefore[i].storage_digest,
          after: after[i].storage_digest,
        })),
        engineering_execution:
          "none; allowlist excludes all execution/review/provider calls",
      },
      null,
      2,
    ),
  );
  await browser.close();
  await new Promise((done) => server.close(done));
  await mcp.close();
}
if (status !== "PASS") throw Error(failure);
console.log(JSON.stringify({ status, checks: checks.length, output }));

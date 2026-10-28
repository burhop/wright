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
import { platform, arch } from "node:os";
import { chromium, expect } from "@playwright/test";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const state = resolve(process.argv[2]);
const input = JSON.parse(readFileSync(process.argv[3], "utf8"));
const deviceScaleFactor = input.device_scale_factor ?? 1;
if (![1, 1.25, 1.5, 2].includes(deviceScaleFactor))
  throw Error("Use a supported bounded display scale");
const nameLookupDelay = input.name_lookup_delay_ms ?? 0;
if (
  !Number.isInteger(nameLookupDelay) ||
  nameLookupDelay < 0 ||
  nameLookupDelay > 2000
)
  throw Error("Name lookup delay must be between zero and two seconds");
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
const bundlePath = resolve(
  process.env.WRIGHT_PROBE_BUNDLE ??
    "prototypes/desktop-harness/native-editor.html",
);
const originalBundle = readFileSync(bundlePath, "utf8");
const bundle = originalBundle.replace(
  "<head>",
  "<head><script>window.openai={widgetState:parent.fixtureWidgetState??{},setWidgetState(value){this.widgetState=value;parent.fixtureWidgetState=value;}};</script>",
);
const safe = (value) => JSON.stringify(value).replaceAll("<", "\\u003c");
const fixtureHostContext = {
  theme: "dark",
  ...(input.ui_review
    ? {
        platform: "desktop",
        styles: {
          variables: {
            "--font-sans": "system-ui",
            "--color-text-primary": "#eeeeee",
          },
        },
        toolInfo: {
          id: "fixture",
          tool: {
            name: "wright_home",
            inputSchema: { type: "object" },
            _meta: {
              ui: {
                resourceUri: `ui://wright/workflow/${createHash("sha256").update(originalBundle).digest("hex")}.html`,
              },
            },
          },
        },
      }
    : {}),
};
const fixture = `<!doctype html><html><meta charset="utf-8"><body style="margin:0;background:#181818;color:#ddd;font:12px system-ui"><div style="height:28px;padding:0 12px;display:flex;align-items:center">Wright prototype · simulated desktop host · actual saved workflow${input.run_id ? " and recorded results · read only" : " · isolated source copy · no engineering run"}</div><iframe id="panel" title="Wright" style="border:0;width:100%;height:calc(100vh - 28px)"></iframe><script>
const frame=document.getElementById('panel');
window.addEventListener('message',async event=>{
 if(event.source!==frame.contentWindow)return;
 const m=event.data, send=data=>frame.contentWindow.postMessage({jsonrpc:'2.0',...data},'*');
 if(m.method==='ui/initialize')send({id:m.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'wright-navigation-fixture',version:'1'},hostCapabilities:{serverTools:{},updateModelContext:{},${input.ui_review ? "message:{text:{}}," : ""}},hostContext:${safe(fixtureHostContext)}}});
 if(m.method==='ui/notifications/initialized'){
  send({method:'ui/notifications/tool-input',params:{arguments:${safe({ workspace_id: scope.workspace_id, session_id: scope.session_id })}}});
  send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:{view:'home',selection:${safe(workspace)}}}});
 }
 if(m.method==='ui/update-model-context'){window.lastContext=m.params;send({id:m.id,result:{}});}
 if(m.method==='ui/message'){window.reviewMessages??=[];window.reviewMessages.push(m.params);send({id:m.id,result:{}});}
 if(m.method==='tools/call'){
  try {const r=await fetch('/tool',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(m.params)});send({id:m.id,result:await r.json()});}
  catch {send({id:m.id,error:{code:-32000,message:'Qualification transport unavailable'}});}
 }
});frame.srcdoc=${safe(bundle)};
</script></body></html>`;
const allowed = new Set([
  ...(input.ui_review ? ["wright_workspace_file_upload"] : []),
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
    if (name === "wright_workspace_file_upload") {
      if (
        !input.ui_review ||
        !/^wright-ui-review-[a-f0-9-]{36}\.json$/.test(request.filename) ||
        request.content_base64.length > 90_000
      )
        throw Error(
          "Only a bounded explicitly prepared UI report may be saved",
        );
      const bytes = Buffer.from(request.content_base64, "base64");
      const report = JSON.parse(bytes.toString("utf8"));
      if (
        report.schema_version !== "wright.ui-review/1" ||
        report.location.navigation.workspace_id !== scope.workspace_id ||
        createHash("sha256").update(bytes).digest("hex") !== request.sha256
      )
        throw Error("UI report identity differs");
    }
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
      name !== "wright_workflow_read" &&
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
    if (name === "wright_workflow_read" && nameLookupDelay)
      await new Promise((done) => setTimeout(done, nameLookupDelay));
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
const page = await browser.newPage({
  viewport: { width: 1080, height: 900 },
  deviceScaleFactor,
});
page.setDefaultTimeout(20_000);
page.on("pageerror", (error) => errors.push(error.message));
const frame = page.frameLocator("#panel");
try {
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await expect(frame.getByLabel("Workspace", { exact: true })).toHaveValue(
    scope.workspace_id,
  );
  if (nameLookupDelay) {
    await expect(
      frame.getByText("Reading saved workflow names…", { exact: true }),
    ).toBeVisible();
    await frame
      .getByLabel("Find a workflow", { exact: true })
      .fill(input.search_while_loading ?? "");
    await expect(
      frame.getByText("No workflows match this search.", { exact: true }),
    ).toHaveCount(0);
    await expect(frame.locator(".native-home__workflows")).not.toBeVisible();
    await page.screenshot({
      path: resolve(output, "reading-workflow-names.png"),
    });
    checks.push(
      "Delayed metadata explains loading; no temporary filename or false empty search is presented",
    );
  }
  await expect(
    frame
      .locator(".native-home__workflows li")
      .filter({ hasText: "/" + scope.path })
      .getByRole("button"),
  ).toBeVisible();
  await page.screenshot({ path: resolve(output, "home.png") });
  await frame
    .locator(".native-home__workflows li")
    .filter({ hasText: "/" + scope.path })
    .getByRole("button")
    .click();
  await expect(frame.getByTestId("workflow-recovery-save")).toBeVisible();
  if (input.assert_usability) {
    await expect(
      frame.getByRole("button", { name: "Edit workflow", exact: true }),
    ).toHaveAttribute("aria-current", "page");
    await frame.locator(".native-workflow-details > summary").click();
    await expect(
      frame.locator(".native-workflow-panel__view-hint"),
    ).toBeVisible();
    await expect(
      frame.locator(".native-workflow-panel__view-hint"),
    ).toContainText("no run selected");
    await frame.locator(".native-workflow-details > summary").press("Escape");
    await expect(
      frame.getByRole("button", { name: "← Workspace home", exact: true }),
    ).toBeVisible();
    checks.push(
      "Editor names the task and explains no run is selected; workspace return is explicit",
    );
  }
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
      .getByRole("button", { name: "← Workspace home", exact: true })
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
    .getByRole("button", { name: /^(Run workflow|View run|Run and results)$/, exact: true })
    .click();
  await expect(frame.getByTestId("common-process-view")).toBeVisible();
  if (input.assert_usability) {
    const typography = await frame
      .locator(".wright-process-ui")
      .evaluate((el) => getComputedStyle(el).fontFamily);
    expect(typography).toMatch(/system-ui|sans-serif|Segoe|Arial|Inter/i);
    checks.push(
      "Results retain host sans-serif typography rather than browser-default serif",
    );
  }
  await frame.getByRole("button", { name: /^(Previous runs|Run history)$/, exact: true }).click();
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
    await expect(
      frame
        .getByTestId("common-process-view")
        .getByText("Loading the saved process state…", { exact: true }),
    ).toHaveCount(0);
    await expect(frame.locator(".wp-result").first()).toBeVisible();
    await page.screenshot({ path: resolve(output, "run-results.png") });
    if (input.preview_filename) {
      const result = frame
        .locator(".wp-result")
        .filter({ hasText: input.preview_filename });
      await expect(
        result.getByRole("heading", {
          name: input.preview_filename,
          exact: true,
        }),
      ).toBeVisible();
      const recordedTitle = await result.locator("h3").getAttribute("title");
      if (!recordedTitle?.endsWith(input.preview_filename))
        throw Error("Result heading lost its recorded title");
      await result.getByText("File details", { exact: true }).click();
      await expect(result.locator(".wp-evidence code").first()).toHaveText(
        recordedTitle,
      );
      await result.getByText("File details", { exact: true }).click();
      await page.screenshot({ path: resolve(output, "readable-results.png") });
      await page.setViewportSize({ width: 480, height: 820 });
      await expect(
        result.getByRole("heading", {
          name: input.preview_filename,
          exact: true,
        }),
      ).toBeVisible();
      expect(
        await frame
          .locator("body")
          .evaluate((element) => element.scrollWidth > element.clientWidth + 1),
      ).toBe(false);
      await page.screenshot({
        path: resolve(output, "readable-results-narrow.png"),
      });
      await page.setViewportSize({ width: 1080, height: 900 });
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
      await expect(
        frame.getByRole("button", { name: /Results · 1\/1 available/ }),
      ).toBeVisible();
      const inspector = frame.getByTestId("workflow-recovery-inspector");
      await expect(
        inspector.getByText("Files produced in this run", { exact: true }),
      ).toBeVisible();
      await expect(inspector).toContainText(input.preview_filename);
      if (input.assert_usability)
        await expect(
          frame.locator(".native-workflow-panel__run"),
        ).toContainText(input.run_id);
      await expect(inspector).not.toContainText(
        "different saved workflow or an edited draft",
      );
      await page.screenshot({ path: resolve(output, "producing-step.png") });
      const inspectorFont = await inspector
        .getByText("What this step does", { exact: true })
        .evaluate((el) => getComputedStyle(el).fontFamily);
      const typography = await inspector
        .locator("h2,h3,h4,p,li,b")
        .evaluateAll((nodes) =>
          nodes.map((el) => ({
            text: el.textContent?.trim().slice(0, 90),
            family: getComputedStyle(el).fontFamily,
            size: getComputedStyle(el).fontSize,
          })),
        );
      writeFileSync(
        resolve(output, "inspector-typography.json"),
        JSON.stringify(typography, null, 2),
      );
      expect(inspectorFont).toMatch(/system-ui|sans-serif/i);
      expect(inspectorFont).not.toMatch(/Times/i);
      checks.push(
        "Producing-step inspector retains the native host sans-serif font",
      );
      checks.push(
        "Exact selected run supplies available results and producing-step files without a false source mismatch",
      );
      await frame
        .getByRole("button", { name: /^(Run workflow|View run|Run and results)$/, exact: true })
        .click();
      await expect(frame.getByTestId("common-process-view")).toBeVisible();
      checks.push(
        "Actual retained PNG displayed with matching byte hash; result links to producing-step inspector and back to the same run",
        "Filename heading fits normal/narrow panel; exact recorded path remains in File details",
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
    .getByRole("button", { name: "Edit workflow", exact: true })
    .click();
  await frame.getByTestId("workflow-recovery-view-code").click();
  await expect(editor).toHaveValue(accepted.source);
  await frame
    .getByRole("button", { name: "← Workspace home", exact: true })
    .click();
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
  await frame
    .getByRole("button", { name: "← Workspace home", exact: true })
    .click();
  await expect(frame.getByLabel("Workspace", { exact: true })).toHaveValue(
    scope.workspace_id,
  );
  await expect(
    frame
      .locator(".native-home__workflows li")
      .filter({ hasText: "/" + scope.path })
      .getByRole("button"),
  ).toBeVisible();
  await expect(frame.getByText("Loading...", { exact: true })).toHaveCount(0);
  await expect(reopen).toBeVisible();
  await page.screenshot({ path: resolve(output, "home-narrow.png") });
  const overflow = await frame
    .locator("body")
    .evaluate((el) => el.scrollWidth > el.clientWidth + 1);
  expect(overflow).toBe(false);
  if (input.ui_review) {
    // Deliberate negative control, not a claimed user defect or native-host capture.
    const refresh = frame.getByRole("button", { name: "Refresh", exact: true });
    const originalStyle = await refresh.getAttribute("style");
    await refresh.evaluate((element) => {
      element.style.width = "700px";
      element.style.minWidth = "700px";
      element.style.flexShrink = "0";
    });
    await frame
      .getByRole("button", { name: "Report UI problem", exact: true })
      .click();
    await frame
      .getByRole("button", { name: "Point to an element", exact: true })
      .click();
    const callCount = calls.length;
    // Click its currently visible part; do not auto-scroll the oversized negative control.
    const targetBox = await refresh.boundingBox();
    expect(targetBox).not.toBeNull();
    await page.mouse.click(
      Math.max(12, targetBox.x) + 12,
      targetBox.y + targetBox.height / 2,
    );
    await expect(frame.getByText(/selected button/)).toBeVisible();
    expect(calls.length).toBe(callCount); // Picking never activates the selected button.
    await frame
      .getByLabel("Problem description", { exact: true })
      .fill(
        "Controlled clipping fixture: Refresh extends past the right edge.",
      );
    await page.screenshot({
      path: resolve(output, "ui-report-before-save.png"),
    });
    await frame
      .getByRole("button", { name: "Save UI report", exact: true })
      .click();
    await expect(frame.getByText(/Report saved for the tester/)).toBeVisible();
    const uploaded = calls.filter(
      (item) => item.name === "wright_workspace_file_upload",
    );
    expect(uploaded).toHaveLength(1);
    const request = uploaded[0].arguments.request;
    const path = `uploads/${request.sha256}/${request.filename}`;
    await expect
      .poll(() =>
        page.evaluate(
          () => window.lastContext?.structuredContent?.ui_problem_report?.path,
        ),
      )
      .toBe(path);
    if (input.run_id)
      expect(
        await page.evaluate(
          () => window.lastContext?.structuredContent?.workflow?.run_id,
        ),
      ).toBe(input.run_id);
    // Independent read through the real MCP owner, not the component's in-memory copy.
    const retained = await read("wright_workspace_file_download", {
      workspace_id: scope.workspace_id,
      session_id: scope.session_id,
      path,
    });
    expect(retained.supported).toBe(true);
    expect(retained.content_base64).toBe(request.content_base64);
    const bytes = Buffer.from(retained.content_base64, "base64");
    expect(createHash("sha256").update(bytes).digest("hex")).toBe(
      retained.sha256,
    );
    const report = JSON.parse(bytes.toString("utf8"));
    expect(report.selected_element.horizontal_clip).toBe(true);
    expect(report.selected_element.relative_selector).toContain(
      "button:nth-of-type",
    );
    expect(report.location.navigation.workspace_id).toBe(scope.workspace_id);
    expect(report.build.resource_uri).toContain(
      createHash("sha256").update(originalBundle).digest("hex"),
    );
    expect(report.build.bundle_payload_sha256).toMatch(/^[a-f0-9]{64}$/);
    expect(report.host.platform).toBe("desktop"); // A reported fixture signal, never native proof.
    expect(report.viewport.width).toBe(480);
    expect(report.comment).toContain("Controlled clipping fixture");
    expect(bytes.length).toBeLessThan(65536);
    writeFileSync(resolve(output, "retrieved-ui-report.json"), bytes);
    writeFileSync(
      resolve(output, "ui-report-receipt.json"),
      JSON.stringify(
        {
          scope,
          path,
          sha256: retained.sha256,
          bytes: retained.bytes,
          retrieval: "Separate real MCP file-download call",
          native_host: "UNVERIFIED",
        },
        null,
        2,
      ),
    );
    await frame
      .getByRole("button", { name: "Ask chat to review", exact: true })
      .click();
    await expect(
      frame.getByText("Review request sent to this conversation.", {
        exact: true,
      }),
    ).toBeVisible();
    const messages = await page.evaluate(() => window.reviewMessages);
    expect(messages).toHaveLength(1);
    expect(messages[0].content[0].text).toContain(path);
    writeFileSync(
      resolve(output, "ui-review-chat-receipt.json"),
      JSON.stringify(
        {
          boundary:
            "Simulated host accepted ui/message; no claim that a native chat turn ran",
          messages,
        },
        null,
        2,
      ),
    );
    await page.screenshot({ path: resolve(output, "ui-report-saved.png") });
    await frame
      .getByRole("button", { name: "Close report", exact: true })
      .click();
    await refresh.evaluate((element, style) => {
      if (style === null) element.removeAttribute("style");
      else element.setAttribute("style", style);
    }, originalStyle);
    checks.push(
      "Opt-in UI review captures a deliberately clipped Wright control, suppresses its action, saves once and is independently read back with matching bytes through actual MCP/storage; no screenshot or native-host claim",
    );
  }
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
          "Real Wright MCP/storage; simulated desktop host, not native OpenAI desktop acceptance",
        name_lookup_delay_ms: nameLookupDelay,
        host: {
          platform: platform(),
          architecture: arch(),
          node: process.version,
          device_scale_factor: deviceScaleFactor,
        },
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
  server.closeAllConnections();
  await new Promise((done) => server.close(done));
  await mcp.close();
}

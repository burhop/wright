// Fresh normal-owner UI fixtures. Refuses replay of a partial or completed setup.
// Usage: node SCRIPT STATE RUNTIME.json OUTPUT.json [PNG]
// No model requests, engineering execution, grants, reviews or provider calls.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
const [stateArg, runtimeArg, outputArg, imageArg] = process.argv.slice(2);
const state = resolve(stateArg),
  runtime = JSON.parse(readFileSync(runtimeArg, "utf8")),
  output = resolve(outputArg);
if (existsSync(output))
  throw Error(
    "Preserve prior setup. Reconcile its recorded intent before another write.",
  );
const receipt = {
  boundary: "Fresh isolated normal-owner fixtures; no engineering execution",
  workflows: [],
  files: [],
  calls: [],
};
const save = () => writeFileSync(output, JSON.stringify(receipt, null, 2));
const mcp = new Client({
  name: "wright-native-workspace-file-fixtures",
  version: "1",
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
async function call(name, args) {
  receipt.intent = {
    tool: name,
    ...(args.path ? { path: args.path } : {}),
    ...(args.workflow_path ? { path: args.workflow_path } : {}),
    ...(args.request_id ? { request_id: args.request_id } : {}),
  };
  save();
  const result = await mcp.callTool({ name, arguments: args });
  receipt.calls.push({ name, is_error: !!result.isError });
  save();
  if (result.isError)
    throw Error(
      "Owner rejected " +
        name +
        "; reconcile the recorded intent instead of replaying setup.",
    );
  const data = result.structuredContent ?? JSON.parse(result.content[0].text);
  receipt.intent = null;
  save();
  return data;
}
try {
  await mcp.connect(transport);
  const name = "Native file qualification " + randomUUID().slice(0, 8);
  receipt.workspace = await call("wright_workspace_create", { name });
  save();
  const scope = {
    workspace_id: receipt.workspace.workspace_id,
    session_id: receipt.workspace.session_id,
  };
  const path = "workflows/mounting-bracket.workflow.wflow";
  const mounting = await call("wright_workflow_create", {
    ...scope,
    path,
    source: readFileSync(
      resolve(
        "specs/080-canonical-workflow-recovery/fixtures/mounting-bracket.workflow.wflow",
      ),
      "utf8",
    ),
  });
  receipt.workflows.push({
    ...scope,
    path,
    storage_digest: mounting.storage_digest,
  });
  save();
  const catalog = await call("wright_workflow_templates", scope),
    template = catalog.templates.find(
      (x) => x.template_id === "robot-tracking-diagnosis",
    );
  if (!template)
    throw Error("Existing Robot Tracking Diagnosis template unavailable");
  const robot = await call("wright_workflow_template_create", {
    ...scope,
    template_id: template.template_id,
    template_version: template.version,
    expected_source_digest: template.source_digest,
    workflow_path: "workflows/robot-tracking-diagnosis.workflow.wflow",
    request_id: randomUUID(),
  });
  receipt.workflows.push({
    ...scope,
    path: robot.path,
    storage_digest: robot.storage_digest,
  });
  save();
  const image = imageArg
    ? readFileSync(imageArg)
    : Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a7doAAAAASUVORK5CYII=",
        "base64",
      );
  const uploads = [
    ["retained-preview.png", image],
    [
      "viewer-not-qualified.step",
      Buffer.from(
        "ISO-10303-21;\n/* Unqualified presentation fixture, not engineering evidence. */\nEND-ISO-10303-21;\n",
      ),
    ],
    [
      "opaque-upload.wflow",
      Buffer.from(
        'workflow opaque_input\n  name: "Opaque file preview"\nend\n',
      ),
    ],
    ...Array.from({ length: 24 }, (_, i) => [
      `measurement-${String(i + 1).padStart(2, "0")}.csv`,
      Buffer.from(`sample,mm\n${i + 1},${(i + 1) * 2}\n`),
    ]),
  ];
  for (const [filename, content] of uploads) {
    const result = await call("wright_workspace_file_upload", {
      request: {
        ...scope,
        filename,
        sha256: createHash("sha256").update(content).digest("hex"),
        content_base64: content.toString("base64"),
      },
    });
    if (!result.ok || !result.document)
      throw Error(
        "Upload outcome unconfirmed; inspect saved files instead of replaying.",
      );
    receipt.files.push({
      filename,
      path: result.document.path,
      sha256: result.document.sha256,
    });
    save();
  }
  receipt.status = "PASS";
  save();
  console.log(
    JSON.stringify({
      status: "PASS",
      workflows: receipt.workflows.length,
      files: receipt.files.length,
      output,
    }),
  );
} finally {
  await mcp.close();
}

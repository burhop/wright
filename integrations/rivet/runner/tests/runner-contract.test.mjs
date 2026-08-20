import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import test from "node:test";

const root = resolve(import.meta.dirname, "..");
const runner = resolve(root, "dist", "wright-runner.mjs");
const fixtures = resolve(root, "tests", "fixtures");

const passthroughProject = `version: 4
data:
  attachedData: {}
  graphs:
    graph-1:
      metadata:
        id: graph-1
        name: Main
        description: ""
      nodes:
        '[input-node]:graphInput "Input"':
          data:
            id: input
            dataType: string
            useDefaultValueInput: false
          outgoingConnections:
            - data->"Output" output-node/value
          visualData: 0/0/200/null//
        '[output-node]:graphOutput "Output"':
          data:
            id: output
            dataType: string
          visualData: 300/0/200/null//
  metadata:
    id: project-1
    title: Contract
    description: ""
    mainGraphId: graph-1
  plugins: []
`;

const discoveryProject = `version: 4
data:
  attachedData: {}
  graphs:
    graph-1:
      metadata:
        id: graph-1
        name: Main
        description: ""
      nodes:
        '[discovery-node]:mcpDiscovery "Reviewed tools"':
          data:
            name: wright-rivet
            version: 2.0.0
            transportType: http
            useNameInput: false
            useVersionInput: false
            useServerUrlInput: false
            useServerIdInput: false
            useToolsOutput: true
            usePromptsOutput: false
          outgoingConnections:
            - tools->"Output" output-node/value
          visualData: 0/0/280/null//
        '[output-node]:graphOutput "Output"':
          data:
            id: output
            dataType: object[]
          visualData: 400/0/280/null//
  metadata:
    id: discovery-project
    title: Reviewed discovery
    description: ""
    mainGraphId: graph-1
  plugins: []
`;

function invoke(project, overrides = {}) {
  const directory = mkdtempSync(resolve(tmpdir(), "wright-rivet-runner-"));
  try {
    const projectPath = resolve(directory, "workflow.rivet-project");
    writeFileSync(projectPath, project, "utf8");
    const digest = createHash("sha256")
      .update(readFileSync(projectPath))
      .digest("hex");
    const request = {
      protocolVersion: 1,
      runId: "run-contract",
      projectPath,
      expectedDigest: digest,
      graph: "Main",
      inputs: { input: "hello" },
      context: {},
      capabilities: [],
      ...overrides,
    };
    return spawnSync(process.execPath, [runner], {
      input: JSON.stringify(request),
      encoding: "utf8",
      timeout: 10_000,
    });
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

async function invokeAsync(project, overrides = {}) {
  const directory = mkdtempSync(resolve(tmpdir(), "wright-rivet-runner-"));
  const projectPath = resolve(directory, "workflow.rivet-project");
  writeFileSync(projectPath, project, "utf8");
  const digest = createHash("sha256")
    .update(readFileSync(projectPath))
    .digest("hex");
  const request = {
    protocolVersion: 2,
    runId: "run-contract",
    projectPath,
    expectedDigest: digest,
    graph: "Main",
    inputs: {},
    context: {},
    capabilities: ["mcp"],
    ...overrides,
  };
  try {
    return await new Promise((resolveResult, reject) => {
      const child = spawn(process.execPath, [runner], {
        stdio: ["pipe", "pipe", "pipe"],
      });
      let stdout = "";
      let stderr = "";
      child.stdout.setEncoding("utf8").on("data", (value) => (stdout += value));
      child.stderr.setEncoding("utf8").on("data", (value) => (stderr += value));
      child.once("error", reject);
      child.once("close", (status) =>
        resolveResult({ status, stdout, stderr }),
      );
      child.stdin.end(JSON.stringify(request));
    });
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

async function invokeCancellable(project, overrides, onStarted) {
  const directory = mkdtempSync(resolve(tmpdir(), "wright-rivet-cancel-"));
  const projectPath = resolve(directory, "workflow.rivet-project");
  writeFileSync(projectPath, project, "utf8");
  const digest = createHash("sha256")
    .update(readFileSync(projectPath))
    .digest("hex");
  const request = {
    protocolVersion: 2,
    runId: "run-cancel",
    projectPath,
    expectedDigest: digest,
    graph: "Main",
    inputs: {},
    context: {},
    capabilities: ["mcp"],
    ...overrides,
  };
  try {
    return await new Promise((resolveResult, reject) => {
      const child = spawn(process.execPath, [runner], {
        stdio: ["pipe", "pipe", "pipe"],
      });
      let stdout = "";
      let stderr = "";
      child.stdout.setEncoding("utf8").on("data", (value) => (stdout += value));
      child.stderr.setEncoding("utf8").on("data", (value) => (stderr += value));
      child.once("error", reject);
      child.once("close", (status) =>
        resolveResult({ status, stdout, stderr }),
      );
      child.stdin.end(JSON.stringify(request));
      onStarted(child);
    });
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

async function loopbackBridge(handler) {
  const server = createServer(handler);
  await new Promise((resolveListen) =>
    server.listen(0, "127.0.0.1", resolveListen),
  );
  const address = server.address();
  return {
    baseUrl: `http://127.0.0.1:${address.port}/internal/rivet-mcp/v1`,
    close: () => new Promise((resolveClose) => server.close(resolveClose)),
  };
}

function mcpGrant(baseUrl, changes = {}) {
  return {
    authorityId: "authority-contract",
    bridgeBaseUrl: baseUrl,
    token: "ci-test-authority-token-012345678901234567890123",
    expiresAt: "2099-01-01T00:00:00Z",
    bindingSetDigest: "e".repeat(64),
    discoveryHandle: "wright-workspace",
    bindings: [
      {
        nodeId: "node-alpha",
        handle: "wright:abcdefghijklmnop",
        qualifiedToolName: "alpha__inspect",
        bindingDigest: "b".repeat(64),
      },
    ],
    ...changes,
  };
}

test("executes a deterministic graph and emits one terminal result", () => {
  const result = invoke(passthroughProject);
  assert.equal(result.status, 0, result.stderr);
  const lines = result.stdout.trim().split(/\r?\n/).map(JSON.parse);
  assert.equal(lines.at(-1).type, "result");
  assert.equal(lines.at(-1).state, "succeeded");
  assert.equal(lines.at(-1).outputs.output.value, "hello");
});

test("fails closed when the project digest changes", () => {
  const result = invoke(passthroughProject, { expectedDigest: "0".repeat(64) });
  assert.notEqual(result.status, 0);
  const terminal = result.stdout.trim().split(/\r?\n/).map(JSON.parse).at(-1);
  assert.equal(terminal.error.code, "RIVET_WORKFLOW_DIGEST_MISMATCH");
});

test("rejects unsupported protocol versions before project execution", () => {
  const result = invoke(passthroughProject, { protocolVersion: 999 });
  assert.notEqual(result.status, 0);
  const terminal = result.stdout.trim().split(/\r?\n/).map(JSON.parse).at(-1);
  assert.equal(terminal.error.code, "RIVET_RUNNER_PROTOCOL_UNSUPPORTED");
});

test("protocol v1 remains valid only for non-MCP graphs", () => {
  const project = readFileSync(
    resolve(fixtures, "valid-bound-mcp.rivet-project"),
    "utf8",
  );
  const result = invoke(project, { capabilities: ["mcp"] });
  assert.notEqual(result.status, 0);
  const terminal = result.stdout.trim().split(/\r?\n/).map(JSON.parse).at(-1);
  assert.equal(terminal.error.code, "RIVET_MCP_GRANT_REQUIRED");
});

test("protocol v2 injects the Wright provider and submits no tool namespace", async () => {
  const receipts = [];
  const bridge = await loopbackBridge((request, response) => {
    let body = "";
    request.setEncoding("utf8").on("data", (chunk) => (body += chunk));
    request.on("end", () => {
      receipts.push({
        url: request.url,
        authorization: request.headers.authorization,
        body: JSON.parse(body),
      });
      response.writeHead(200, { "Content-Type": "application/x-ndjson" });
      response.write(
        `${JSON.stringify({ type: "progress", callId: "call-1", phase: "child-progress", status: "running", progress: 0.5 })}\n`,
      );
      response.end(
        `${JSON.stringify({ type: "result", callId: "call-1", content: [{ type: "text", text: "ok" }], structuredContent: { server: "alpha", value: 2 }, isError: false, artifacts: [] })}\n`,
      );
    });
  });
  try {
    const project = readFileSync(
      resolve(fixtures, "valid-bound-mcp.rivet-project"),
      "utf8",
    )
      .replace('- response->"Output"', '- structuredContent->"Output"')
      .replace("dataType: object[]", "dataType: object");
    const result = await invokeAsync(project, {
      mcp: mcpGrant(bridge.baseUrl),
    });
    assert.equal(result.status, 0, result.stderr || result.stdout);
    assert.equal(receipts.length, 1);
    assert.equal(receipts[0].url, "/internal/rivet-mcp/v1/calls");
    assert.equal(
      receipts[0].authorization,
      `Bearer ${mcpGrant(bridge.baseUrl).token}`,
    );
    assert.equal(receipts[0].body.nodeHandle, "wright:abcdefghijklmnop");
    assert.equal(receipts[0].body.bindingDigest, "b".repeat(64));
    assert.equal(receipts[0].body.qualifiedToolName, undefined);
    assert.equal(receipts[0].body.serverId, undefined);
    const events = result.stdout.trim().split(/\r?\n/).map(JSON.parse);
    assert.equal(
      events.some((event) => event.phase === "mcp-child-progress"),
      true,
    );
    assert.equal(events.at(-1).state, "succeeded");
    assert.deepEqual(events.at(-1).outputs.output, {
      type: "object",
      value: { server: "alpha", value: 2 },
    });
    assert.equal(result.stdout.includes(mcpGrant(bridge.baseUrl).token), false);
  } finally {
    await bridge.close();
  }
});

test("MCP node diagnostics stay off the JSONL protocol channel", async () => {
  const bridge = await loopbackBridge((request, response) => {
    request.resume();
    request.on("end", () => {
      response.writeHead(200, { "Content-Type": "application/x-ndjson" });
      response.end(
        `${JSON.stringify({ type: "result", error: { code: "RIVET_MCP_PANEL_UNAVAILABLE", message: "Vendor application is not ready." } })}\n`,
      );
    });
  });
  try {
    const project = readFileSync(
      resolve(fixtures, "valid-bound-mcp.rivet-project"),
      "utf8",
    );
    const result = await invokeAsync(project, {
      mcp: mcpGrant(bridge.baseUrl),
    });
    assert.notEqual(result.status, 0);
    const events = result.stdout.trim().split(/\r?\n/).map(JSON.parse);
    assert.equal(events.at(-1).type, "result");
    assert.equal(events.at(-1).state, "failed");
    assert.equal(
      events.at(-1).error.code,
      "RIVET_MCP_PANEL_UNAVAILABLE",
    );
    assert.match(result.stderr, /Wright MCP call failed/);
    assert.match(events.at(-1).error.message, /Wright MCP call failed/);
  } finally {
    await bridge.close();
  }
});

test("protocol v2 discovers only through the reserved Wright handle", async () => {
  const receipts = [];
  const bridge = await loopbackBridge((request, response) => {
    let body = "";
    request.setEncoding("utf8").on("data", (chunk) => (body += chunk));
    request.on("end", () => {
      receipts.push({ url: request.url, body: JSON.parse(body) });
      response.writeHead(200, { "Content-Type": "application/x-ndjson" });
      response.end(
        `${JSON.stringify({ type: "result", structuredContent: { tools: [{ name: "alpha__inspect", description: "Reviewed", inputSchema: { type: "object" } }] }, isError: false })}\n`,
      );
    });
  });
  try {
    const result = await invokeAsync(discoveryProject, {
      mcp: mcpGrant(bridge.baseUrl, { bindings: [] }),
    });
    assert.equal(result.status, 0, result.stderr || result.stdout);
    assert.equal(receipts.length, 1, result.stdout);
    assert.deepEqual(receipts, [
      {
        url: "/internal/rivet-mcp/v1/discover",
        body: {
          authorityId: "authority-contract",
          runId: "run-contract",
          discoveryHandle: "wright-workspace",
          requestId: receipts[0].body.requestId,
        },
      },
    ]);
    assert.equal(result.stdout.includes(mcpGrant(bridge.baseUrl).token), false);
  } finally {
    await bridge.close();
  }
});

test("protocol v2 aborts an active provider fetch and suppresses late success", async () => {
  let childRequest;
  let receivedResolve;
  const received = new Promise((resolveReceived) => {
    receivedResolve = resolveReceived;
  });
  const bridge = await loopbackBridge((request, _response) => {
    childRequest = request;
    request.resume();
    request.on("end", receivedResolve);
  });
  try {
    const project = readFileSync(
      resolve(fixtures, "valid-bound-mcp.rivet-project"),
      "utf8",
    );
    let child;
    const resultPromise = invokeCancellable(
      project,
      { mcp: mcpGrant(bridge.baseUrl) },
      (running) => (child = running),
    );
    await received;
    child.kill("SIGINT");
    const result = await resultPromise;
    const events = result.stdout.trim().split(/\r?\n/).map(JSON.parse);
    const terminal = events.findLast((event) => event.type === "result");
    if (process.platform === "win32") {
      // Windows terminates for these POSIX signal aliases instead of
      // delivering Node's handler. The owned process still ends without
      // accepting a late result; Python records the cancel terminal.
      assert.equal(terminal, undefined);
      assert.notEqual(result.status, 0);
    } else {
      assert.equal(terminal.state, "cancelled");
      assert.equal(terminal.error.code, "RIVET_RUNNER_CANCELLED");
    }
    assert.equal(
      events.some((event) => event.state === "succeeded"),
      false,
    );
    assert.equal(result.stdout.includes(mcpGrant(bridge.baseUrl).token), false);
    assert.equal(childRequest.destroyed, true);
  } finally {
    await bridge.close();
  }
});

test("protocol v2 rejects direct child config and dynamic tool names before bridge receipt", async () => {
  let receipts = 0;
  const bridge = await loopbackBridge((_request, response) => {
    receipts += 1;
    response.writeHead(500).end();
  });
  try {
    const hostile = readFileSync(
      resolve(fixtures, "hostile-direct-config.rivet-project"),
      "utf8",
    );
    const direct = await invokeAsync(hostile, {
      mcp: mcpGrant(bridge.baseUrl),
    });
    assert.equal(
      direct.stdout.includes("RIVET_MCP_PROJECT_CONFIG_DENIED"),
      true,
    );
    const valid = readFileSync(
      resolve(fixtures, "valid-bound-mcp.rivet-project"),
      "utf8",
    );
    const dynamic = await invokeAsync(
      valid.replace("useToolNameInput: false", "useToolNameInput: true"),
      {
        mcp: mcpGrant(bridge.baseUrl),
      },
    );
    assert.equal(
      dynamic.stdout.includes("RIVET_MCP_DYNAMIC_TOOL_DENIED"),
      true,
    );
    assert.equal(receipts, 0);
  } finally {
    await bridge.close();
  }
});

test("protocol v2 rejects non-exact loopback origins and binding mismatches", async () => {
  const project = readFileSync(
    resolve(fixtures, "valid-bound-mcp.rivet-project"),
    "utf8",
  );
  const origin = await invokeAsync(project, {
    mcp: mcpGrant("http://localhost:43123/internal/rivet-mcp/v1"),
  });
  assert.equal(origin.stdout.includes("RIVET_MCP_BRIDGE_DENIED"), true);
  const mismatch = await invokeAsync(project, {
    mcp: mcpGrant("http://127.0.0.1:43123/internal/rivet-mcp/v1", {
      bindings: [
        {
          ...mcpGrant("http://127.0.0.1:43123/internal/rivet-mcp/v1")
            .bindings[0],
          qualifiedToolName: "beta__inspect",
        },
      ],
    }),
  });
  assert.equal(mismatch.stdout.includes("RIVET_MCP_BINDING_MISMATCH"), true);
});

test("protocol v2 rejects missing, extra, and secret-like binding material", async () => {
  const baseUrl = "http://127.0.0.1:43123/internal/rivet-mcp/v1";
  const project = readFileSync(
    resolve(fixtures, "valid-bound-mcp.rivet-project"),
    "utf8",
  );
  const missing = await invokeAsync(project, {
    mcp: mcpGrant(baseUrl, { bindings: [] }),
  });
  assert.equal(missing.stdout.includes("RIVET_MCP_BINDING_MISSING"), true);
  const extraBinding = {
    nodeId: "node-beta",
    handle: "wright:qrstuvwxyzabcdef",
    qualifiedToolName: "beta__inspect",
    bindingDigest: "c".repeat(64),
  };
  const extra = await invokeAsync(project, {
    mcp: mcpGrant(baseUrl, {
      bindings: [...mcpGrant(baseUrl).bindings, extraBinding],
    }),
  });
  assert.equal(extra.stdout.includes("RIVET_MCP_BINDING_EXTRA"), true);
  const secretLike = await invokeAsync(
    project.replace(
      "name: wright-rivet",
      "name: wright-rivet\n            apiKey: ci-test-must-not-cross",
    ),
    { mcp: mcpGrant(baseUrl) },
  );
  assert.equal(
    secretLike.stdout.includes("RIVET_MCP_PROJECT_CONFIG_DENIED"),
    true,
  );
  assert.equal(secretLike.stdout.includes("ci-test-must-not-cross"), false);
});

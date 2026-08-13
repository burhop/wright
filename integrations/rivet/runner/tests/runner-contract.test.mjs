import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const root = resolve(import.meta.dirname, '..');
const runner = resolve(root, 'dist', 'wright-runner.mjs');

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

function invoke(project, overrides = {}) {
  const directory = mkdtempSync(resolve(tmpdir(), 'wright-rivet-runner-'));
  try {
    const projectPath = resolve(directory, 'workflow.rivet-project');
    writeFileSync(projectPath, project, 'utf8');
    const digest = createHash('sha256').update(readFileSync(projectPath)).digest('hex');
    const request = {
      protocolVersion: 1,
      runId: 'run-contract',
      projectPath,
      expectedDigest: digest,
      graph: 'Main',
      inputs: { input: 'hello' },
      context: {},
      capabilities: [],
      ...overrides,
    };
    return spawnSync(process.execPath, [runner], {
      input: JSON.stringify(request),
      encoding: 'utf8',
      timeout: 10_000,
    });
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test('executes a deterministic graph and emits one terminal result', () => {
  const result = invoke(passthroughProject);
  assert.equal(result.status, 0, result.stderr);
  const lines = result.stdout.trim().split(/\r?\n/).map(JSON.parse);
  assert.equal(lines.at(-1).type, 'result');
  assert.equal(lines.at(-1).state, 'succeeded');
  assert.equal(lines.at(-1).outputs.output.value, 'hello');
});

test('fails closed when the project digest changes', () => {
  const result = invoke(passthroughProject, { expectedDigest: '0'.repeat(64) });
  assert.notEqual(result.status, 0);
  const terminal = result.stdout.trim().split(/\r?\n/).map(JSON.parse).at(-1);
  assert.equal(terminal.error.code, 'RIVET_WORKFLOW_DIGEST_MISMATCH');
});

test('rejects unsupported protocol versions before project execution', () => {
  const result = invoke(passthroughProject, { protocolVersion: 999 });
  assert.notEqual(result.status, 0);
  const terminal = result.stdout.trim().split(/\r?\n/).map(JSON.parse).at(-1);
  assert.equal(terminal.error.code, 'RIVET_RUNNER_PROTOCOL_UNSUPPORTED');
});

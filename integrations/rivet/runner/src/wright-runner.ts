import { createHash } from 'node:crypto';
import { isAbsolute } from 'node:path';
import { readFile } from 'node:fs/promises';

import { createProcessor, loadProjectFromFile, type Project } from '@valerypopoff/rivet2-node';

export const WRIGHT_RIVET_RUNNER_PROTOCOL = 1;
export const RIVET_SOURCE_REVISION = '4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053';
export const RIVET_PACKAGE_VERSION = '2.1.9';

const MAX_REQUEST_BYTES = 2 * 1024 * 1024;
const MAX_EVENT_BYTES = 64 * 1024;
const MAX_OUTPUT_BYTES = 1024 * 1024;
const RUN_ID_PATTERN = /^[A-Za-z0-9._:-]{1,128}$/;
const DIGEST_PATTERN = /^[a-f0-9]{64}$/;

const CAPABILITY_NODE_TYPES: Readonly<Record<string, ReadonlySet<string>>> = {
  ai: new Set([
    'chat',
    'chatAnthropic',
    'chatGoogle',
    'chatHuggingFace',
    'chatLoop',
    'llmChatV2',
    'llmProfile',
    'openaiAttachAssistantFile',
    'openaiCreateThread',
    'openaiCreateThreadMessage',
    'openaiDeleteThread',
    'openaiGetFile',
    'openaiGetThread',
    'openaiListFiles',
    'openaiListThreadMessages',
    'openaiRunThread',
    'openaiUploadFile',
  ]),
  code: new Set(['code', 'codeNew', 'externalCall']),
  dataset: new Set([
    'appendToDataset',
    'createDataset',
    'datasetNearestNeighbors',
    'datasetSelector',
    'getAllDatasets',
    'getDatasetRow',
    'loadDataset',
    'replaceDataset',
  ]),
  filesystem: new Set(['fileBrowser', 'filePathBrowser', 'readAllFiles', 'readDirectory', 'readFile']),
  interactive: new Set(['userInput']),
  mcp: new Set(['mcpDiscovery', 'mcpGetPrompt', 'mcpToolCall']),
  network: new Set(['httpCall']),
};

export type WrightRunnerRequest = {
  protocolVersion: number;
  runId: string;
  projectPath: string;
  expectedDigest: string;
  graph?: string;
  inputs?: Record<string, unknown>;
  context?: Record<string, unknown>;
  ai?: { baseUrl: string; token: string; model: string };
  capabilities?: string[];
};

type RunnerError = Error & { code?: string };

function failure(code: string, message: string): RunnerError {
  const error = new Error(message) as RunnerError;
  error.code = code;
  return error;
}

function writeEvent(event: Record<string, unknown>): void {
  const encoded = JSON.stringify(event);
  if (Buffer.byteLength(encoded, 'utf8') > MAX_EVENT_BYTES) {
    throw failure('RIVET_RUNNER_EVENT_TOO_LARGE', 'Runner event exceeded the bounded JSONL event size.');
  }
  process.stdout.write(`${encoded}\n`);
}

async function readRequest(): Promise<WrightRunnerRequest> {
  process.stdin.setEncoding('utf8');
  let raw = '';
  for await (const chunk of process.stdin) {
    raw += chunk;
    if (Buffer.byteLength(raw, 'utf8') > MAX_REQUEST_BYTES) {
      throw failure('RIVET_RUNNER_REQUEST_TOO_LARGE', 'Runner request exceeded the input limit.');
    }
  }
  let value: unknown;
  try {
    value = JSON.parse(raw);
  } catch {
    throw failure('RIVET_RUNNER_REQUEST_INVALID', 'Runner request must be one JSON object.');
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw failure('RIVET_RUNNER_REQUEST_INVALID', 'Runner request must be one JSON object.');
  }
  return value as WrightRunnerRequest;
}

function validateRequest(request: WrightRunnerRequest): void {
  if (request.protocolVersion !== WRIGHT_RIVET_RUNNER_PROTOCOL) {
    throw failure('RIVET_RUNNER_PROTOCOL_UNSUPPORTED', 'Unsupported Wright Rivet runner protocol.');
  }
  if (!RUN_ID_PATTERN.test(request.runId ?? '')) {
    throw failure('RIVET_RUNNER_REQUEST_INVALID', 'Invalid run identifier.');
  }
  if (typeof request.projectPath !== 'string' || !isAbsolute(request.projectPath)) {
    throw failure('RIVET_RUNNER_REQUEST_INVALID', 'Project path must be absolute.');
  }
  if (!DIGEST_PATTERN.test(request.expectedDigest ?? '')) {
    throw failure('RIVET_RUNNER_REQUEST_INVALID', 'Expected digest must be a lowercase SHA-256 digest.');
  }
  if (request.inputs != null && (typeof request.inputs !== 'object' || Array.isArray(request.inputs))) {
    throw failure('RIVET_RUNNER_REQUEST_INVALID', 'Inputs must be an object.');
  }
  if (request.context != null && (typeof request.context !== 'object' || Array.isArray(request.context))) {
    throw failure('RIVET_RUNNER_REQUEST_INVALID', 'Context must be an object.');
  }
}

export async function verifyProjectDigest(request: WrightRunnerRequest): Promise<string> {
  const project = await readFile(request.projectPath);
  const actual = createHash('sha256').update(project).digest('hex');
  if (actual !== request.expectedDigest) {
    throw failure('RIVET_WORKFLOW_DIGEST_MISMATCH', 'Workflow contents changed after the run was authorized.');
  }
  return project.toString('utf8');
}

function projectNodeTypes(project: Project): Set<string> {
  const types = new Set<string>();
  for (const graph of Object.values(project.graphs ?? {})) {
    const nodes = Array.isArray(graph.nodes) ? graph.nodes : Object.values(graph.nodes ?? {});
    for (const node of nodes) {
      if (node && typeof node.type === 'string') types.add(node.type);
    }
  }
  return types;
}

function enforceCapabilities(project: Project, request: WrightRunnerRequest): void {
  const granted = new Set(request.capabilities ?? []);
  if (request.ai) granted.add('ai');
  const nodeTypes = projectNodeTypes(project);
  for (const [capability, protectedTypes] of Object.entries(CAPABILITY_NODE_TYPES)) {
    const deniedType = [...nodeTypes].find((type) => protectedTypes.has(type));
    if (deniedType && !granted.has(capability)) {
      throw failure(
        'RIVET_RUNNER_CAPABILITY_DENIED',
        `Node type ${deniedType} requires the ${capability} capability.`,
      );
    }
  }
}

function installNetworkGuard(request: WrightRunnerRequest): void {
  const permittedOrigin = request.ai ? new URL(request.ai.baseUrl).origin : undefined;
  const nativeFetch = globalThis.fetch;
  globalThis.fetch = async (input: string | URL | Request, init?: RequestInit) => {
    const target = new URL(input instanceof Request ? input.url : input.toString());
    if (!permittedOrigin || target.origin !== permittedOrigin) {
      throw failure('RIVET_RUNNER_NETWORK_DENIED', 'Runner network access is restricted to the Wright AI bridge.');
    }
    let guardedInit = init;
    if (request.ai && typeof init?.body === 'string') {
      try {
        const payload = JSON.parse(init.body);
        if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
          guardedInit = { ...init, body: JSON.stringify({ ...payload, model: request.ai.model }) };
        }
      } catch {
        throw failure('RIVET_RUNNER_AI_REQUEST_INVALID', 'AI request body must be JSON.');
      }
    }
    return nativeFetch(input, guardedInit);
  };
}

function nodeLabel(event: any): Record<string, unknown> {
  return {
    nodeId: event?.node?.id,
    nodeType: event?.node?.type,
    nodeTitle: event?.node?.title,
  };
}

async function execute(request: WrightRunnerRequest): Promise<void> {
  validateRequest(request);
  await verifyProjectDigest(request);
  const project = await loadProjectFromFile(request.projectPath);
  enforceCapabilities(project, request);
  installNetworkGuard(request);

  const abortController = new AbortController();
  const abort = () => abortController.abort(failure('RIVET_RUNNER_CANCELLED', 'Workflow run was cancelled.'));
  process.once('SIGINT', abort);
  process.once('SIGTERM', abort);

  writeEvent({ type: 'progress', runId: request.runId, state: 'running', phase: 'graph-starting' });
  const processor = createProcessor(project, {
    graph: request.graph,
    inputs: request.inputs ?? {},
    context: request.context ?? {},
    projectPath: request.projectPath,
    abortSignal: abortController.signal,
    openAiApiKey: request.ai?.token ?? '',
    customAiApiKey: request.ai?.token ?? '',
    openAiEndpoint: request.ai ? `${request.ai.baseUrl.replace(/\/$/, '')}/chat/completions` : '',
    getChatNodeEndpoint: request.ai
      ? async () => ({
          endpoint: `${request.ai!.baseUrl.replace(/\/$/, '')}/chat/completions`,
          headers: { Authorization: `Bearer ${request.ai!.token}` },
        })
      : undefined,
    onNodeStart: (event) =>
      writeEvent({ type: 'progress', runId: request.runId, state: 'running', phase: 'node-start', ...nodeLabel(event) }),
    onNodeFinish: (event) =>
      writeEvent({ type: 'progress', runId: request.runId, state: 'running', phase: 'node-finish', ...nodeLabel(event) }),
    onNodeError: (event) =>
      writeEvent({ type: 'progress', runId: request.runId, state: 'running', phase: 'node-error', ...nodeLabel(event) }),
  });

  try {
    const outputs = await processor.run();
    const terminal = { type: 'result', runId: request.runId, state: 'succeeded', outputs };
    if (Buffer.byteLength(JSON.stringify(terminal), 'utf8') > MAX_OUTPUT_BYTES) {
      throw failure('RIVET_RUNNER_OUTPUT_TOO_LARGE', 'Workflow output exceeded the configured limit.');
    }
    writeEvent(terminal);
  } finally {
    processor.dispose();
    process.removeListener('SIGINT', abort);
    process.removeListener('SIGTERM', abort);
  }
}

async function main(): Promise<void> {
  let runId: string | undefined;
  try {
    const request = await readRequest();
    runId = request.runId;
    await execute(request);
  } catch (caught) {
    const error = caught as RunnerError;
    const code = error.code ?? (error.name === 'AbortError' ? 'RIVET_RUNNER_CANCELLED' : 'RIVET_RUNNER_FAILED');
    const event = {
      type: 'result',
      runId,
      state: code === 'RIVET_RUNNER_CANCELLED' ? 'cancelled' : 'failed',
      error: { code, message: error.message || 'Rivet workflow execution failed.' },
    };
    try {
      writeEvent(event);
    } catch {
      process.stdout.write(
        `${JSON.stringify({ type: 'result', runId, state: 'failed', error: { code: 'RIVET_RUNNER_FAILED', message: 'Runner failure.' } })}\n`,
      );
    }
    process.exitCode = 1;
  }
}

void main();

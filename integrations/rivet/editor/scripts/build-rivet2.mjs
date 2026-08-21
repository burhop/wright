import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs';
import { dirname, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repository = 'https://github.com/valerypopoff/rivet2.0.git';
const revision = '4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053';
const packageName = '@valerypopoff/rivet-app';
const packageVersion = '2.8.9';
const editorRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const defaultCheckout = resolve(editorRoot, '..', 'spike', '.work', 'rivet2');
const checkout = resolve(process.env.WRIGHT_RIVET2_CHECKOUT || defaultCheckout);
const patchPaths = [
  resolve(editorRoot, 'patches', 'rivet2-canvas-only.patch'),
  resolve(editorRoot, 'patches', 'rivet2-graph-builder-recovery.patch'),
  resolve(editorRoot, 'patches', 'rivet2-legacy-node-catalog.patch'),
  resolve(editorRoot, 'patches', 'rivet2-atomic-workflow-plan.patch'),
  resolve(editorRoot, 'patches', 'rivet2-composition-adapters.patch'),
  resolve(editorRoot, 'patches', 'rivet2-mcp-structured-content.patch'),
  resolve(editorRoot, 'patches', 'rivet2-run-state-overlay.patch'),
];
const wrappers = ['App.tsx', 'WrightAiRuntime.ts', 'WrightEditorBridge.tsx', 'index.html'];
const output = resolve(editorRoot, 'dist');

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd,
    encoding: 'utf8',
    env: { ...process.env, ...options.env },
    stdio: options.capture ? 'pipe' : 'inherit',
  });
  if (result.status !== 0) {
    const detail = options.capture ? `\n${result.stderr || result.stdout}` : '';
    throw new Error(`${command} ${args.join(' ')} failed with status ${result.status}${detail}`);
  }
  return (result.stdout || '').trimEnd();
}

function sha256(input) {
  return createHash('sha256').update(input).digest('hex');
}

function sha256File(path) {
  return sha256(readFileSync(path));
}

function canonicalizePinnedTextInput(path) {
  const content = readFileSync(path, 'utf8');
  const canonical = content.replace(/\r\n?/g, '\n');
  if (canonical !== content) {
    writeFileWithRetry(path, canonical);
  }
}

function writeFileWithRetry(path, content) {
  let lastError;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      writeFileSync(path, content, 'utf8');
      return;
    } catch (error) {
      lastError = error;
      if (!['EBUSY', 'EPERM', 'UNKNOWN'].includes(error?.code)) {
        throw error;
      }
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 250);
    }
  }
  throw lastError;
}

function walkFiles(directory) {
  return readdirSync(directory, { withFileTypes: true })
    .flatMap((entry) => {
      const path = resolve(directory, entry.name);
      return entry.isDirectory() ? walkFiles(path) : [path];
    })
    .sort((left, right) => left.localeCompare(right));
}

for (const path of [
  ...patchPaths,
  ...wrappers.map((name) => resolve(editorRoot, 'wrapper', name)),
]) {
  canonicalizePinnedTextInput(path);
}

if (!existsSync(resolve(checkout, '.git'))) {
  throw new Error('Pinned checkout is missing. Run acquire-rivet2.mjs first.');
}
const actualRevision = run('git', ['rev-parse', 'HEAD'], { cwd: checkout, capture: true });
if (actualRevision !== revision) {
  throw new Error(`Expected Rivet 2 ${revision}, received ${actualRevision}`);
}
const dirty = run('git', ['status', '--porcelain'], { cwd: checkout, capture: true });
const expectedChangedPaths = new Set([
  'packages/app/index.html',
  'packages/app/src/App.tsx',
  'packages/app/src/WrightEditorBridge.tsx',
  'packages/app/src/WrightAiRuntime.ts',
  'packages/app/src/components/RivetApp.tsx',
  'packages/app/src/components/RivetAppHostLifecycle.tsx',
  'packages/app/src/components/RivetAppLoader.tsx',
  'packages/app/graphs/graph-creator.rivet-project',
  'packages/app/src/features/graphBuilder/authoringCatalog.ts',
  'packages/app/src/features/graphBuilder/legacyDraftRunner.test.ts',
  'packages/app/src/features/graphBuilder/legacyDraftRunner.ts',
  'packages/app/src/hooks/aiGraphBuilderHelpers.test.ts',
  'packages/app/src/hooks/aiGraphBuilderHelpers.ts',
  'packages/app/src/hooks/legacyGraphBuilderLogging.test.ts',
  'packages/app/src/hooks/legacyGraphBuilderLogging.ts',
  'packages/app/src/hooks/useAiGraphBuilder.ts',
  'packages/app/src/hooks/useRivetWorkspaceHost.ts',
  'packages/app/src/hooks/workspaceHost/types.ts',
  'packages/app/src/providers/HostCallbacksContext.tsx',
  'packages/app/src/providers/HostUiConfigContext.tsx',
  'packages/app/src/components/VisualNode.tsx',
  'packages/app/src/state/graphBuilder.ts',
  'packages/core/src/integrations/mcp/MCPProvider.ts',
  'packages/core/src/model/nodes/MCPToolCallNode.ts',
  'packages/core/test/integrations/mcp/MCPBase.test.ts',
  'packages/node/src/native/NodeMCPProvider.ts',
  'packages/node/test/nodeMcpProvider.test.ts',
]);
const wrapperTargets = new Map([
  ['App.tsx', resolve(checkout, 'packages', 'app', 'src', 'App.tsx')],
  ['WrightEditorBridge.tsx', resolve(checkout, 'packages', 'app', 'src', 'WrightEditorBridge.tsx')],
  ['WrightAiRuntime.ts', resolve(checkout, 'packages', 'app', 'src', 'WrightAiRuntime.ts')],
  ['index.html', resolve(checkout, 'packages', 'app', 'index.html')],
]);

if (dirty) {
  const changedPaths = dirty
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => line.slice(3).replaceAll('\\', '/'));
  const onlyExpectedPaths = changedPaths.every((path) => expectedChangedPaths.has(path));
  const patchesAreApplied = patchPaths.every(
    (patchPath) =>
      spawnSync('git', ['apply', '--reverse', '--check', patchPath], {
        cwd: checkout,
        stdio: 'ignore',
      }).status === 0,
  );
  if (!onlyExpectedPaths || !patchesAreApplied) {
    throw new Error(
      'Pinned checkout contains changes other than the reviewed Wright patch surface. Use a fresh ignored checkout.',
    );
  }
  for (const [name, target] of wrapperTargets) {
    cpSync(resolve(editorRoot, 'wrapper', name), target);
  }
} else {
  for (const patchPath of patchPaths) {
    run('git', ['apply', '--check', patchPath], { cwd: checkout });
    run('git', ['apply', patchPath], { cwd: checkout });
  }
  for (const [name, target] of wrapperTargets) {
    cpSync(resolve(editorRoot, 'wrapper', name), target);
  }
}

const yarn = resolve(checkout, '.yarn', 'releases', 'yarn-4.17.1.cjs');
run(process.execPath, [yarn, 'install', '--immutable'], { cwd: checkout });
for (const dependency of ['@valerypopoff/rivet2-core', '@valerypopoff/trivet']) {
  run(process.execPath, ['--max-old-space-size=8192', yarn, 'workspace', dependency, 'run', 'build'], {
    cwd: checkout,
  });
}
run(
  process.execPath,
  [
    '--max-old-space-size=8192',
    yarn,
    'workspace',
    packageName,
    'run',
    'build',
  ],
  { cwd: checkout },
);

const builtOutput = resolve(checkout, 'packages', 'app', 'dist');
if (!existsSync(resolve(builtOutput, 'index.html'))) {
  throw new Error('Rivet 2 build did not produce packages/app/dist/index.html');
}
const resolvedOutput = resolve(output);
if (resolvedOutput !== resolve(editorRoot, 'dist')) {
  throw new Error(`Refusing to replace unexpected artifact path: ${resolvedOutput}`);
}
rmSync(resolvedOutput, { recursive: true, force: true });
mkdirSync(resolvedOutput, { recursive: true });
cpSync(builtOutput, resolvedOutput, { recursive: true });

const publicAssetPattern = /https?:\/\/(?:fonts\.(?:googleapis|gstatic)\.com|cdn\.|unpkg\.|jsdelivr\.)/i;
const files = walkFiles(resolvedOutput).map((path) => {
  const artifactPath = `dist/${relative(resolvedOutput, path).replaceAll('\\', '/')}`;
  const content = readFileSync(path);
  if (publicAssetPattern.test(content.toString('utf8'))) {
    throw new Error(`Public editor asset reference remains in ${artifactPath}`);
  }
  return {
    path: artifactPath,
    bytes: statSync(path).size,
    sha256: sha256(content),
  };
});
const treeInput = files.map((file) => `${file.sha256}  ${file.path}\n`).join('');
const entrypoint = 'dist/index.html';
const manifest = {
  schema_version: 2,
  editor: 'rivet2-canvas',
  rivet_version: packageVersion,
  source: {
    repository,
    revision,
    package: packageName,
    package_version: packageVersion,
  },
  patches: patchPaths.map((patchPath) => ({
    path: `patches/${relative(resolve(editorRoot, 'patches'), patchPath).replaceAll('\\', '/')}`,
    sha256: sha256File(patchPath),
  })),
  wrapper: wrappers.map((name) => ({
    path: `wrapper/${name}`,
    sha256: sha256File(resolve(editorRoot, 'wrapper', name)),
  })),
  entrypoint,
  sha256: sha256File(resolve(editorRoot, entrypoint)),
  tree_sha256: sha256(treeInput),
  files,
  license: 'MIT',
  runtime_network_policy: 'local-only',
};
writeFileWithRetry(resolve(editorRoot, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
process.stdout.write(
  `${JSON.stringify({ files: files.length, output, revision, tree_sha256: manifest.tree_sha256 })}\n`,
);

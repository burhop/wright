// Wright-owned compiler. No generated configuration, package scripts or plugins.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const diagnostics = [];
const add = message => { if (diagnostics.length < 64) diagnostics.push(String(message).slice(0, 2000)); };
try {
  const request = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const root = path.resolve(request.root);
  const requireInstalled = createRequire(path.join(request.dependencyRoot, 'package.json'));
  const ts = requireInstalled('typescript');
  const aliases = {
    '@wright/process-client': path.join(request.clientRoot, 'src/index.ts'),
    '@wright/ui-kit': path.join(request.kitRoot, 'src/index.ts'),
  };
  for (const [name, expected] of Object.entries(request.packages)) {
    const packageRoot = name === '@wright/process-client' ? request.clientRoot :
      name === '@wright/ui-kit' ? request.kitRoot : path.join(request.dependencyRoot, 'node_modules', name);
    const actual = JSON.parse(fs.readFileSync(path.join(packageRoot, 'package.json'), 'utf8'));
    if (actual.name !== name || actual.version !== expected.version) throw new Error('Installed compiler package identity changed.');
  }
  const allowedImports = new Set(['react', '@wright/process-client', '@wright/ui-kit', './style.css']);
  const forbiddenNames = new Set(['eval', 'Function', 'require', 'fetch', 'XMLHttpRequest', 'WebSocket', 'Worker', 'SharedWorker', 'importScripts']);
  const appPath = path.join(root, 'App.tsx');
  const source = ts.createSourceFile(appPath, fs.readFileSync(appPath, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  for (const diagnostic of source.parseDiagnostics) add(ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n'));
  function inspect(node) {
    if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) {
      if (node.moduleSpecifier) {
        const specifier = ts.isStringLiteral(node.moduleSpecifier) ? node.moduleSpecifier.text : '';
        if (!allowedImports.has(specifier)) add(`Import is outside the public interface allowlist: ${specifier}`);
      }
    }
    if ((ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) ||
        ts.isImportEqualsDeclaration(node)) add('Dynamic or require-style imports are unsupported.');
    if (ts.isIdentifier(node) && forbiddenNames.has(node.text)) add(`Use the scoped host client instead of ${node.text}.`);
    if (ts.isStringLiteralLike(node) && /^(?:https?:|wss?:|ftp:|file:|javascript:|data:|\/\/)/i.test(node.text.trim()))
      add('External URLs and inline executable/data URLs are unsupported.');
    ts.forEachChild(node, inspect);
  }
  inspect(source);
  const cssPath = path.join(root, 'style.css');
  if (fs.existsSync(cssPath)) {
    const postcss = requireInstalled('postcss');
    const css = postcss.parse(fs.readFileSync(cssPath, 'utf8'), { from: cssPath });
    css.walkAtRules(rule => { if (rule.name.toLowerCase() === 'import') add('CSS imports are unsupported.'); });
    css.walkDecls(decl => {
      if (/expression\s*\(|javascript\s*:|behavior\s*:|-moz-binding/i.test(`${decl.prop}:${decl.value}`)) add('Executable CSS constructs are unsupported.');
      for (const match of decl.value.matchAll(/url\s*\(\s*(['"]?)(.*?)\1\s*\)/gi)) {
        const relative = match[2].replace(/^\.\//, '');
        if (!request.assets.includes(relative)) add('CSS URLs must name a supplied local raster asset.');
      }
    });
  }
  const entry = path.join(root, 'wright-entry.tsx');
  fs.writeFileSync(entry, `import {createRoot} from 'react-dom/client';
import type {ComponentType} from 'react';
import {createPresentationProcessClient} from '@wright/process-client';
import type {ProcessClient, InteractionSnapshot, PresentationClientPorts} from '@wright/process-client';
import App from './App';
interface HostProps { client: ProcessClient; snapshot: InteractionSnapshot; readOnly: boolean; }
const CheckedApp: ComponentType<HostProps> = App;
export function createPresentationClient(context: unknown, ports?: Omit<PresentationClientPorts, 'fetch'>) {
  return createPresentationProcessClient(context, {...ports, fetch: (input, init) => globalThis.fetch(input, init)});
}
export function mount(node: Element, props: HostProps) {
  const root = createRoot(node);
  root.render(<CheckedApp {...props}/>);
  const dispose = () => root.unmount();
  dispose.update = (snapshot: InteractionSnapshot) => root.render(<CheckedApp {...props} snapshot={snapshot}/>);
  return dispose;
}
`);
  if (!diagnostics.length) {
    const options = {
      target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext,
      moduleResolution: ts.ModuleResolutionKind.Bundler, jsx: ts.JsxEmit.ReactJSX,
      strict: true, skipLibCheck: true, noEmit: true, esModuleInterop: true,
      allowSyntheticDefaultImports: true, resolveJsonModule: true,
    };
    const host = ts.createCompilerHost(options);
    host.resolveModuleNames = (names, containingFile) => names.map(name => {
      if (aliases[name]) return { resolvedFileName: aliases[name], extension: ts.Extension.Ts, isExternalLibraryImport: true };
      return ts.resolveModuleName(name, containingFile, options, host).resolvedModule ||
        ts.resolveModuleName(name, path.join(request.dependencyRoot, '__wright__.tsx'), options, host).resolvedModule;
    });
    const assetDeclarations = path.join(root, 'wright-assets.d.ts');
    fs.writeFileSync(assetDeclarations, "declare module '*.css';\n");
    const program = ts.createProgram([appPath, assetDeclarations, entry], options, host);
    for (const diagnostic of ts.getPreEmitDiagnostics(program)) {
      const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
      const location = diagnostic.file && diagnostic.start !== undefined ? diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start) : null;
      add(location ? `${path.basename(diagnostic.file.fileName)}:${location.line + 1}:${location.character + 1}: ${message}` : message);
    }
  }
  if (!diagnostics.length) {
    // The model supplies App only; mounting is an explicit call by the managed host.
    const viteModule = path.join(request.dependencyRoot, 'node_modules/vite/dist/node/index.js');
    const { build } = await import(pathToFileURL(viteModule).href);
    await build({
      root, configFile: false, envFile: false, plugins: [], logLevel: 'silent',
      publicDir: false, resolve: { alias: [
        ...Object.entries(aliases).map(([find, replacement]) => ({ find, replacement })),
        {find: /^react$/, replacement: requireInstalled.resolve('react')},
        {find: /^react\/jsx-runtime$/, replacement: requireInstalled.resolve('react/jsx-runtime')},
        {find: /^react-dom\/client$/, replacement: requireInstalled.resolve('react-dom/client')},
      ] },
      build: {
        outDir: path.join(root, 'dist'), emptyOutDir: false, sourcemap: false,
        lib: { entry, formats: ['es'], fileName: () => 'app.js', cssFileName: 'style' },
      },
    });
    const assets = path.join(root, 'dist/assets');
    for (const asset of request.assets) {
      fs.mkdirSync(assets, { recursive: true });
      const target = path.join(root, 'dist', asset);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(path.join(root, asset), target);
    }
  }
} catch (error) {
  add(error?.message || 'The fixed compiler failed.');
}
process.stdout.write(JSON.stringify({ ok: diagnostics.length === 0, diagnostics }));
process.exitCode = diagnostics.length ? 1 : 0;

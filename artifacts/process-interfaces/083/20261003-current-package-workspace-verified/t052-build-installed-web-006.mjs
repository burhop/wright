import { build } from 'vite';
import { existsSync } from 'node:fs';

const output = 'D:/repos/wright/.local-run/process-interfaces-083/t052-installed-web-006';
if (existsSync(output)) throw new Error('Fresh installed frontend output required');
process.env.VITE_WRIGHT_WORKFLOW_RECOVERY = '1';
process.env.VITE_WRIGHT_WORKFLOW_COMPOSER = '1';
process.env.VITE_WRIGHT_PROCESS_DEFINITION_VIEW = '1';
await build({
  root: 'D:/repos/wright/apps/web',
  cacheDir: 'D:/repos/wright/.local-run/process-interfaces-083/t052-installed-web-cache-006',
  build: { outDir: output, emptyOutDir: false, sourcemap: false },
});
console.log('Fresh production frontend compiled for private installed qualification only.');

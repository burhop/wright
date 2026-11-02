// Build only the reporting viewer, using the repository's existing dependencies.
import { build } from 'vite';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
await build({
  configFile: false,
  root,
  oxc: { jsx: { runtime: 'automatic' } },
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    outDir: path.join(root, 'artifacts/first-contact/golden-hour-tracking'),
    emptyOutDir: false,
    lib: {
      entry: path.join(root, 'scripts/synthetic_beta_testing/assets/evidence-viewer.ts'),
      formats: ['es'],
      fileName: () => 'evidence-viewer.js',
    },
  },
});

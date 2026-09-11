import { build } from "vite";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repository = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
const requireWeb = createRequire(
  path.join(repository, "apps/web/package.json"),
);
const { default: react } = await import(
  pathToFileURL(requireWeb.resolve("@vitejs/plugin-react")).href
);
await build({
  configFile: false,
  root: path.join(repository, "apps/web"),
  base: "/metrics/",
  publicDir: false,
  plugins: [react()],
  build: {
    outDir: path.join(repository, "tmp/development-dashboard/assets"),
    emptyOutDir: true,
    rollupOptions: {
      input: path.join(repository, "apps/web/development-metrics.html"),
    },
  },
});

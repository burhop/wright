// Local packaging with existing Vite/React. No server or publication pipeline.
import { build } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";
import { writeFileSync } from "node:fs";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const result = await build({
  configFile: false,
  root: resolve(repository, "apps/web"),
  plugins: [react()],
  define: { "import.meta.url": "undefined", "import.meta.resolve": "undefined" },
  build: {
    write: false,
    minify: true,
    modulePreload: false,
    rollupOptions: {
      input: resolve(repository, "apps/web/src/prototypes/desktop-panel/native-entry.tsx"),
      output: { format: "iife", name: "WrightNativeEditor", codeSplitting: false },
    },
  },
});
const output = Array.isArray(result) ? result.flatMap(item => item.output) : result.output;
const unexpected = output.filter(item =>
  item.type === "asset" ? !item.fileName.endsWith(".css") : item.imports.length || item.dynamicImports.some(name => name !== item.fileName) || /\bimport\s*\(/.test(item.code),
);
if (unexpected.length) throw new Error("Native resource has external dependencies: " + unexpected.map(item => item.fileName).join(","));
const script = output.filter(item => item.type === "chunk").map(item => item.code.replace(/^[ \t]+$/gm, "")).join("\n").replace(/<\/script/gi, "<\\/script");
const style = output.filter(item => item.type === "asset").map(item => String(item.source).replace(/^[ \t]+$/gm, "")).join("\n").replace(/<\/style/gi, "<\\/style");
const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wright Workflows</title><style>html,body{margin:0;height:100%;}#notice:empty{display:none}#notice{padding:12px;font:14px system-ui}#editor{height:100%;}${style}</style></head><body><p id="notice" role="status">Connecting to the desktop host…</p><div id="editor"></div><script>${script}</script></body></html>`;
writeFileSync(resolve(repository, "prototypes/desktop-harness/native-editor.html"), html);
console.log(JSON.stringify({ resource: "native-editor.html", bytes: Buffer.byteLength(html), external_assets: 0 }));

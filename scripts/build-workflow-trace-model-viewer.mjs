import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { rolldown } from "rolldown";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const portable = resolve(
  root,
  "packages/workspace_service/src/workspace_service/workflow_trace/portable",
);
const bundle = await rolldown({
  input: resolve(portable, "stl-viewer-entry.js"),
  platform: "browser",
});
try {
  const { output } = await bundle.generate({ format: "iife", minify: true });
  await writeFile(
    resolve(portable, "stl-viewer.js"),
    output.find((item) => item.type === "chunk").code,
  );
} finally {
  await bundle.close();
}
const three = dirname(dirname(fileURLToPath(import.meta.resolve("three"))));
await writeFile(
  resolve(portable, "THREE-LICENSE.txt"),
  await readFile(resolve(three, "LICENSE")),
);
console.log("Built offline geometry viewer.");

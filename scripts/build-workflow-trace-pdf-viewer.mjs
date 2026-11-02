import { readFile, readdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { rolldown } from "rolldown";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const portable = resolve(
  root,
  "packages/workspace_service/src/workspace_service/workflow_trace/portable",
);
const pdfRoot = dirname(
  fileURLToPath(import.meta.resolve("pdfjs-dist/package.json")),
);
const assets = {};
for (const [kind, directory, suffix] of [
  ["cMapUrl", "cmaps", ".bcmap"],
  ["standardFontDataUrl", "standard_fonts", null],
]) {
  for (const name of await readdir(resolve(pdfRoot, directory))) {
    if (suffix ? !name.endsWith(suffix) : !/\.(pfb|ttf)$/.test(name)) continue;
    assets[`${kind}/${name}`] = (
      await readFile(resolve(pdfRoot, directory, name))
    ).toString("base64");
  }
}
async function compile(name) {
  const bundle = await rolldown({
    input: resolve(portable, name),
    platform: "browser",
    transform: { define: { "import.meta": "{}" } },
  });
  try {
    const { output } = await bundle.generate({
      format: "iife",
      minify: true,
      name: "WrightPDFWorker",
    });
    const chunk = output.find((item) => item.type === "chunk");
    if (name === "document-viewer-entry.js") {
      const packages = new Set();
      const notices = [];
      for (const moduleId of chunk.moduleIds) {
        if (!moduleId.includes("node_modules/")) continue;
        let directory = dirname(moduleId);
        while (directory.includes("node_modules/")) {
          try {
            const info = JSON.parse(
              await readFile(resolve(directory, "package.json"), "utf8"),
            );
            if (!packages.has(directory)) {
              packages.add(directory);
              const license = (await readdir(directory)).find((file) =>
                /^licen[sc]e(?:\.|$)/i.test(file),
              );
              if (!license) throw new Error(`Missing license for ${info.name}`);
              notices.push(
                `${info.name} ${info.version}\n${await readFile(resolve(directory, license), "utf8")}`,
              );
            }
            break;
          } catch (error) {
            if (error.code !== "ENOENT") throw error;
          }
          directory = dirname(directory);
        }
      }
      await writeFile(
        resolve(portable, "DOCUMENT-LICENSES.txt"),
        notices.sort().join("\n\n"),
      );
    }
    return chunk.code;
  } finally {
    await bundle.close();
  }
}
const literal = (value) => JSON.stringify(value).replaceAll("<", "\\u003c");
// Classic workers also start from a file-origin report; module workers do not.
const worker = await compile(resolve(pdfRoot, "build/pdf.worker.min.mjs"));
const code = `/* PDF.js 6.3.289, Apache-2.0. See PDFJS-LICENSE.txt. */\nwindow.WrightPDFAssets=${literal(assets)};\nwindow.WrightPDFWorkerSource=${literal(worker)};\n${await compile("pdf-viewer-entry.js")}`;
await writeFile(resolve(portable, "pdf-viewer.js"), code);
await writeFile(
  resolve(portable, "PDFJS-LICENSE.txt"),
  await readFile(resolve(pdfRoot, "LICENSE")),
);
for (const directory of ["cmaps", "standard_fonts"]) {
  const licenses = (await readdir(resolve(pdfRoot, directory))).filter((name) =>
    /LICENSE/.test(name),
  );
  for (const name of licenses)
    await writeFile(
      resolve(portable, `PDFJS-${directory}-${name}.txt`),
      await readFile(resolve(pdfRoot, directory, name)),
    );
}
console.log(`Built offline PDF viewer (${code.length} characters).`);
await writeFile(
  resolve(portable, "document-viewer.js"),
  await compile("document-viewer-entry.js"),
);

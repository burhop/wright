// Raster upload companions for original, code-authored engineering diagrams.
import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import crypto from "node:crypto";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const root = path.join(repo, "tests/datasets/engineering-workflows/scenarios");
const verify = process.argv.includes("--verify-lineage");
const lineageIndex = process.argv.indexOf("--lineage-root");
const lineageRoot = path.resolve(lineageIndex >= 0 ? process.argv[lineageIndex + 1] : path.join(repo, ".local-run/feature-081-live/image-normalization-lineage"));
const sha = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const operationSha = sha(await fs.readFile(fileURLToPath(import.meta.url)));
const browser = await chromium.launch({ headless: true });
let rendered = 0;
try {
  const page = await browser.newPage({ viewport: { width: 1500, height: 1100 }, deviceScaleFactor: 1 });
  // Diagrams are self-contained. Prevent an accidental external asset dependency.
  await page.route("http://**/*", route => route.abort());
  await page.route("https://**/*", route => route.abort());
  for (const template of await fs.readdir(root, { withFileTypes: true })) {
    if (!template.isDirectory()) continue;
    for (const scenario of await fs.readdir(path.join(root, template.name), { withFileTypes: true })) {
      if (!scenario.isDirectory()) continue;
      const directory = path.join(root, template.name, scenario.name);
      const manifestPath = path.join(directory, "scenario.json");
      const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
      let changed = false;
      for (const image of [...manifest.files.images]) {
        if (!image.endsWith(".svg")) continue;
        const source = path.resolve(directory, image);
        if (!source.startsWith(directory + path.sep)) throw new Error("Image path escapes scenario");
        const target = image.slice(0, -4) + ".png";
        const svg = await fs.readFile(source, "utf8");
        await page.setContent('<html><body style="margin:0;background:white">' + svg + "</body></html>");
        const png = await page.locator("svg").first().screenshot();
        const existing = verify ? await fs.readFile(path.join(directory, target)) : null;
        if (!verify) await fs.writeFile(path.join(directory, target), png);
        const receipt = {
          schema_version: 1, operation: "wright.svg-rasterization.v1",
          observation_kind: verify ? "reproduced_now_compared_existing" : "rendered_now",
          observed_at: new Date().toISOString(), historical_execution_claim: false,
          scenario_id: manifest.scenario_id, source: image, source_sha256: sha(Buffer.from(svg, "utf8")),
          output: target, output_sha256: sha(existing ?? png), reproduced_sha256: sha(png),
          matches: !verify || sha(existing) === sha(png), operation_sha256: operationSha,
          renderer: { engine: "chromium", version: browser.version(), deviceScaleFactor: 1,
            viewport: { width: 1500, height: 1100 }, network: "http_https_blocked" }
        };
        const receipts = path.join(lineageRoot, manifest.scenario_id);
        await fs.mkdir(receipts, { recursive: true });
        const receiptPath = path.join(receipts, sha(Buffer.from(svg, "utf8")) + "-" + sha(existing ?? png) + ".json");
        try { await fs.writeFile(receiptPath, JSON.stringify(receipt, null, 2) + "\n", { flag: "wx" }); }
        catch (error) { if (error.code !== "EEXIST") throw error; }
        rendered++;
        if (!verify && !manifest.files.images.includes(target)) {
          manifest.files.images.push(target);
          changed = true;
        }
      }
      if (changed) {
        const next = manifestPath + ".next";
        await fs.writeFile(next, JSON.stringify(manifest, null, 2) + "\n");
        await fs.rename(next, manifestPath);
      }
    }
  }
  console.log(JSON.stringify({ rendered, root }));
} finally {
  await browser.close();
}

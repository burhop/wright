import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { readdir, stat } from "node:fs/promises";
import { resolve } from "node:path";
import { readBaseline, spikeRoot, writeEvidence } from "./evidence.mjs";

const baseline = await readBaseline();
const upstream = resolve(spikeRoot, ".work", "rivet");
const yarn = resolve(upstream, ".yarn", "releases", "yarn-4.17.1.cjs");
if (!existsSync(yarn)) throw new Error("Pinned Rivet source and bundled Yarn are required; run spike:acquire first.");

const allowNetwork = process.env.SPIKE_ALLOW_NETWORK === "1";
const buildEnvironment = { ...process.env, YARN_ENABLE_NETWORK: allowNetwork ? "1" : "0" };
try {
  execFileSync(process.execPath, [yarn, "install", "--immutable", ...(allowNetwork ? [] : ["--immutable-cache"]), "--mode=skip-build"], {
    cwd: upstream,
    env: buildEnvironment,
    stdio: "inherit"
  });
  for (const workspace of ["@valerypopoff/rivet2-core", "@valerypopoff/trivet", "@valerypopoff/rivet-app"]) {
    execFileSync(process.execPath, [yarn, "workspace", workspace, "run", "build"], {
      cwd: upstream,
      env: buildEnvironment,
      stdio: "inherit"
    });
  }
} catch (error) {
  const { target } = await writeEvidence("build", "blocked", {
    sourceRevision: baseline.sourceRevision,
    networkPolicy: allowNetwork ? "network enabled for diagnostic build" : "YARN_ENABLE_NETWORK=0",
    message: error instanceof Error ? error.message : String(error)
  });
  console.error(target);
  process.exitCode = 1;
  process.exit(1);
}

const dist = resolve(upstream, "packages", "app", "dist");
if (!existsSync(dist)) throw new Error("Rivet editor build produced no dist directory.");
const entries = await readdir(dist, { recursive: true });
let byteCount = 0;
for (const entry of entries) {
  const target = resolve(dist, entry);
  if ((await stat(target)).isFile()) byteCount += (await stat(target)).size;
}
const { target } = await writeEvidence("build", "passed", {
  sourceRevision: baseline.sourceRevision,
  dist,
  assetCount: entries.length,
  byteCount,
  networkPolicy: allowNetwork ? "network enabled for diagnostic build" : "YARN_ENABLE_NETWORK=0"
});
console.log(target);

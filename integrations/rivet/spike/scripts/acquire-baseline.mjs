import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { baselinePath, digestFile, readBaseline, spikeRoot, writeEvidence } from "./evidence.mjs";

const baseline = await readBaseline();
const workRoot = resolve(spikeRoot, ".work");
const upstream = resolve(workRoot, "rivet");
await mkdir(workRoot, { recursive: true });

if (!existsSync(resolve(upstream, ".git"))) {
  execFileSync("git", ["clone", "--filter=blob:none", "--no-checkout", baseline.sourceRepository, upstream], { stdio: "inherit" });
}
execFileSync("git", ["-C", upstream, "fetch", "--tags", "--force", "origin", baseline.sourceRevision], { stdio: "inherit" });
execFileSync("git", ["-C", upstream, "checkout", "--detach", baseline.sourceRevision], { stdio: "inherit" });
const revision = execFileSync("git", ["-C", upstream, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
if (revision !== baseline.sourceRevision) {
  throw new Error(`Immutable source mismatch: expected ${baseline.sourceRevision}, got ${revision}`);
}

const lockfile = resolve(upstream, "yarn.lock");
const packageFile = resolve(upstream, "package.json");
const { target } = await writeEvidence("acquire", "passed", {
  sourceRevision: revision,
  baselineDigest: await digestFile(baselinePath),
  lockfileDigest: await digestFile(lockfile),
  packageDigest: await digestFile(packageFile),
  upstream
});
console.log(target);

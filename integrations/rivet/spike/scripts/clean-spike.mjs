import { rm } from "node:fs/promises";
import { resolve } from "node:path";
import { reportsRoot, spikeRoot, writeEvidence } from "./evidence.mjs";

const generatedRoots = [resolve(spikeRoot, ".work"), resolve(spikeRoot, "node_modules"), reportsRoot];
for (const target of generatedRoots) {
  if (!target.startsWith(spikeRoot)) throw new Error(`Refusing to clean outside spike root: ${target}`);
  await rm(target, { recursive: true, force: true });
}
await writeEvidence("cleanup", "passed", { removed: generatedRoots });
console.log("Spike generated content removed.");

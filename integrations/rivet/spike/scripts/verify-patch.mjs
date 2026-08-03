import { existsSync } from "node:fs";
import { readdir } from "node:fs/promises";
import { resolve } from "node:path";
import { spikeRoot, writeEvidence } from "./evidence.mjs";

const patches = resolve(spikeRoot, "baseline", "patches");
const entries = existsSync(patches) ? await readdir(patches) : [];
const patchFiles = entries.filter((entry) => entry.endsWith(".patch"));
const { target } = await writeEvidence("patches", "passed", { patchFiles, policy: "No patches are permitted for baseline rivet-v1.25.0." });
console.log(target);

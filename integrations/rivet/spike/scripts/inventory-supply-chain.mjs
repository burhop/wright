import { readdir, readFile, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { spikeRoot, writeEvidence } from "./evidence.mjs";

const modules = resolve(spikeRoot, "node_modules");
const packages = [];
async function visit(directory) {
  for (const entry of await readdir(directory)) {
    if (entry === ".bin") continue;
    const target = resolve(directory, entry);
    const details = await stat(target);
    if (!details.isDirectory()) continue;
    if (entry.startsWith("@")) {
      await visit(target);
      continue;
    }
    const manifest = resolve(target, "package.json");
    if (!existsSync(manifest)) continue;
    const value = JSON.parse(await readFile(manifest, "utf8"));
    const legacyLicenses = Array.isArray(value.licenses)
      ? value.licenses.map((license) => typeof license === "string" ? license : license.type).filter(Boolean)
      : [];
    packages.push({ name: value.name, version: value.version, license: value.license ?? (legacyLicenses.join(" OR ") || null) });
  }
}
await visit(modules);
const missingLicense = packages.filter((item) => !item.license).map((item) => `${item.name}@${item.version}`);
const { target } = await writeEvidence("supply-chain", missingLicense.length === 0 ? "passed" : "blocked", {
  packageCount: packages.length,
  missingLicense,
  packages: packages.sort((a, b) => a.name.localeCompare(b.name))
});
console.log(target);
if (missingLicense.length) process.exitCode = 1;

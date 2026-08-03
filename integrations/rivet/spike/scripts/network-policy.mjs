import { readFile, readdir, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { spikeRoot, writeEvidence } from "./evidence.mjs";

const dist = resolve(spikeRoot, ".work", "rivet", "packages", "app", "dist");
const fixture = resolve(spikeRoot, "fixture", "runner-harness.mjs");
const authorities = new Set();
async function scan(target) {
  const details = await stat(target);
  if (details.isDirectory()) {
    for (const name of await readdir(target)) await scan(resolve(target, name));
    return;
  }
  if (details.size > 5_000_000) return;
  const text = await readFile(target, "utf8").catch(() => "");
  for (const match of text.matchAll(/https?:\/\/([^/'"\\\s]+)/g)) authorities.add(match[1]);
}
if (existsSync(dist)) await scan(dist);
const fixtureText = await readFile(fixture, "utf8");
const fixtureUsesNetwork = /fetch\(|https?:\/\//.test(fixtureText);
const result = authorities.size === 0 && !fixtureUsesNetwork ? "passed" : "blocked";
const { target } = await writeEvidence("offline", result, {
  deniedAtBuild: "YARN_ENABLE_NETWORK=0",
  staticAuthorities: [...authorities].sort(),
  fixtureUsesNetwork
});
console.log(target);
if (result !== "passed") process.exitCode = 1;

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import process from "node:process";

export const spikeRoot = resolve(import.meta.dirname, "..");
export const reportsRoot = resolve(spikeRoot, "reports");
export const baselinePath = resolve(spikeRoot, "baseline", "baseline.json");

export function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

export async function readBaseline() {
  return JSON.parse(await readFile(baselinePath, "utf8"));
}

export function environment() {
  return {
    node: process.version,
    platform: process.platform,
    arch: process.arch,
    packageManager: process.env.npm_config_user_agent ?? "unknown"
  };
}

export async function writeEvidence(phase, result, details = {}, events = [], reportName = phase) {
  const baseline = await readBaseline();
  const envelope = {
    contractVersion: 1,
    baselineId: baseline.baselineId,
    phase,
    environment: environment(),
    result,
    timestamp: new Date().toISOString(),
    events,
    details
  };
  await mkdir(reportsRoot, { recursive: true });
  const target = resolve(reportsRoot, `${reportName}.json`);
  await writeFile(target, `${JSON.stringify(envelope, null, 2)}\n`, "utf8");
  return { envelope, target };
}

export async function digestFile(path) {
  return sha256(await readFile(path));
}

export async function writeText(path, text) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, text, "utf8");
}

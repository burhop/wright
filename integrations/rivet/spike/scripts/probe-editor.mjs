import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { readBaseline, spikeRoot, writeEvidence } from "./evidence.mjs";

const baseline = await readBaseline();
const root = resolve(spikeRoot, ".work", "rivet", "packages", "app", "src");
const targets = {
  io: resolve(root, "io", "IOProvider.ts"),
  browserIo: resolve(root, "io", "BrowserIOProvider.ts"),
  browserDataset: resolve(root, "io", "BrowserDatasetProvider.ts"),
  tauri: resolve(root, "model", "native", "TauriNativeApi.ts"),
  appPackage: resolve(spikeRoot, ".work", "rivet", "packages", "app", "package.json")
};
const source = Object.fromEntries(await Promise.all(Object.entries(targets).map(async ([key, path]) => [key, await readFile(path, "utf8")] )));
const finding = {
  ioProviderInterface: source.io.includes("export interface IOProvider"),
  browserIoProvider: source.browserIo.includes("BrowserIOProvider"),
  indexedDbDataset: /indexedDB|idb/i.test(source.browserDataset),
  tauriNativeApi: source.tauri.includes("TauriNativeApi"),
  globalProviderRisk: /let\s+ioProvider|export\s+let\s+ioProvider|globalThis/i.test(source.browserIo),
  appUsesTauri: /@tauri-apps\/api/.test(source.appPackage),
  candidate: baseline.sourceRevision
};
const result = finding.ioProviderInterface && finding.browserIoProvider ? "passed" : "blocked";
const { target } = await writeEvidence("editor", result, finding, [
  { syntheticWorkspace: "workspace-a", action: "provider-inspection" },
  { syntheticWorkspace: "workspace-b", action: "provider-inspection" }
]);
console.log(target);

import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const revision = "4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053";
const appVersion = "2.8.9";
const packageVersion = "2.1.9";
const runnerRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const checkout = resolve(
  process.env.WRIGHT_RIVET2_CHECKOUT ||
    resolve(runnerRoot, "..", "spike", ".work", "rivet2"),
);
const source = resolve(runnerRoot, "src", "wright-runner.ts");
const output = resolve(runnerRoot, "dist", "wright-runner.mjs");

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd,
    encoding: "utf8",
    stdio: options.capture ? "pipe" : "inherit",
  });
  if (result.status !== 0) {
    throw new Error(
      `${command} ${args.join(" ")} failed with status ${result.status}`,
    );
  }
  return (result.stdout || "").trim();
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

if (!existsSync(resolve(checkout, ".git"))) {
  throw new Error(
    "Pinned Rivet 2 checkout is missing. Run the editor acquire script first.",
  );
}
if (
  run("git", ["rev-parse", "HEAD"], { cwd: checkout, capture: true }) !==
  revision
) {
  throw new Error(`Pinned Rivet 2 checkout must be at ${revision}`);
}

mkdirSync(dirname(output), { recursive: true });
const yarn = resolve(checkout, ".yarn", "releases", "yarn-4.17.1.cjs");
run(
  process.execPath,
  [
    yarn,
    "exec",
    "esbuild",
    source,
    "--bundle",
    "--platform=node",
    "--format=esm",
    "--target=node22",
    '--banner:js=import { createRequire as __wrightCreateRequire } from "node:module"; const require = __wrightCreateRequire(import.meta.url);',
    `--alias:@valerypopoff/rivet2-node=${resolve(checkout, "packages", "node", "src", "index.ts")}`,
    `--outfile=${output}`,
  ],
  { cwd: checkout },
);

const manifest = {
  schema_version: 1,
  runner: "wright-rivet2-node",
  protocol_version: 2,
  rivet_version: appVersion,
  source: {
    repository: "https://github.com/valerypopoff/rivet2.0.git",
    revision,
    package: "@valerypopoff/rivet2-node",
    package_version: packageVersion,
  },
  entrypoint: "dist/wright-runner.mjs",
  sha256: sha256(output),
  bytes: statSync(output).size,
  build_input: {
    path: "src/wright-runner.ts",
    sha256: sha256(source),
  },
  runtime_network_policy: "wright-bridge-only",
};
writeFileSync(
  resolve(runnerRoot, "manifest.json"),
  `${JSON.stringify(manifest, null, 2)}\n`,
  "utf8",
);

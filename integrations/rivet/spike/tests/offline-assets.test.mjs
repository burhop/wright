import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
test("network probe runs with a declared denial policy", async () => {
  const source = await readFile(resolve(root, "scripts", "network-policy.mjs"), "utf8");
  assert.match(source, /YARN_ENABLE_NETWORK=0/);
  assert.match(source, /staticAuthorities/);
});

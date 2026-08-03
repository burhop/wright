import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
test("supply-chain inventory blocks missing license dispositions", async () => {
  const source = await readFile(resolve(root, "scripts", "inventory-supply-chain.mjs"), "utf8");
  assert.match(source, /missingLicense/);
  assert.match(source, /blocked/);
});

import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
test("baseline refuses floating source references", async () => {
  const baseline = JSON.parse(await readFile(resolve(root, "baseline", "baseline.json"), "utf8"));
  assert.notEqual(baseline.sourceRevision, "main");
  assert.notEqual(baseline.sourceRevision, "latest");
  assert.equal(baseline.patches.length, 0);
});

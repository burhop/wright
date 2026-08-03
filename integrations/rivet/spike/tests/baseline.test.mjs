import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
test("baseline is pinned by full immutable revision and exact package versions", async () => {
  const baseline = JSON.parse(await readFile(resolve(root, "baseline", "baseline.json"), "utf8"));
  assert.match(baseline.sourceRevision, /^[0-9a-f]{40}$/);
  assert.equal(baseline.packages["@ironclad/rivet-core"], "1.25.0");
  assert.equal(baseline.packages["@ironclad/rivet-node"], "1.25.0");
});

test("fixture contains only synthetic host operation identifiers", async () => {
  const fixture = await readFile(resolve(root, "fixture", "mock-workflow.rivet-project"), "utf8");
  assert.match(fixture, /wright_mock_operation/);
  assert.doesNotMatch(fixture, /token|secret|workspace_id|session_id/i);
});

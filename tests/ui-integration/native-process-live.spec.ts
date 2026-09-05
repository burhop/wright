import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// Opt in with PLAYWRIGHT_INCLUDE_LIVE=1, PLAYWRIGHT_BASE_URL and an explicitly
// prepared disposable workspace/session. All browser/API traffic is real.
const session = process.env.WRIGHT_NATIVE_LIVE_SESSION;
test.skip(
  !session,
  "Requires WRIGHT_NATIVE_LIVE_SESSION for an explicitly prepared disposable workspace",
);
const query = () => `?session_id=${encodeURIComponent(session!)}`;
const source = async (page: Page) =>
  JSON.parse(await page.getByTestId("native-source").inputValue());
const savedStatus = async (page: Page, revision: number) =>
  expect(page.getByTestId("native-status")).toContainText(
    `Saved revision ${revision}`,
  );

async function openExample(page: Page, id: string) {
  await page.getByTestId("native-example-list").selectOption(id);
  await page.getByTestId("native-open-example").click();
  await page.getByTestId("native-save").click();
  await savedStatus(page, 1);
}

async function runRecord(page: Page) {
  const id = await page.getByTestId("native-run-history").inputValue();
  const response = await page.request.get(
    `/api/native-processes/runs/${id}${query()}`,
  );
  expect(response.status()).toBe(200);
  return response.json();
}

async function verifyArtifact(page: Page, expected: string) {
  const run = await runRecord(page);
  const artifact = run.artifacts.at(-1);
  expect(artifact).toBeTruthy();
  await page
    .getByTestId(`native-inspect-artifact-${artifact.artifact_id}`)
    .click();
  await expect(
    page.getByTestId(`native-artifact-content-${artifact.artifact_id}`),
  ).toHaveValue(expected);
  const downloadEvent = page.waitForEvent("download");
  await page.getByTestId(`native-download-${artifact.artifact_id}`).click();
  const download = await downloadEvent;
  const bytes = readFileSync((await download.path())!);
  expect(bytes.toString("utf8")).toBe(expected);
  expect(createHash("sha256").update(bytes).digest("hex")).toBe(
    artifact.content_digest,
  );
  expect(artifact.provenance.run_id).toBe(run.run_id);
  expect(artifact.provenance.semantic_digest).toBe(run.semantic_digest);
  await page.getByTestId(`native-provenance-${artifact.artifact_id}`).click();
  await expect(
    page.getByTestId(`native-artifact-${artifact.artifact_id}`),
  ).toContainText(run.semantic_digest);
  return run;
}

test("@live native saved process computes, preserves failure and links correction", async ({
  page,
}, info) => {
  test.setTimeout(90_000);
  expect(
    session,
    "An explicitly prepared disposable native session is required",
  ).toBeTruthy();
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/native-processes");
  await openExample(page, "mass-check");
  const definition = await source(page);
  const savedResponse = await page.request.get(
    `/api/native-processes/documents/${definition.id}${query()}`,
  );
  expect(savedResponse.status()).toBe(200);
  expect((await savedResponse.json()).definition).toEqual(definition);
  await page.getByTestId("native-check").click();
  await page.getByTestId("native-run-start").click();
  await expect(page.getByTestId("native-run-state")).toHaveText("succeeded");
  const initial = await verifyArtifact(page, "Mass: 135 g");
  const range = definition.steps.find(
    (step: { operation: string }) => step.operation === "quantity.range@1",
  );
  await page.getByTestId(`native-correct-${range.id}`).click();
  await page.getByTestId("native-config-maximum-value").fill("100");
  await page.getByTestId("native-apply-step").click();
  await page.getByTestId("native-save").click();
  await savedStatus(page, 2);
  await page.getByTestId("native-run-start").click();
  await expect(page.getByTestId("native-run-state")).toHaveText("failed");
  const failed = await runRecord(page);
  expect(failed.reason.code).toBe("ASSERTION_FAILED");
  expect(failed.artifacts).toEqual([]);
  expect(
    failed.steps.some((step: { state: string }) => step.state === "blocked"),
  ).toBe(true);
  await page.getByTestId(`native-correct-${range.id}`).click();
  await page.getByTestId("native-config-maximum-value").fill("200");
  await page.getByTestId("native-apply-step").click();
  await page.getByTestId("native-save").click();
  await savedStatus(page, 3);
  await page.getByTestId("native-run-derived").click();
  await expect(page.getByTestId("native-run-state")).toHaveText("succeeded");
  const corrected = await verifyArtifact(page, "Mass: 135 g");
  expect(corrected.derived_from_run_id).toBe(failed.run_id);
  const retained = await page.request.get(
    `/api/native-processes/runs/${failed.run_id}${query()}`,
  );
  expect(await retained.json()).toEqual(failed);
  await page.reload();
  await page.getByTestId("native-saved-list").selectOption(definition.id);
  await page.getByTestId("native-open").click();
  await page.getByTestId("native-run-history").selectOption(corrected.run_id);
  await expect(page.getByTestId("native-run-state")).toHaveText("succeeded");
  const violations = (
    await new AxeBuilder({ page }).analyze()
  ).violations.filter((row) =>
    ["serious", "critical"].includes(row.impact ?? ""),
  );
  expect(violations).toEqual([]);
  expect(errors).toEqual([]);
  const evidencePath = info.outputPath("actual-native-runs.json");
  writeFileSync(
    evidencePath,
    JSON.stringify(
      {
        mockedRequests: false,
        definitionId: definition.id,
        initial,
        failed,
        corrected,
      },
      null,
      2,
    ),
  );
  await info.attach("actual-native-runs", {
    path: evidencePath,
    contentType: "application/json",
  });
  await page.screenshot({
    path: info.outputPath("native-run-recovery.png"),
    fullPage: true,
  });
});

test("@live native document and artifact-review examples produce exact files", async ({
  page,
}, info) => {
  test.setTimeout(60_000);
  expect(session).toBeTruthy();
  await page.goto("/native-processes");
  const observed = [];
  for (const [id, content] of [
    ["concept-brief", "Design a desk bracket.\nMaximum mass: 200 g."],
    ["package-review", "Part: BR-001\nUnits: mm\nRevision: A"],
  ]) {
    await openExample(page, id);
    await page.getByTestId("native-run-start").click();
    await expect(page.getByTestId("native-run-state")).toHaveText("succeeded");
    observed.push(await verifyArtifact(page, content));
  }
  const evidencePath = info.outputPath("actual-native-example-runs.json");
  writeFileSync(evidencePath, JSON.stringify(observed, null, 2));
  await info.attach("actual-native-example-runs", {
    path: evidencePath,
    contentType: "application/json",
  });
});

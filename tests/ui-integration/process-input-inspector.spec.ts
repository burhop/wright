import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
import { expect, test } from "@playwright/test";
import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
} from "./fixtures/workflow-recovery";

const source = readFileSync(
  resolve(
    process.cwd(),
    "specs/083-process-working-interfaces/fixtures/declared-human-input.workflow.wflow",
  ),
  "utf8",
);

test("edits input and human declarations through the workspace inspector and preserves undo, save and reopen", async ({
  page,
  browser,
}, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const fixture = await mockRecoveryWorkspace(page, { source });
  await openRecoveryEditor(page);
  const input = page.getByTestId("workflow-input-declaration-json");
  await page.getByTestId("workflow-recovery-block-block.brief").click();
  await expect(input).toBeVisible();
  const original = JSON.parse(await input.inputValue());
  const metadata = {
    ...original,
    value_schema: { type: "string", minLength: 2 },
    default: "Compare a and b after editing.",
  };
  await input.fill(JSON.stringify(metadata, null, 2));
  await page.getByTestId("workflow-input-declaration-apply").click();
  await expect(input).toHaveValue(/Compare a and b after editing/);
  await page.getByTestId("workflow-recovery-undo").click();
  await expect
    .poll(async () => JSON.parse(await input.inputValue()))
    .toEqual(original);
  await page.getByTestId("workflow-recovery-redo").click();
  await expect
    .poll(async () => JSON.parse(await input.inputValue()))
    .toEqual(metadata);
  await page.screenshot({
    path: testInfo.outputPath("input-schema-inspector.png"),
  });
  await page.getByTestId("workflow-recovery-block-block.choice").click();
  const instructions = page.getByTestId("workflow-human-input-instructions");
  await expect(instructions).toBeVisible();
  await expect(
    page.getByTestId("workflow-recovery-block-block.choice"),
  ).toContainText("Declared user input");
  await instructions.fill(
    "Review both measured comparison outputs before selecting.",
  );
  const declaration = page.getByTestId("workflow-human-input-json");
  const human = JSON.parse(await declaration.inputValue());
  expect(human.output_port).toBe("choice_response");
  human.response_schema.properties.selection.enum = ["a", "b", "c"];
  await declaration.fill(JSON.stringify(human, null, 2));
  await page.getByTestId("workflow-human-input-apply").click();
  await expect(instructions).toHaveValue(human.instructions);
  await page.screenshot({
    path: testInfo.outputPath("human-response-inspector.png"),
  });
  await page.getByTestId("workflow-recovery-save").click();
  await expect(page.getByTestId("workflow-recovery-save-status")).toHaveText(
    "Saved",
  );
  const saved = fixture.current()!.source;
  expect(saved).toContain('"interaction_input":');
  expect(saved).toContain('"human_interaction":');
  expect(saved).toContain('"output_port":"choice_response"');
  await testInfo.attach("inspector-saved.workflow.wflow", {
    body: Buffer.from(saved),
    contentType: "text/plain",
  });
  await page.reload();
  await expect(page.getByTestId("workflow-recovery-concept")).toHaveAttribute(
    "data-revision",
    String(fixture.current()!.definition_revision),
  );
  await page.getByTestId("workflow-recovery-block-block.brief").click();
  await expect
    .poll(async () => JSON.parse(await input.inputValue()))
    .toEqual(metadata);
  await page.getByTestId("workflow-recovery-block-block.choice").click();
  await expect
    .poll(async () => JSON.parse(await declaration.inputValue()))
    .toEqual(human);
  await page.getByTestId("workflow-recovery-view-code").click();
  await expect(page.getByTestId("workflow-recovery-source-editor")).toHaveValue(
    /Review both measured comparison outputs/,
  );
  expect(fixture.runCount()).toBe(0);
  await testInfo.attach("checked-inspector-scope.json", {
    contentType: "application/json",
    body: Buffer.from(
      JSON.stringify(
        {
          browser: browser.version(),
          viewport: page.viewportSize(),
          url: page.url(),
          saved_source_sha256: createHash("sha256").update(saved).digest("hex"),
          accepted_revision: fixture.current()!.definition_revision,
          editor_starts: fixture.runCount(),
          normal_workspace_entry: true,
          inspector_apply_undo_redo_save_reopen: true,
          controlled_http_contracts: true,
          live_backend: false,
          live_model: false,
          live_mcp: false,
        },
        null,
        2,
      ),
    ),
  });
});

test("creates a saveable draft user step without inventing a question or response", async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const fixture = await mockRecoveryWorkspace(page, { source });
  await openRecoveryEditor(page);
  await page.getByTestId("workflow-recovery-create-group-more").click();
  await page
    .getByTestId("workflow-recovery-create-template-human-input")
    .click();
  const inspector = page.getByTestId("workflow-human-input-editor");
  await expect(inspector).toContainText("This step is a draft");
  await expect(
    page.getByTestId("workflow-human-input-instructions"),
  ).toHaveValue("");
  await page.getByTestId("workflow-human-input-apply").click();
  await expect(inspector.getByRole("alert")).toContainText(
    "meaningful instructions",
  );
  await page.getByTestId("workflow-recovery-save").click();
  await expect(page.getByTestId("workflow-recovery-save-status")).toHaveText(
    "Saved",
  );
  expect(fixture.current()!.source).toContain(
    '"authoring_template":"human-input"',
  );
  await testInfo.attach("inspector-draft.workflow.wflow", {
    body: Buffer.from(fixture.current()!.source),
    contentType: "text/plain",
  });
  await page.reload();
  await page.getByTestId("workflow-recovery-block-block.human-input-1").click();
  await expect(inspector).toContainText("This step is a draft");
  await expect(
    page.getByTestId("workflow-human-input-instructions"),
  ).toHaveValue("");
  expect(fixture.runCount()).toBe(0);
  await page.screenshot({
    path: testInfo.outputPath("reopened-draft-user-step.png"),
  });
});

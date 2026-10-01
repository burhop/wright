import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { resolve } from "node:path";
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

test("preserves declared input schemas through workspace source editing, saving and reopening", async ({
  page,
  browser,
}, testInfo) => {
  const mock = await mockRecoveryWorkspace(page, { source });
  await openRecoveryEditor(page);
  const concept = page.getByTestId("workflow-recovery-concept");
  await expect(concept).toHaveAttribute(
    "data-semantic-digest",
    /^sha256:[a-f0-9]{64}$/,
  );
  await page.getByTestId("workflow-recovery-view-code").click();
  const editor = page.getByTestId("workflow-recovery-source-editor");
  const original = await editor.inputValue();
  expect(original).toContain('"human_interaction":');
  expect(original).toContain('"interaction_input":');
  await editor.fill(
    original.replace("Select comparison", "Review and select comparison"),
  );
  await expect(page.getByTestId("workflow-recovery-run-start")).toBeDisabled();
  await page.getByTestId("workflow-recovery-source-apply").click();
  await page.getByTestId("workflow-recovery-save").click();
  await expect(page.getByTestId("workflow-recovery-save-status")).toHaveText(
    "Saved",
  );
  expect(mock.current()?.source).toContain("Review and select comparison");
  expect(mock.current()?.source).toContain('"response_schema":');
  expect(mock.current()?.source).toContain('"required":["selection"]');
  expect(mock.current()?.source).toContain('"output_port":"choice_response"');
  expect(mock.current()?.source).toContain('"additionalProperties":false');
  expect(mock.runCount()).toBe(0);
  await page.reload();
  await expect(concept).toHaveAttribute(
    "data-revision",
    String(mock.current()?.definition_revision),
  );
  await page.getByTestId("workflow-recovery-view-code").click();
  await expect(editor).toHaveValue(/Review and select comparison/);
  await expect(editor).toHaveValue(/"human_interaction":/);
  await expect(editor).toHaveValue(/"interaction_input":/);
  expect(mock.runCount()).toBe(0);
  await page.screenshot({
    path: testInfo.outputPath("declared-input-source.png"),
  });
  await testInfo.attach("checked-scope.json", {
    contentType: "application/json",
    body: Buffer.from(
      JSON.stringify(
        {
          browser: browser.version(),
          viewport: page.viewportSize(),
          url: page.url(),
          original_source_sha256: createHash("sha256")
            .update(source, "utf8")
            .digest("hex"),
          saved_source_sha256: mock.current()?.storage_digest,
          saved_definition_revision: mock.current()?.definition_revision,
          process: {
            workspace_id: mock.current()?.workspace_id,
            source_path: mock.current()?.path,
            source_digest: mock.current()?.storage_digest,
          },
          controlled_run_start_count: mock.runCount(),
          served_frontend: true,
          controlled_http_contracts: true,
          source_edit_save_reopen: true,
          runtime_checkpoint_consumption: false,
          live_api: false,
          live_model: false,
          live_mcp: false,
          engineering_acceptance: false,
        },
        null,
        2,
      ),
    ),
  });
});

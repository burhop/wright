import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { resolve } from "node:path";
import { expect, test } from "@playwright/test";

import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
} from "./fixtures/workflow-recovery";
import { fixtureRunId, mockCommonProcessWorkspace } from "./fixtures/process-common-view";
import type { InteractionResponse, InteractionSnapshot } from "@wright/process-client";

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

for (const loseAcknowledgement of [false, true]) {
  test(`declared response resumes the saved workspace run${loseAcknowledgement ? " after explicit lost-ack reconciliation" : " after closing and reopening its tab"}`, async ({
    page,
    browser,
  }, testInfo) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    const fixture = await mockCommonProcessWorkspace(page, { source });
    const subject = createHash("sha256")
      .update("controlled-declared-subject")
      .digest("hex");
    let retained: InteractionResponse | undefined;
    const submissions: unknown[] = [];
    const snapshot = (): InteractionSnapshot => {
      const receipt = fixture.accepted()!;
      return {
        context: {
          process: fixture.process,
          run_id: fixtureRunId,
          input_snapshot_id: receipt.input_snapshot_id,
          input_digest: receipt.input_digest,
          generated_at: new Date().toISOString(),
        },
        state: retained ? "completed" : "waiting_human",
        interactions: retained
          ? []
          : [
              {
                checkpoint_id: "browser-input-checkpoint",
                step_id: "choice",
                kind: "input",
                subject_digest: subject,
                instructions:
                  "Choose the comparison to carry forward after reviewing the output.",
                state: "waiting",
                response_schema: {
                  type: "object",
                  properties: {
                    selection: { type: "string", enum: ["a", "b"] },
                  },
                  required: ["selection"],
                  additionalProperties: false,
                },
              },
            ],
        actions: retained
          ? []
          : [
              {
                action_id: "respond-input",
                operation: "respond",
                title: "Submit response",
                enabled: true,
                checkpoint_id: "browser-input-checkpoint",
                subject_digest: subject,
              },
            ],
      };
    };
    await page.route(
      `**/api/workspace/process-interfaces/runs/${fixtureRunId}**`,
      async (route) => {
        if (new URL(route.request().url()).pathname.endsWith("/events")) {
          const state = retained ? "completed" : "waiting_human";
          const data = {
            run_id: fixtureRunId,
            state,
            events: [],
            cursor: retained ? "response-2" : "waiting-1",
            following: false,
            has_more: false,
          };
          return route.fulfill({
            contentType: "text/event-stream",
            body: `id: ${data.cursor}\nevent: progress\ndata: ${JSON.stringify(data)}\n\n`,
          });
        }
        return route.fulfill({ json: snapshot() });
      },
    );
    await page.route(
      "**/api/workspace/process-interfaces/interactions/browser-input-checkpoint/response",
      async (route) => {
        const body = route.request().postDataJSON();
        submissions.push(body);
        expect(body).toEqual({
          session_id: "session-recovery",
          path: fixture.process.source_path,
          expected_storage_digest: fixture.process.source_digest,
          subject_digest: subject,
          value: { selection: "b" },
          request_id: expect.any(String),
        });
        if (retained) expect(body.request_id).toBe(retained.request_id);
        else
          retained = {
            response_id: "browser-answer",
            workspace_id: fixture.process.workspace_id,
            run_id: fixtureRunId,
            checkpoint_id: "browser-input-checkpoint",
            subject_digest: subject,
            schema_digest: subject,
            input_digest: fixture.accepted()!.input_digest,
            value: body.value,
            request_id: body.request_id,
            actor: "controlled-test-actor",
            reason: "Response to declared process input",
            created_at: new Date().toISOString(),
            digest: subject,
          };
        if (loseAcknowledgement && submissions.length === 1)
          return route.abort("failed");
        return route.fulfill({ status: 202, json: retained });
      },
    );
    await openRecoveryEditor(page);
    await page.getByTestId("workflow-working-view-open").click();
    await page
      .getByLabel("Design request (required)")
      .fill("Controlled comparison request.");
    await page
      .getByRole("button", { name: "Prepare and check inputs", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Start process", exact: true }),
    ).toBeEnabled();
    await page
      .getByRole("button", { name: "Start process", exact: true })
      .click();
    const common = page.getByTestId("common-process-view");
    await expect(common.getByLabel("selection (required)")).toBeVisible();
    await expect(
      common.getByRole("button", { name: "Submit response" }),
    ).toBeDisabled();
    const savedUrl = page.url();
    await page
      .getByTestId("editor-tabs-container")
      .locator('[data-testid^="editor-tab-close-/.wright/process-views/"]')
      .click();
    await expect(common).toHaveCount(0);
    expect(fixture.cancellations()).toBe(0);
    await page.goto(savedUrl);
    await expect(common.getByLabel("selection (required)")).toBeVisible();
    expect(fixture.starts()).toBe(1);
    expect(submissions).toHaveLength(0);
    await expect(common.getByRole("alert")).toHaveText("Provide a value.");
    await expect(common.getByRole("button", { name: "Submit response" })).toBeDisabled();
    await common.getByLabel("selection (required)").scrollIntoViewIfNeeded();
    await page.screenshot({
      path: testInfo.outputPath("reopened-input-form.png"),
      fullPage: true,
    });
    await common.getByLabel("selection (required)").selectOption("1");
    await common.getByRole("button", { name: "Submit response" }).click();
    if (loseAcknowledgement) {
      await expect(
        common.getByRole("button", { name: "Reconcile response request" }),
      ).toBeVisible();
      expect(submissions).toHaveLength(1);
      await expect(common.getByLabel("selection (required)")).toBeDisabled();
      await common
        .getByRole("button", { name: "Reconcile response request" })
        .click();
      expect(submissions[1]).toEqual(submissions[0]);
    }
    await expect(
      common.getByText("Process completed", { exact: true }),
    ).toBeVisible();
    await expect(common.getByRole("alert")).toHaveCount(0);
    expect(fixture.starts()).toBe(1);
    expect(fixture.cancellations()).toBe(0);
    await page.screenshot({
      path: testInfo.outputPath("same-run-response-completed.png"),
      fullPage: true,
    });
    await testInfo.attach("checked-response-scope.json", {
      contentType: "application/json",
      body: Buffer.from(
        JSON.stringify(
          {
            browser: browser.version(),
            url: page.url(),
            viewport: page.viewportSize(),
            process: fixture.process,
            run_id: fixtureRunId,
            checkpoint_id: retained?.checkpoint_id,
            subject_digest: subject,
            start_count: fixture.starts(),
            response_request_count: submissions.length,
            same_request_retry: loseAcknowledgement,
            close_without_cancel: true,
            served_frontend: true,
            controlled_http_contracts: true,
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
}

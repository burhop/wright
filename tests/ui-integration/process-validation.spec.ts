import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test } from "@playwright/test";

import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
} from "./fixtures/workflow-recovery";

const runtimeSource = readFileSync(
  resolve(
    process.cwd(),
    "tests/datasets/process-validation/processes/structured-loop.workflow.wflow",
  ),
  "utf8",
);

const taskSettings = (taskId: string) => {
  const section = new RegExp(`task ${taskId}\\n([\\s\\S]*?)\\nend`).exec(
    runtimeSource,
  )?.[1];
  const settings = /^ {2}settings: (.+)$/m.exec(section ?? "")?.[1];
  if (!settings) throw new Error(`Missing settings for ${taskId}`);
  return settings;
};

const source = `workflow structured_validation_loop
  name: "Structured output validation and correction"
  purpose: "Create structured engineering data, validate it, and release only a passing revision."
  discipline: "mechanical.design"
  reviewed_ai_suggestions: true
end

task produce
  name: "Produce controlled structured output"
  purpose: "Create the structured result that the next step validates."
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: []
  outputs: [{"key":"result","name":"Structured result","kind":"structured_result","item":null,"required":true,"quantity":"one","description":"The exact structured result to validate."}]
  prompt: "Create a JSON object with part_id and length_mm."
  settings: ${taskSettings("produce")}
  tool: null
  reusable_step: null
end

task inspect
  name: "Validate structured output"
  purpose: "Measure the producer output against the pinned requirements."
  step_type: work
  group: null
  performed_by: configured_tool
  inputs: [{"key":"subject","name":"Structured result","kind":"structured_result","item":null,"required":true,"quantity":"one","description":"The exact producer revision under validation."}]
  outputs: [{"key":"assessment","name":"Validation assessment","kind":"engineering_document","item":null,"required":true,"quantity":"one","description":"Saved findings and release disposition."}]
  prompt: "Run the pinned deterministic validation profile."
  settings: ${taskSettings("inspect")}
  tool: null
  reusable_step: null
end

task consume
  name: "Consume validated structured output"
  purpose: "Use only the current structured result released by validation."
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: [{"key":"validated_result","name":"Validated result","kind":"structured_result","item":null,"required":true,"quantity":"one","description":"The current passing producer revision."}]
  outputs: [{"key":"release_note","name":"Release note","kind":"engineering_document","item":null,"required":true,"quantity":"one","description":"A note recording release after validation."}]
  prompt: "State that the connected result was released after validation."
  settings: ${taskSettings("consume")}
  tool: null
  reusable_step: null
end

connection subject
  type: item
  from: "produce.result"
  to: "inspect.subject"
  label: "Output to validate"
  when: null
end

connection current_result
  type: item
  from: "produce.result"
  to: "consume.validated_result"
  label: "Current validated output"
  when: null
end

connection repair
  type: revision
  from: "inspect"
  to: "produce"
  label: "Correct measured defects"
  when: revise
end

connection release
  type: approval
  from: "inspect"
  to: "consume"
  label: "Release current passing revision"
  when: pass
end
`;

const event = (
  kind: string,
  taskId: string,
  taskTitle: string,
  extra: Record<string, unknown> = {},
) => ({
  kind,
  at: "2026-09-16T20:00:00Z",
  task_id: taskId,
  task_title: taskTitle,
  ...extra,
});

test("authors a validator and shows correction diagnostics with assessment links from Workflows", async ({
  page,
}, testInfo) => {
  const firstAssessment = "assessment-seeded-defect";
  const finalAssessment = "assessment-corrected-output";
  const mock = await mockRecoveryWorkspace(page, {
    source,
    run: {
      events: [
        event(
          "run_started",
          "",
          "Structured output validation and correction",
          {
            run_log_path: "runs/structured-validation/run-001.json",
          },
        ),
        event(
          "step_started",
          "produce",
          "Produce controlled structured output",
          {
            execution_kind: "ai",
          },
        ),
        event(
          "step_completed",
          "produce",
          "Produce controlled structured output",
        ),
        event("step_started", "inspect", "Validate structured output", {
          execution_kind: "validator",
        }),
        event("design_check", "inspect", "Validate structured output", {
          status: "revise",
          revision: 0,
          assessment_id: firstAssessment,
          assessment_path: `validation/${firstAssessment}.json`,
          report: {
            verdict: "revise",
            assessment_id: firstAssessment,
            assessment_path: `validation/${firstAssessment}.json`,
            corrections: [
              "Measured length is 98 mm; acceptance requires 100 mm ± 0.1 mm.",
            ],
          },
        }),
        event(
          "validation_feedback_delivered",
          "inspect",
          "Validate structured output",
          {
            assessment_id: firstAssessment,
            remaining_revisions: 2,
            complete_result_ref: `wright://workspace/ws-recovery/validation/${firstAssessment}`,
          },
        ),
        event(
          "design_revision",
          "produce",
          "Produce controlled structured output",
          {
            revision: 1,
            remaining_revisions: 1,
            invalidated_task_ids: ["produce", "inspect", "consume"],
          },
        ),
        event("step_started", "inspect", "Validate structured output", {
          execution_kind: "validator",
        }),
        event("design_check", "inspect", "Validate structured output", {
          status: "pass",
          revision: 1,
          assessment_id: finalAssessment,
          assessment_path: `validation/${finalAssessment}.json`,
          report: {
            verdict: "pass",
            assessment_id: finalAssessment,
            assessment_path: `validation/${finalAssessment}.json`,
            corrections: [],
          },
        }),
        event(
          "step_completed",
          "consume",
          "Consume validated structured output",
        ),
      ],
      result: {
        status: "completed",
        run_id: "run-001",
        run_log_path: "runs/structured-validation/run-001.json",
        workspace_id: "ws-recovery",
        workflow_path: "workflows/mounting-bracket.workflow.wflow",
        workflow_title: "Structured output validation and correction",
        task_id: "consume",
        task_title: "Consume validated structured output",
        output_path: "release-note-001.txt",
        output_bytes: 94,
        outputs: [
          {
            task_id: "consume",
            task_title: "Consume validated structured output",
            output_path: "release-note-001.txt",
            output_bytes: 94,
            output_format: "text",
          },
        ],
        results: [],
        steps: [],
      },
    },
  });

  await openRecoveryEditor(page);
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await page.getByTestId("workflow-recovery-block-block.inspect").click();
  const editor = page.getByTestId("workflow-recovery-validator-editor");
  await expect(editor).toBeVisible();
  await expect(editor.getByLabel("Validation profile")).toHaveValue(
    "structured-demo",
  );
  await expect(
    editor.getByLabel("Output to validate · result"),
  ).not.toHaveValue("");
  await expect(editor.getByLabel("Validation revision target")).toHaveValue(
    "block.produce",
  );
  await expect(editor.getByLabel("Maximum corrected revisions")).toHaveValue(
    "2",
  );

  await page.getByTestId("workflow-recovery-run-start").click();
  await expect.poll(() => mock.runCount()).toBe(1);
  expect(mock.runRequestCount()).toBe(1);
  await expect(page.getByTestId("workflow-native-run-summary")).toContainText(
    "Workflow completed",
  );
  const log = page.getByTestId("workflow-recovery-native-run-log");
  await log.locator("summary").click();
  await expect(log).toContainText("Output held for correction");
  await expect(log).toContainText("Correction feedback delivered");
  await expect(log).toContainText("Repairing output · revision 1");
  await expect(log).toContainText("Design check: pass");
  const evidence = page.getByTestId(
    "workflow-recovery-open-validation-evidence",
  );
  await expect(evidence).toHaveCount(2);
  await expect(evidence.first()).toContainText(firstAssessment);
  await expect(evidence.last()).toContainText(finalAssessment);

  await testInfo.attach("process-validation-workflow-run", {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png",
  });
});

test("shows the exact human requirements review from the workspace Workflows control", async ({
  page,
}, testInfo) => {
  const subjectDigest = "e".repeat(64);
  const mock = await mockRecoveryWorkspace(page, {
    source,
    run: {
      events: [],
      result: {
        status: "awaiting_approval",
        run_id: "run-validation-review",
        run_log_path: "runs/structured-validation/run-validation-review.json",
        workspace_id: "ws-recovery",
        workflow_path: "workflows/mounting-bracket.workflow.wflow",
        workflow_title: "Structured output validation and correction",
        task_id: "review_requirements",
        task_title: "Review requirements",
        output_path: "validation/review-package.json",
        output_bytes: 512,
        outputs: [],
        results: [],
        steps: [],
        approval: {
          checkpoint_id: "checkpoint-validation-review",
          workspace_id: "ws-recovery",
          workflow_id: "workflows/mounting-bracket.workflow.wflow",
          run_id: "run-validation-review",
          step_id: "review_requirements",
          action_kind: "local_review",
          subject: {
            definition_digest: "a".repeat(64),
            input_digests: ["b".repeat(64)],
            artifact_digests: ["c".repeat(64)],
            binding: { server: "wright", tool: "review_artifacts" },
            destination: { kind: "local_review", id: "workspace" },
            settings: {
              validation_review: {
                profile_ref: {
                  id: "structured-demo",
                  version: "1.0.0",
                  sha256: "d".repeat(64),
                },
                requirement_ids: ["STRUCT-001", "STRUCT-002"],
              },
              validation_review_requirements: [
                {
                  id: "STRUCT-001",
                  text: "The output records the required identity fields.",
                  scope: "content",
                  sources: [
                    {
                      artifact_ref: "requirements/structured.md",
                      locator: "Identity fields",
                      sha256: "f".repeat(64),
                    },
                  ],
                },
                {
                  id: "STRUCT-002",
                  text: "The measured length remains within its declared limit.",
                  scope: "design",
                  sources: [
                    {
                      artifact_ref: "requirements/structured.md",
                      locator: "Length constraint",
                      sha256: "1".repeat(64),
                    },
                  ],
                },
              ],
            },
            action: { kind: "local_review", mode: "review_only" },
          },
          subject_digest: subjectDigest,
          state: "pending",
          continuation: { next_step_index: 2 },
          actor: null,
          reason: null,
          created_at: 1,
          updated_at: 1,
          expires_at: null,
          external_action: null,
        },
      },
    },
  });

  await openRecoveryEditor(page);
  await page.getByTestId("workflow-recovery-run-start").click();
  await expect.poll(() => mock.runCount()).toBe(1);
  expect(mock.runRequestCount()).toBe(1);
  const review = page.getByTestId("workflow-external-approval");
  await expect(review).toBeVisible();
  await expect(review.getByRole("heading", { level: 3 })).toHaveText(
    "Review results against the requirements",
  );
  await expect(review).toContainText("structured-demo");
  await expect(review).toContainText("STRUCT-001");
  await expect(review).toContainText("STRUCT-002");
  await expect(review).toContainText(
    "The output records the required identity fields.",
  );
  await expect(review).toContainText("requirements/structured.md");
  await expect(review).toContainText("Length constraint");
  await expect(review).toContainText(subjectDigest);
  await expect(review).toContainText(
    "Approval records your engineering judgment for these files; it does not mean the whole workflow has passed.",
  );
  await expect(
    review.getByTestId("workflow-external-approval-approve"),
  ).toHaveText("Approve reviewed requirements");

  await page.getByRole("button", { name: "Expand details" }).click();
  await review.getByRole("heading", { level: 3 }).scrollIntoViewIfNeeded();

  await testInfo.attach("validation-requirements-review", {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png",
  });
});

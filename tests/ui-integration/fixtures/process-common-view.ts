/** Controlled HTTP contracts for the served workspace journey, not live tool proof. */
import { createHash } from "node:crypto";
import { expect, type Page } from "@playwright/test";
import type {
  ArtifactRef,
  InputBinding,
  InputSnapshot,
  InteractionSnapshot,
  NavigationTarget,
  ProcessRef,
  Readiness,
  StartReceipt,
} from "@wright/process-client";
import { mockRecoveryWorkspace } from "./workflow-recovery";

const prefix = "/api/workspace/process-interfaces";
const session = "session-recovery";
export const commonViewSource = `workflow common_view_fixture
  name: "Common view browser fixture"
  purpose: "Exercise presentation contracts without engineering dispatch."
  discipline: "engineering"
  reviewed_ai_suggestions: false
end
input brief
  name: "Design request"
  purpose: "Supply the exact test request."
  group: null
  step_type: work
  provided_by: engineer
  inputs: []
  outputs: [{"key":"brief_out","kind":"engineering_document","name":"Brief","required":true,"item":null,"quantity":"one","description":"Exact supplied test request"}]
  instructions: "Enter the request."
  settings: {"input_mode":"text"}
  tool: null
  reusable_step: null
end
task first
  name: "Create test report"
  purpose: "Use the supplied test request to prepare a report."
  group: null
  step_type: work
  performed_by: ai_assisted
  inputs: [{"key":"first_in","kind":"engineering_document","name":"Brief","required":true,"item":null,"quantity":"one","description":"Exact supplied test request"}]
  outputs: [{"key":"first_document_out","kind":"engineering_document","name":"Report","required":true,"item":null,"quantity":"one","description":"Controlled test report"}]
  prompt: "Use the exact supplied request."
  settings: {"output_format":"text","output_filename":"report.txt","save_output":true}
  tool: null
  reusable_step: null
end
connection supplied
  type: item
  from: "brief.brief_out"
  to: "first.first_in"
  label: "Supplied request"
  when: null
end
`;

const digest = (value: string | Buffer) =>
  createHash("sha256").update(value).digest("hex");
export const fixtureRunId = "common-browser-run";
const resultId = `${fixtureRunId}:first:first_document_out`;
const report = Buffer.from(
  "Controlled browser fixture output; no engineering acceptance.",
);
const assessment = Buffer.from(
  JSON.stringify({ fixture: true, finding: "Controlled assessment evidence" }),
);
const resultRef: ArtifactRef = {
  artifact_ref: "outputs/report.txt",
  sha256: digest(report),
  result_id: resultId,
};
const assessmentRef: ArtifactRef = {
  artifact_ref: "outputs/assessment.json",
  sha256: digest(assessment),
  result_id: `${fixtureRunId}:validator:assessment`,
};

export async function mockCommonProcessWorkspace(
  page: Page,
  options: {
    source?: string;
    loseStartAcknowledgement?: boolean;
    disconnectEvents?: boolean;
  } = {},
) {
  const editor = await mockRecoveryWorkspace(page, {
    source: options.source ?? commonViewSource,
  });
  const process: ProcessRef = {
    workspace_id: "ws-recovery",
    source_path: "workflows/mounting-bracket.workflow.wflow",
    source_digest: digest(options.source ?? commonViewSource),
  };
  let input: InputSnapshot | undefined;
  let accepted: StartReceipt | undefined;
  let completed = false;
  let failed = false;
  let starts = 0,
    eventReads = 0,
    cancelled = 0;
  const requests: string[] = [];
  const navigations: NavigationTarget[] = [];
  const reads: ArtifactRef[] = [];
  const readiness = (): Readiness => {
    const supplied = input?.bindings.some(
      (binding) =>
        binding.kind === "value" &&
        binding.input_id === "brief" &&
        typeof binding.value === "string" &&
        binding.value.trim().length > 0,
    );
    return {
      process,
      assessment_id: "browser-readiness",
      assessed_at: new Date().toISOString(),
      input_digest: input?.digest,
      state: supplied ? "ready" : "blocked",
      reasons: supplied
        ? []
        : [
            {
              code: "INPUT_REQUIRED",
              message: "Provide the design request before starting.",
              correction: "Enter the request and prepare the inputs again.",
              navigation: { kind: "block", block_id: "brief" },
            },
          ],
    };
  };
  const snapshot = (run = false): InteractionSnapshot => {
    const checked = input ? readiness() : undefined;
    return {
      context: {
        process,
        generated_at: new Date().toISOString(),
        cursor: completed ? 2 : 1,
        ...(input
          ? { input_snapshot_id: input.snapshot_id, input_digest: input.digest }
          : {}),
        ...(run ? { run_id: fixtureRunId } : {}),
      },
      state: run
        ? failed
          ? "failed"
          : completed
            ? "completed"
            : "running"
        : checked?.state === "ready"
          ? "ready"
          : "preparing",
      inputs: [
        {
          input_id: "brief",
          block_id: "brief",
          port_id: "brief_out",
          title: "Design request",
          value_schema: { type: "string" },
          required: true,
          current_value: input?.bindings[0],
        },
      ],
      readiness: checked,
      diagnostics:
        run && failed
          ? [
              {
                code: "INTERACTION_NOT_DECLARED",
                message:
                  "Create test report: additional user input was requested in an unattended step.",
                correction:
                  "Supply the missing requirement before starting, connect an upstream producer, or declare a human-input step before this task.",
                step_id: "first",
                navigation: {
                  kind: "block",
                  block_id: "first",
                  run_id: fixtureRunId,
                },
                technical_details_ref: "runs/browser/diagnostic.json",
              },
            ]
          : [],
      actions: run
        ? [
            {
              action_id: "cancel-run",
              operation: "cancel",
              title: "Cancel this run",
              enabled: !completed && !failed,
              subject_digest: input?.digest,
              reasons:
                completed || failed
                  ? [
                      {
                        code: "ACTION_NOT_PERMITTED",
                        message: "This fixture run has ended.",
                        correction: "Inspect the saved result.",
                      },
                    ]
                  : [],
            },
          ]
        : [
            {
              action_id: "start",
              operation: "start",
              title: "Start process",
              enabled: checked?.state === "ready",
              subject_digest: input?.digest,
              reasons:
                checked?.state === "ready"
                  ? []
                  : [
                      {
                        code: "INPUT_REQUIRED",
                        message: "Prepare the design request first.",
                        correction: "Provide inputs and check readiness.",
                      },
                    ],
            },
          ],
      outputs:
        run && (completed || failed)
          ? [
              {
                result_id: resultId,
                step_id: "first",
                port_id: "first_document_out",
                role: "document",
                title: "Browser fixture report",
                representations: [resultRef],
                assessments: [
                  {
                    assessment_id: "browser-assessment",
                    subject_digest: digest(report),
                    outcome: "pass",
                    currentness: "current",
                  },
                ],
                supported_viewers: ["text"],
              },
            ]
          : [],
      observations: run
        ? [
            {
              observation_id: "browser-operation",
              provider_binding: "controlled-browser-fixture",
              operation_id: fixtureRunId,
              state: failed ? "failed" : completed ? "completed" : "running",
              observed_at: new Date().toISOString(),
              stale_after: new Date(Date.now() + 60_000).toISOString(),
              activity: failed
                ? "The unattended step needs a declared dependency."
                : completed
                ? "Controlled fixture completed"
                : "Preparing the controlled fixture report",
              progress_percent: failed ? null : completed ? 100 : 20,
              limitations: [
                "Controlled HTTP fixture; no model or engineering tool was invoked.",
              ],
            },
          ]
        : [],
    };
  };
  await page.route(`**${prefix}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const suffix = url.pathname.slice(prefix.length);
    const body =
      request.method() === "GET"
        ? Object.fromEntries(url.searchParams)
        : request.postDataJSON();
    expect(body.session_id).toBe(session);
    expect(body.path).toBe(process.source_path);
    expect(body.expected_storage_digest).toBe(process.source_digest);
    if (suffix === "/interaction") return route.fulfill({ json: snapshot() });
    if (suffix === "/inputs") {
      const bindings = body.bindings as InputBinding[];
      input = {
        process,
        snapshot_id: "browser-inputs",
        digest: digest(JSON.stringify(bindings)),
        created_at: new Date().toISOString(),
        bindings,
      };
      await new Promise((resolve) => setTimeout(resolve, 200));
      return route.fulfill({ json: input });
    }
    if (suffix === "/readiness") return route.fulfill({ json: readiness() });
    if (suffix === "/runs") {
      starts++;
      expect(input).toBeDefined();
      expect(body.input_snapshot_id).toBe(input!.snapshot_id);
      expect(body.expected_input_digest).toBe(input!.digest);
      requests.push(body.request_id);
      if (!accepted)
        accepted = {
          process,
          request_id: body.request_id,
          run_id: fixtureRunId,
          input_snapshot_id: input!.snapshot_id,
          input_digest: input!.digest,
          payload_digest: digest(JSON.stringify(body)),
          principal_id: "controlled-test-actor",
          created_at: new Date().toISOString(),
        };
      expect(body.request_id).toBe(accepted.request_id);
      if (starts === 1 && options.loseStartAcknowledgement)
        return route.abort("failed");
      return route.fulfill({ status: 202, json: accepted });
    }
    if (suffix === `/runs/${fixtureRunId}`)
      return route.fulfill({ json: snapshot(true) });
    if (suffix === `/runs/${fixtureRunId}/events`) {
      eventReads++;
      if (eventReads === 1 && options.disconnectEvents)
        return route.abort("failed");
      const cursor = completed ? "browser-cursor-2" : "browser-cursor-1";
      const event = {
        run_id: fixtureRunId,
        state: failed ? "failed" : completed ? "completed" : "running",
        events: [
          {
            sequence: completed ? 2 : 1,
            kind: completed ? "step_completed" : "step_started",
            task_id: "first",
            task_title: "Create test report",
          },
        ],
        cursor,
        has_more: false,
        following: !completed && !failed,
      };
      return route.fulfill({
        contentType: "text/event-stream",
        body: `id: ${cursor}\nevent: progress\ndata: ${JSON.stringify(event)}\n\n`,
      });
    }
    if (suffix === `/runs/${fixtureRunId}/cancel`) {
      cancelled++;
      return route.fulfill({
        json: {
          request_id: body.request_id,
          run_id: fixtureRunId,
          state: "cancellation_requested",
        },
      });
    }
    if (suffix === "/navigation") {
      const target = body.target as NavigationTarget;
      navigations.push(target);
      if (target.kind === "assessment") {
        expect(target.run_id).toBe(fixtureRunId);
        expect(target.result_id).toBe(resultId);
        expect(target.assessment_id).toBe("browser-assessment");
        return route.fulfill({
          json: {
            process,
            target: { ...target, block_id: "first" },
            representation: assessmentRef,
          },
        });
      }
      return route.fulfill({ json: { process, target } });
    }
    if (suffix === "/representations/read") {
      const ref = body.reference as ArtifactRef;
      reads.push(ref);
      expect(body.run_id).toBe(fixtureRunId);
      const file =
        ref.artifact_ref === resultRef.artifact_ref ? report : assessment;
      expect(ref.sha256).toBe(digest(file));
      return route.fulfill({
        body: file,
        headers: {
          "content-type": ref.artifact_ref.endsWith(".json")
            ? "application/json"
            : "text/plain",
          "content-length": String(file.length),
          "x-content-type-options": "nosniff",
          "x-wright-artifact-sha256": digest(file),
          "cache-control": "no-store",
        },
      });
    }
    throw new Error(
      `Unmocked common-view contract: ${request.method()} ${suffix}`,
    );
  });
  return {
    editor,
    process,
    resultId,
    starts: () => starts,
    requests: () => requests,
    accepted: () => accepted,
    eventReads: () => eventReads,
    cancellations: () => cancelled,
    navigations: () => navigations,
    representations: () => reads,
    complete: () => {
      completed = true;
    },
    failWithUndeclaredInput: () => {
      failed = true;
    },
  };
}

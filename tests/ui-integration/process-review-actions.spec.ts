/** Served workspace presentation with controlled HTTP; no live engineering effects. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
import { expect, test } from "@playwright/test";
import type {
  InteractionSnapshot,
  ReviewDecision,
  ApprovedActionReceipt,
} from "@wright/process-client";
import {
  fixtureRunId,
  mockCommonProcessWorkspace,
} from "./fixtures/process-common-view";
import { openRecoveryEditor } from "./fixtures/workflow-recovery";

const source = readFileSync(
  resolve(
    process.cwd(),
    "specs/083-process-working-interfaces/fixtures/declared-review-action.workflow.wflow",
  ),
  "utf8",
);
for (const lose of ["none", "review", "action", "unknown"] as const) {
  test(`reviews then explicitly submits an exact action in the normal workspace (${lose} lost acknowledgement)`, async ({
    page,
    browser,
  }, testInfo) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    const fixture = await mockCommonProcessWorkspace(page, { source });
    const subject = createHash("sha256")
      .update("controlled-review-action-subject")
      .digest("hex");
    let decision: ReviewDecision | undefined;
    let action: ApprovedActionReceipt | undefined;
    let observed = false;
    const reviews: unknown[] = [],
      actions: unknown[] = [];
    const snapshot = (): InteractionSnapshot => ({
      context: {
        process: fixture.process,
        run_id: fixtureRunId,
        input_snapshot_id: fixture.accepted()!.input_snapshot_id,
        input_digest: fixture.accepted()!.input_digest,
        generated_at: new Date().toISOString(),
      },
      state:
        lose === "unknown" && action
          ? "reconciliation_required"
          : observed
            ? "completed"
            : action
              ? "waiting_external"
              : "waiting_human",
      interactions: [
        {
          checkpoint_id: "browser-review",
          step_id: "review",
          kind: "action",
          subject_digest: subject,
          instructions: "Review the controlled document before continuing.",
          decisions: ["approved", "changes_requested"],
          state: action ? "consumed" : "waiting",
          ...(decision ? { decision } : {}),
          ...(action ? { action_receipt: action } : {}),
        },
      ],
      actions: [
        {
          action_id: "review-browser-review",
          operation: "review",
          title: "Review action",
          enabled: !decision,
          checkpoint_id: "browser-review",
          subject_digest: subject,
          reasons: decision
            ? [
                {
                  code: "ACTION_NOT_PERMITTED",
                  message: "Review already recorded.",
                  correction: "Inspect its recorded decision.",
                },
              ]
            : [],
        },
        {
          action_id: "continue-browser-review",
          operation: "action",
          title: "Continue process",
          enabled: !!decision && !action,
          checkpoint_id: "browser-review",
          subject_digest: subject,
          reasons:
            decision && !action
              ? []
              : [
                  {
                    code: "ACTION_NOT_PERMITTED",
                    message: action
                      ? "Action already consumed."
                      : "Complete its review first.",
                    correction: "Inspect the exact checkpoint.",
                  },
                ],
        },
      ],
      observations: action
        ? [
            {
              observation_id: "browser-digital-operation",
              provider_binding: "controlled-http",
              operation_id: "browser-operation-one",
              state: observed ? "completed" : "waiting_external",
              observed_at: new Date().toISOString(),
              stale_after: new Date(Date.now() + 60000).toISOString(),
              activity: observed
                ? "Controlled observed completion"
                : "Waiting for controlled provider acceptance",
              progress_percent: observed ? 100 : null,
              limitations: [
                "Controlled HTTP fixture; no engineering provider was invoked.",
              ],
            },
          ]
        : [],
    });
    await page.route(
      `**/api/workspace/process-interfaces/runs/${fixtureRunId}**`,
      async (route) => {
        if (new URL(route.request().url()).pathname.endsWith("/events")) {
          const state = snapshot().state,
            cursor = observed ? "complete-3" : action ? "action-2" : "review-1";
          const event = {
            run_id: fixtureRunId,
            state,
            events: [],
            cursor,
            following: false,
            has_more: false,
          };
          return route.fulfill({
            contentType: "text/event-stream",
            body: `id: ${cursor}\nevent: progress\ndata: ${JSON.stringify(event)}\n\n`,
          });
        }
        return route.fulfill({ json: snapshot() });
      },
    );
    await page.route(
      "**/api/workspace/process-interfaces/interactions/browser-review/decision",
      async (route) => {
        const body = route.request().postDataJSON();
        reviews.push(body);
        expect(body).toEqual({
          session_id: "session-recovery",
          path: fixture.process.source_path,
          expected_storage_digest: fixture.process.source_digest,
          subject_digest: subject,
          decision: "approved",
          reason: "Controlled review of the exact document",
          request_id: expect.any(String),
        });
        if (decision) expect(body.request_id).toBe(decision.request_id);
        else
          decision = {
            decision: "approved",
            actor: "controlled-test-actor",
            reason: body.reason,
            request_id: body.request_id,
            integration_test: false,
          };
        if (lose === "review" && reviews.length === 1)
          return route.abort("failed");
        return route.fulfill({ json: snapshot() });
      },
    );
    await page.route(
      "**/api/workspace/process-interfaces/actions/continue-browser-review",
      async (route) => {
        const body = route.request().postDataJSON();
        actions.push(body);
        expect(body).toEqual({
          session_id: "session-recovery",
          path: fixture.process.source_path,
          expected_storage_digest: fixture.process.source_digest,
          subject_digest: subject,
          request_id: expect.any(String),
        });
        expect(decision?.decision).toBe("approved");
        if (action) expect(body.request_id).toBe(action.request_id);
        else
          action = {
            request_id: body.request_id,
            principal_id: "controlled-test-actor",
            submission: lose === "unknown" ? "unknown" : "authorized",
            observed_outcome: lose === "unknown" ? "unknown" : null,
            delivery_completed: false,
            cancellation_requested: false,
          };
        if (lose === "action" && actions.length === 1)
          return route.abort("failed");
        return route.fulfill({ status: 202, json: snapshot() });
      },
    );
    await openRecoveryEditor(page);
    await page.getByTestId("workflow-working-view-open").click();
    await page
      .getByLabel("Design request (required)")
      .fill("Controlled action request.");
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
    await expect(
      common.getByRole("button", { name: "Request changes", exact: true }),
    ).toBeDisabled();
    await common
      .getByLabel("Review reason")
      .fill("Controlled review of the exact document");
    await page.screenshot({
      path: testInfo.outputPath("declared-review-controls.png"),
      fullPage: true,
    });
    await common.getByRole("button", { name: "Approve", exact: true }).click();
    if (lose === "review") {
      await expect(
        common.getByRole("button", {
          name: "Reconcile review request",
          exact: true,
        }),
      ).toBeVisible();
      await page.reload();
      await expect(
        common.getByRole("button", {
          name: "Reconcile review request",
          exact: true,
        }),
      ).toBeVisible();
      expect(reviews).toHaveLength(1);
      expect(actions).toHaveLength(0);
      await common
        .getByRole("button", { name: "Reconcile review request", exact: true })
        .click();
      expect(reviews[1]).toEqual(reviews[0]);
    }
    await expect(
      common.getByText("Review recorded: Approved", { exact: true }),
    ).toBeVisible();
    expect(actions).toHaveLength(0);
    const savedUrl = page.url();
    await expect(
      common.getByRole("button", { name: "Continue process", exact: true }),
    ).toBeDisabled();
    await common.getByLabel("I reviewed this action and its evidence").check();
    await common
      .getByRole("button", { name: "Continue process", exact: true })
      .click();
    if (lose === "action") {
      await expect(
        common.getByRole("button", {
          name: "Reconcile action request",
          exact: true,
        }),
      ).toBeVisible();
      await page.reload();
      await expect(
        common.getByRole("button", {
          name: "Reconcile action request",
          exact: true,
        }),
      ).toBeVisible();
      expect(actions).toHaveLength(1);
      await common
        .getByRole("button", { name: "Reconcile action request", exact: true })
        .click();
      expect(actions[1]).toEqual(actions[0]);
    }
    await expect(
      common.getByText(
        lose === "unknown"
          ? "Submission outcome is unknown; reconcile before another action."
          : "Action authorized; provider acceptance is not confirmed yet.",
        { exact: true },
      ),
    ).toBeVisible();
    await expect(
      common.getByRole("button", {
        name: "Reconcile action request",
        exact: true,
      }),
    ).toHaveCount(0);
    await page.screenshot({
      path: testInfo.outputPath("authorized-awaiting-observation.png"),
      fullPage: true,
    });
    if (lose !== "unknown") {
      observed = true;
      action = {
        ...action!,
        submission: "accepted",
        delivery_completed: true,
        observed_outcome: "completed",
        provider_reference: "browser-operation-one",
      };
    }
    await common
      .getByRole("button", { name: "Refresh view", exact: true })
      .click();
    await expect(
      common.getByText(
        lose === "unknown"
          ? "Observed outcome: unknown"
          : "Observed outcome: completed",
        { exact: true },
      ),
    ).toBeVisible();
    await page.goto(savedUrl);
    await expect(
      common.getByText(
        lose === "unknown"
          ? "Observed outcome: unknown"
          : "Observed outcome: completed",
        { exact: true },
      ),
    ).toBeVisible();
    if (lose === "unknown") {
      await expect(
        common.getByText("Observed outcome: completed", { exact: true }),
      ).toHaveCount(0);
      await expect(
        common
          .getByRole("button", { name: "Continue process", exact: true })
          .and(page.locator("button:enabled")),
      ).toHaveCount(0);
      expect(action?.submission).toBe("unknown");
      expect(action?.delivery_completed).toBe(false);
    }
    expect(fixture.starts()).toBe(1);
    expect(fixture.editor.runCount()).toBe(0);
    expect(fixture.cancellations()).toBe(0);
    expect(reviews).toHaveLength(lose === "review" ? 2 : 1);
    expect(actions).toHaveLength(lose === "action" ? 2 : 1);
    await page.screenshot({
      path: testInfo.outputPath("reopened-observed-completion.png"),
      fullPage: true,
    });
    await testInfo.attach("checked-action-scope.json", {
      contentType: "application/json",
      body: Buffer.from(
        JSON.stringify(
          {
            browser: browser.version(),
            url: page.url(),
            process: fixture.process,
            run_id: fixtureRunId,
            subject_digest: subject,
            viewport: page.viewportSize(),
            reviews,
            actions,
            starts: fixture.starts(),
            decision,
            action,
            served_workspace: true,
            controlled_http: true,
            live_backend: false,
            live_model: false,
            live_mcp: false,
            physical_operation: false,
            engineering_acceptance: false,
            user_acceptance: false,
          },
          null,
          2,
        ),
      ),
    });
  });
}

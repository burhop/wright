/** Served presentation checks; actual durable runtime is exercised by Python tests. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
import { expect, test } from "@playwright/test";
import type {
  InteractionResponse,
  InteractionSnapshot,
} from "@wright/process-client";
import {
  fixtureRunId,
  mockCommonProcessWorkspace,
} from "./fixtures/process-common-view";
import { openRecoveryEditor } from "./fixtures/workflow-recovery";

const source = readFileSync(
  resolve(
    process.cwd(),
    "specs/083-process-working-interfaces/fixtures/two-declared-human-inputs.workflow.wflow",
  ),
  "utf8",
);
for (const scenario of ["accepted", "lost", "schema", "stale"] as const) {
  test(`two declared inputs preserve one workspace run (${scenario})`, async ({
    page,
    browser,
  }, testInfo) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    const fixture = await mockCommonProcessWorkspace(page, { source });
    let stage = 0;
    let stale = false;
    const requests: Array<Record<string, unknown>> = [];
    const recorded = new Map<string, InteractionResponse>();
    const checkpoint = (index: number) => `two-input-${index + 1}`;
    const subject = (index: number) =>
      createHash("sha256")
        .update(`controlled-two-input-subject-${index}`)
        .digest("hex");
    const snapshot = (): InteractionSnapshot => ({
      context: {
        process: fixture.process,
        run_id: fixtureRunId,
        input_snapshot_id: fixture.accepted()!.input_snapshot_id,
        input_digest: fixture.accepted()!.input_digest,
        generated_at: new Date().toISOString(),
      },
      state: stage < 2 ? "waiting_human" : "completed",
      interactions:
        stage < 2
          ? [
              {
                checkpoint_id: checkpoint(stage),
                step_id: stage === 0 ? "choice" : "choice_two",
                kind: "input",
                state: "waiting",
                subject_digest: subject(stage),
                instructions:
                  stage === 0
                    ? "Choose the first comparison."
                    : "Choose the second comparison after reviewing its output.",
                response_schema: {
                  type: "object",
                  properties: {
                    selection: { type: "string", enum: ["a", "b"] },
                  },
                  required: ["selection"],
                  additionalProperties: false,
                },
              },
            ]
          : [],
      actions:
        stage < 2
          ? [
              {
                action_id: "respond-input",
                operation: "respond",
                title: "Submit response",
                enabled: !stale,
                checkpoint_id: checkpoint(stage),
                subject_digest: subject(stage),
                reasons: stale
                  ? [
                      {
                        code: "SUBJECT_STALE",
                        message: "The recorded evidence changed.",
                        correction:
                          "Refresh and review the current evidence before responding.",
                      },
                    ]
                  : [],
              },
            ]
          : [],
    });
    await page.route(
      `**/api/workspace/process-interfaces/runs/${fixtureRunId}**`,
      async (route) => {
        if (new URL(route.request().url()).pathname.endsWith("/events")) {
          const data = {
            run_id: fixtureRunId,
            state: stage < 2 ? "waiting_human" : "completed",
            cursor: `barrier-${stage}`,
            events: [],
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
      "**/api/workspace/process-interfaces/interactions/two-input-*/response",
      async (route) => {
        const index = route.request().url().includes("two-input-1/") ? 0 : 1;
        const body = route.request().postDataJSON();
        requests.push({ checkpoint_id: checkpoint(index), ...body });
        expect(body).toMatchObject({
          session_id: "session-recovery",
          path: fixture.process.source_path,
          expected_storage_digest: fixture.process.source_digest,
          subject_digest: subject(index),
          request_id: expect.any(String),
          value: { selection: index === 0 ? "b" : "a" },
        });
        if (
          (scenario === "schema" || scenario === "stale") &&
          requests.length === 1
        ) {
          stale = scenario === "stale";
          return route.fulfill({
            status: stale ? 409 : 400,
            json: {
              detail: {
                reason: {
                  code: stale ? "SUBJECT_STALE" : "RESPONSE_INVALID",
                  message: stale
                    ? "The recorded evidence changed."
                    : "The response does not match the recorded schema.",
                  correction: stale
                    ? "Refresh and review the current evidence before responding."
                    : "Check the required response fields and submit explicitly.",
                },
              },
            },
          });
        }
        let receipt = recorded.get(checkpoint(index));
        if (receipt) {
          expect(body.request_id).toBe(receipt.request_id);
          expect(body.value).toEqual(receipt.value);
        } else {
          expect(index).toBe(stage);
          receipt = {
            response_id: `controlled-answer-${index}`,
            workspace_id: fixture.process.workspace_id,
            run_id: fixtureRunId,
            checkpoint_id: checkpoint(index),
            subject_digest: subject(index),
            schema_digest: subject(index),
            input_digest: fixture.accepted()!.input_digest,
            value: body.value,
            request_id: body.request_id,
            actor: "controlled-test-actor",
            reason: "Response to declared process input",
            created_at: new Date().toISOString(),
            digest: subject(index),
          };
          recorded.set(checkpoint(index), receipt);
          stage++;
        }
        if (scenario === "lost" && requests.length === 1)
          return route.abort("failed");
        return route.fulfill({ status: 202, json: receipt });
      },
    );
    await openRecoveryEditor(page);
    await page.getByTestId("workflow-working-view-open").click();
    await page
      .getByLabel("Design request (required)")
      .fill("Controlled two-checkpoint comparison request.");
    await page
      .getByRole("button", { name: "Prepare and check inputs", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Start process", exact: true })
      .click();
    const common = page.getByTestId("common-process-view");
    await expect(
      common.getByText("Choose the first comparison.", { exact: true }),
    ).toBeVisible();
    const savedUrl = page.url();
    await page.reload();
    await expect(common.getByLabel("selection (required)")).toBeVisible();
    expect(requests).toHaveLength(0);
    expect(fixture.starts()).toBe(1);
    await common.getByLabel("selection (required)").selectOption("1");
    await common
      .getByRole("button", { name: "Submit response", exact: true })
      .click();
    if (scenario === "lost") {
      await expect(
        common.getByRole("button", { name: "Reconcile response request" }),
      ).toBeVisible();
      await page.reload();
      await expect(
        common.getByRole("button", { name: "Reconcile response request" }),
      ).toBeVisible();
      expect(requests).toHaveLength(1);
      await expect(
        common.getByRole("button", { name: "Submit response", exact: true }),
      ).toBeDisabled();
      await common
        .getByRole("button", { name: "Reconcile response request" })
        .click();
      expect(requests[1]).toEqual(requests[0]);
    } else if (scenario === "schema" || scenario === "stale") {
      await expect(common.getByRole("alert")).toContainText(
        scenario === "schema" ? "recorded schema" : "evidence changed",
      );
      expect(stage).toBe(0);
      expect(requests).toHaveLength(1);
      await expect(
        common.getByRole("button", { name: "Reconcile response request" }),
      ).toHaveCount(0);
      if (scenario === "schema") {
        await common
          .getByRole("button", { name: "Submit response", exact: true })
          .click();
        expect(requests[1].request_id).not.toBe(requests[0].request_id);
      } else {
        await common
          .getByRole("button", { name: "Refresh view", exact: true })
          .click();
        await expect(
          common.getByRole("button", { name: "Submit response", exact: true }),
        ).toBeDisabled();
      }
    }
    if (!stale) {
      await expect(
        common.getByText(
          "Choose the second comparison after reviewing its output.",
          { exact: true },
        ),
      ).toBeVisible();
      await page
        .getByTestId("editor-tabs-container")
        .locator('[data-testid^="editor-tab-close-/.wright/process-views/"]')
        .click();
      await expect(common).toHaveCount(0);
      await page.goto(savedUrl);
      await expect(
        common.getByText(
          "Choose the second comparison after reviewing its output.",
          { exact: true },
        ),
      ).toBeVisible();
      expect(fixture.starts()).toBe(1);
      await common.getByLabel("selection (required)").selectOption("0");
      await common
        .getByRole("button", { name: "Submit response", exact: true })
        .click();
      await expect(
        common.getByText("Completed · Run details", { exact: true }),
      ).toBeVisible();
      await page.reload();
      await expect(
        common.getByText("Completed · Run details", { exact: true }),
      ).toBeVisible();
      expect(recorded.size).toBe(2);
      await expect(
        common.getByRole("button", { name: "Submit response", exact: true }),
      ).toHaveCount(0);
    }
    expect(fixture.starts()).toBe(1);
    expect(fixture.cancellations()).toBe(0);
    expect(fixture.editor.runCount()).toBe(0);
    await page.screenshot({
      path: testInfo.outputPath(`two-input-${scenario}.png`),
      fullPage: true,
    });
    await testInfo.attach("checked-two-input-scope.json", {
      contentType: "application/json",
      body: Buffer.from(
        JSON.stringify(
          {
            browser: browser.version(),
            viewport: page.viewportSize(),
            url: page.url(),
            scenario,
            process: fixture.process,
            run_id: fixtureRunId,
            starts: fixture.starts(),
            cancellations: fixture.cancellations(),
            requests,
            retained_responses: [...recorded.values()],
            final_stage: stage,
            controlled_http_contracts: true,
            live_backend: false,
            live_model: false,
            live_mcp: false,
            hardware: false,
          },
          null,
          2,
        ),
      ),
    });
  });
}

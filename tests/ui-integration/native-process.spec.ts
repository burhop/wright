import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// Browser integration against an explicitly simulated service. Real API/runtime acceptance is separate.
const contractRoot = resolve("specs/079-wright-native-authoring/contracts");
const schema = JSON.parse(
  readFileSync(resolve(contractRoot, "native-process.schema.json"), "utf8"),
);
const definitions = ["concept-brief", "mass-check", "package-review"].map(
  (id) =>
    JSON.parse(
      readFileSync(resolve(contractRoot, "examples", id + ".json"), "utf8"),
    ),
);
const examples = definitions.map((definition) => ({
  id: definition.id,
  title: definition.title,
  definition,
  presentation: Object.fromEntries(
    definition.steps.map((step: { id: string }, index: number) => [
      step.id,
      { x: (index % 3) * 300, y: Math.floor(index / 3) * 220 },
    ]),
  ),
}));
const capacityDefinition = {
  format: "wright-native-process",
  schema_version: "1.0.0",
  id: "capacity-example",
  title: "25-step authoring fixture",
  steps: Array.from({ length: 25 }, (_, index) => ({
    id: `input-step-${index}`,
    title: `Engineering input ${index + 1}`,
    operation: "text.input@1",
    config: { value: `Input ${index + 1}` },
  })),
  ports: Array.from({ length: 25 }, (_, index) => ({
    id: `input-port-${index}`,
    step_id: `input-step-${index}`,
    key: "value",
    label: "value",
    direction: "output",
    type: "text",
    cardinality: "one",
    required: true,
  })),
  connections: [],
  outputs: [],
};
examples.push({
  id: capacityDefinition.id,
  title: capacityDefinition.title,
  definition: capacityDefinition,
  presentation: Object.fromEntries(
    capacityDefinition.steps.map((step, index) => [
      step.id,
      { x: (index % 5) * 300, y: Math.floor(index / 5) * 220 },
    ]),
  ),
});
const contract = {
  format: "wright-native-process",
  schema_version: "1.0.0",
  schema,
  canonicalization: "wright-native-json-v1",
  operations: schema.$defs.step.allOf.map((condition: any) => {
    const id = condition.if.properties.operation.const;
    const sample = definitions
      .flatMap((definition) =>
        definition.steps.map((step: any) => ({ definition, step })),
      )
      .find((item: any) => item.step.operation === id);
    const ports = sample
      ? sample.definition.ports.filter(
          (port: any) => port.step_id === sample.step.id,
        )
      : [];
    return {
      id,
      inputs: ports
        .filter((port: any) => port.direction === "input")
        .map(({ key, type }: any) => ({
          key,
          type,
          cardinality: "one",
          required: true,
        })),
      outputs: ports
        .filter((port: any) => port.direction === "output")
        .map(({ key, type }: any) => ({
          key,
          type,
          cardinality: "one",
          required: true,
        })),
      config_schema: condition.then.properties.config,
      required_config_keys: [],
    };
  }),
};
async function mockService(page: Page) {
  const records = new Map<string, any>();
  const writes: any[] = [];
  let conflict = false;
  await page.route("**/api/**", async (route) => {
    const request = route.request(),
      url = new URL(request.url()),
      path = url.pathname;
    if (path.startsWith("/api/native-processes")) {
      expect(url.searchParams.get("session_id")).toBe("native-test-session");
      if (path.endsWith("/contract")) return route.fulfill({ json: contract });
      if (path.endsWith("/examples"))
        return route.fulfill({ json: { examples } });
      if (path.endsWith("/runs") && request.method() === "GET")
        return route.fulfill({ json: { runs: [], next_cursor: null } });
      if (path.endsWith("/check"))
        return route.fulfill({
          json: { structurally_valid: true, ready: true, findings: [] },
        });
      if (request.method() === "POST" || request.method() === "PUT") {
        const body = request.postDataJSON();
        writes.push(body);
        if (conflict)
          return route.fulfill({
            status: 409,
            json: {
              code: "NATIVE_CONFLICT",
              message: "Another client saved this process.",
              recovery: "Reload or save a copy.",
              trace_id: "simulated-conflict",
            },
          });
        const revision = (records.get(body.definition.id)?.revision ?? 0) + 1;
        const envelope = {
          definition: body.definition,
          presentation: body.presentation,
          revision,
          token: String(revision).repeat(64),
          semantic_digest: createHash("sha256")
            .update(JSON.stringify(body.definition))
            .digest("hex"),
          updated_at: "2026-09-04T12:00:00Z",
        };
        records.set(body.definition.id, envelope);
        return route.fulfill({
          status: request.method() === "POST" ? 201 : 200,
          json: envelope,
        });
      }
      const id = path.replace("/api/native-processes", "").replace(/^\//, "");
      if (id) return route.fulfill({ json: records.get(id) });
      return route.fulfill({
        json: {
          documents: [...records.values()].map((record) => ({
            id: record.definition.id,
            title: record.definition.title,
            revision: record.revision,
            token: record.token,
            updated_at: record.updated_at,
          })),
          next_cursor: null,
        },
      });
    }
    if (path === "/api/auth/session/status")
      return route.fulfill({
        json: { auth_required: false, authenticated: true },
      });
    if (path === "/api/setup/status")
      return route.fulfill({
        json: { is_configured: true, active_agent: "hermes", theme: "dark" },
      });
    if (path === "/api/workspace/list" || path === "/api/workspace/recent")
      return route.fulfill({
        json: {
          workspaces: [
            {
              workspace_id: "native-workspace",
              session_id: "native-test-session",
              workspace_name: "Simulated engineering workspace",
              local_path: "/simulated/workspace",
              git_remote_url: null,
              git_username: null,
              updated_at: 1,
            },
          ],
        },
      });
    if (path === "/api/agent/sessions")
      return route.fulfill({ json: { sessions: [] } });
    if (path === "/api/mcp/servers")
      return route.fulfill({ json: { servers: [] } });
    if (path === "/api/mcp/tools")
      return route.fulfill({ json: { tools: [] } });
    if (path.endsWith("/health"))
      return route.fulfill({ json: { state: "connected", latencyMs: 1 } });
    return route.fulfill({
      status: 404,
      json: { detail: "No simulated API handler" },
    });
  });
  return {
    records,
    writes,
    setConflict: () => {
      conflict = true;
    },
  };
}
async function source(page: Page) {
  return JSON.parse(await page.getByTestId("native-source").inputValue());
}
async function mockRunService(
  page: Page,
  savedRecords: Map<string, any>,
  initial: "failed" | "succeeded" | "running" = "failed",
) {
  const runs = new Map<string, any>(),
    submissions: any[] = [];
  const content = Buffer.from("Verified fixture artifact\n", "utf8");
  const digest = createHash("sha256").update(content).digest("hex");
  let tamper = false,
    unavailable = false,
    cancellations = 0;
  await page.route("**/api/native-processes/**", async (route) => {
    const request = route.request(),
      path = new URL(request.url()).pathname;
    const historyMatch = /^\/api\/native-processes\/([^/]+)\/runs$/.exec(path);
    if (historyMatch) {
      if (request.method() === "GET")
        return route.fulfill({
          json: {
            runs: [...runs.values()]
              .filter((run) => run.process_id === historyMatch[1])
              .reverse(),
            next_cursor: null,
          },
        });
      const body = request.postDataJSON(),
        saved = savedRecords.get(historyMatch[1]);
      submissions.push(body);
      expect(body.expected_token).toBe(saved.token);
      const id = `run-${runs.size + 1}`,
        state = body.derived_from_run_id ? "succeeded" : initial;
      const reason = {
        code: "NATIVE_ASSERTION_FAILED",
        message: "Fixture assertion did not match.",
        recovery: "Correct the terms, save, and rerun.",
        step_id: "brief-check",
        port_id: null,
      };
      const run = {
        run_id: id,
        process_id: saved.definition.id,
        state,
        semantic_digest: saved.semantic_digest,
        created_at: "2026-09-04T12:00:00Z",
        started_at: "2026-09-04T12:00:01Z",
        completed_at: state === "running" ? null : "2026-09-04T12:00:02Z",
        derived_from_run_id: body.derived_from_run_id,
        reason: state === "failed" ? reason : null,
        trace_id: `trace-${id}`,
        snapshot: {
          definition: saved.definition,
          revision: saved.revision,
          token: saved.token,
          semantic_digest: saved.semantic_digest,
        },
        bindings: body.bindings,
        actor: "simulated-engineer",
        timeout_seconds: body.timeout_seconds,
        steps: saved.definition.steps.map((step: any) => ({
          step_id: step.id,
          operation: step.operation,
          state:
            state === "running"
              ? "pending"
              : state === "failed" && step.id === "brief-check"
                ? "failed"
                : state === "failed" && step.id === "brief-file"
                  ? "blocked"
                  : "succeeded",
          started_at: null,
          completed_at: null,
          inputs: {},
          outputs: {},
          reason:
            state === "failed" && step.id === "brief-check" ? reason : null,
        })),
        artifacts:
          state === "succeeded"
            ? [
                {
                  artifact_id: `artifact-${id}`,
                  step_id: "brief-file",
                  port_id: "brief-file-output-artifact",
                  filename: "fixture-brief.md",
                  content_digest: digest,
                  size: content.length,
                  media_type: "text/markdown",
                  provenance: {
                    operation: "artifact.write-text@1",
                    semantic_digest: saved.semantic_digest,
                    input_port: "brief-file-input-text",
                    fixture_mode: "simulated_runtime",
                  },
                },
              ]
            : [],
        last_sequence: 3,
      };
      runs.set(id, run);
      return route.fulfill({
        status: 202,
        json: { run_id: id, state, semantic_digest: saved.semantic_digest },
      });
    }
    const runMatch = /^\/api\/native-processes\/runs\/([^/]+)(.*)$/.exec(path);
    if (!runMatch) return route.fallback();
    const run = runs.get(runMatch[1]),
      suffix = runMatch[2];
    if (suffix === "/cancel") {
      cancellations++;
      run.state = "cancelled";
      run.last_sequence++;
      run.completed_at = "2026-09-04T12:00:03Z";
      return route.fulfill({ json: run });
    }
    if (suffix.startsWith("/artifacts/")) {
      const bytes = tamper
        ? Buffer.concat([Buffer.from("X"), content.subarray(1)])
        : content;
      return route.fulfill({
        body: bytes,
        contentType: "text/markdown",
        headers: {
          "X-Content-SHA256": digest,
          "Content-Disposition": 'attachment; filename="fixture-brief.md"',
        },
      });
    }
    if (suffix === "/events")
      return route.fulfill({
        json: {
          events: [
            {
              sequence: 3,
              occurred_at: "2026-09-04T12:00:02Z",
              kind: "fixture_run_state",
              payload: { state: run.state },
              trace_id: run.trace_id,
            },
          ],
          next_sequence: 3,
        },
      });
    if (unavailable)
      return route.fulfill({
        status: 503,
        json: {
          code: "NATIVE_RUNTIME_BUSY",
          message: "Simulated service unavailable.",
          recovery: "Reconnect.",
        },
      });
    return route.fulfill({ json: run });
  });
  return {
    submissions,
    content,
    digest,
    setTamper: () => {
      tamper = true;
    },
    setUnavailable: (value: boolean) => {
      unavailable = value;
    },
    cancellations: () => cancellations,
  };
}
async function openExample(page: Page, id = "concept-brief") {
  await page.goto("/native-processes");
  await page.getByTestId("native-example-list").selectOption(id);
  await page.getByTestId("native-open-example").click();
  await expect(page.locator(".react-flow__node")).toHaveCount(
    definitions.find((definition) => definition.id === id).steps.length,
  );
}
test.describe("Native authoring with a simulated service", () => {
  test("creates and connects from keyboard controls, saves and reopens exact language identities", async ({
    page,
  }, info) => {
    const service = await mockService(page);
    await page.goto("/native-processes");
    await page.getByTestId("native-operation").selectOption("text.input@1");
    await page.getByTestId("native-add-step").focus();
    await page.keyboard.press("Enter");
    await page.getByTestId("native-config-value").fill("Engineering claim.");
    await page.getByTestId("native-apply-step").click();
    await page
      .getByTestId("native-operation")
      .selectOption("artifact.write-text@1");
    await page.getByTestId("native-add-step").click();
    await page.getByTestId("native-config-filename").fill("brief.md");
    await page.getByTestId("native-apply-step").click();
    const before = await source(page);
    const from = before.ports.find(
      (port: any) => port.direction === "output" && port.type === "text",
    );
    const to = before.ports.find(
      (port: any) => port.direction === "input" && port.type === "text",
    );
    await page.getByTestId("native-connect-source").selectOption(from.id);
    await page.getByTestId("native-connect-target").selectOption(to.id);
    await page.getByTestId("native-connect").focus();
    await page.keyboard.press("Enter");
    await expect(page.locator(".react-flow__edge")).toHaveCount(1);
    const output = before.ports.find((port: any) => port.type === "artifact");
    await page.getByTestId(`native-declare-${output.id}`).check();
    const expected = await source(page);
    expect(expected.connections[0]).toMatchObject({
      source_port_id: from.id,
      target_port_id: to.id,
    });
    await page.getByTestId("native-save").click();
    await expect(page.getByTestId("native-status")).toContainText(
      "Saved revision 1",
    );
    expect(service.writes).toHaveLength(1);
    expect(service.writes[0].definition).toEqual(expected);
    await page.screenshot({
      path: info.outputPath("authoring-desktop.png"),
      fullPage: true,
    });
    await page
      .getByTestId("native-canvas")
      .screenshot({ path: info.outputPath("authoring-canvas.png") });
    await page.reload();
    await page.getByTestId("native-saved-list").selectOption(expected.id);
    await page.getByTestId("native-open").click();
    await expect(page.getByTestId("native-status")).toContainText(
      "Opened saved revision 1",
    );
    expect(await source(page)).toEqual(expected);
    await expect(page.locator(".react-flow__edge")).toHaveCount(1);
  });
  test("projects programmatic endpoints, preserves semantics while moving, and reviews deletion with undo", async ({
    page,
  }) => {
    await mockService(page);
    await openExample(page);
    const before = await source(page);
    for (const connection of before.connections) {
      await expect(
        page.locator(`.react-flow__edge[data-id="${connection.id}"]`),
      ).toHaveCount(1);
      await expect(
        page.locator(`[data-handleid="${connection.source_port_id}"]`),
      ).toHaveCount(1);
      await expect(
        page.locator(`[data-handleid="${connection.target_port_id}"]`),
      ).toHaveCount(1);
    }
    const node = page.locator(
      `.react-flow__node[data-id="${before.steps[0].id}"]`,
    );
    await node.focus();
    await page.keyboard.press("Enter");
    await expect(node).toHaveClass(/selected/);
    const priorPosition = await node.getAttribute("style");
    await page.keyboard.press("ArrowRight");
    await expect(node).not.toHaveAttribute("style", priorPosition!);
    expect(await source(page)).toEqual(before);
    await page
      .getByTestId("native-step-list")
      .selectOption(before.steps.at(-1).id);
    await page.getByTestId("native-review-delete").click();
    await expect(
      page.getByRole("region", { name: "Step deletion impact" }),
    ).toContainText("declared outputs");
    await page.getByTestId("native-confirm-delete").click();
    expect((await source(page)).outputs).toHaveLength(0);
    await page.getByTestId("native-undo").click();
    expect(await source(page)).toEqual(before);
  });
  test("retains a stale writer's draft and traps confirmation focus", async ({
    page,
  }) => {
    const service = await mockService(page);
    await openExample(page);
    await page.getByTestId("native-save").click();
    await expect(page.getByTestId("native-status")).toContainText(
      "Saved revision",
    );
    await page.getByTestId("native-process-title").fill("Keep this work");
    await page.getByTestId("native-apply-title").click();
    service.setConflict();
    await page.getByTestId("native-save").click();
    await expect(page.getByTestId("native-error")).toContainText(
      "Another client",
    );
    expect((await source(page)).title).toBe("Keep this work");
    await page.getByTestId("native-load-current").click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByTestId("native-stay")).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(page.getByTestId("native-leave")).toBeFocused();
    await page.keyboard.press("Escape");
    expect((await source(page)).title).toBe("Keep this work");
  });
  test("supports narrow layout, 200 percent zoom and automated accessibility checks", async ({
    page,
  }, info) => {
    await mockService(page);
    await openExample(page);
    await page.getByTestId("native-step-list").selectOption("need-source");
    const results = await new AxeBuilder({ page })
      .include('[data-testid="page-native-process"]')
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
    await page.setViewportSize({ width: 640, height: 1000 });
    const dimensions = await page.evaluate(() => ({
      width: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.width + 1);
    await expect(page.getByTestId("native-connect-source")).toBeVisible();
    await page.screenshot({
      path: info.outputPath("authoring-narrow.png"),
      fullPage: true,
    });
    await page
      .getByTestId("native-canvas")
      .screenshot({ path: info.outputPath("authoring-narrow-canvas.png") });
    await page.setViewportSize({ width: 1280, height: 1000 });
    await page.evaluate(() => {
      document.documentElement.style.zoom = "2";
    });
    await page.getByTestId("native-step-title").focus();
    await expect(page.getByTestId("native-step-title")).toBeFocused();
    const zoomed = await page.evaluate(() => ({
      width: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(zoomed.scroll).toBeLessThanOrEqual(zoomed.width + 1);
    await page.screenshot({
      path: info.outputPath("authoring-200-percent.png"),
      fullPage: true,
    });
  });
  test("records 20 warm opens of a 25-step fixture without losing identities", async ({
    page,
  }, info) => {
    test.setTimeout(60000);
    await mockService(page);
    await page.goto("/native-processes");
    await page
      .getByTestId("native-example-list")
      .selectOption("capacity-example");
    const observations: number[] = [];
    for (let attempt = 0; attempt < 20; attempt++) {
      const started = Date.now();
      await page.getByTestId("native-open-example").click();
      if (attempt > 0) await page.getByTestId("native-leave").click();
      await expect(page.locator(".react-flow__node")).toHaveCount(25);
      expect((await source(page)).steps.map((step: any) => step.id)).toEqual(
        capacityDefinition.steps.map((step) => step.id),
      );
      observations.push(Date.now() - started);
    }
    // Includes browser automation overhead; diagnostic, not an invented microbenchmark pass threshold.
    const observationsPath = info.outputPath(
      "25-step-warm-open-observations.json",
    );
    writeFileSync(
      observationsPath,
      JSON.stringify(
        {
          mode: "simulated_service_actual_browser",
          milliseconds: observations,
        },
        null,
        2,
      ),
    );
    await info.attach("25-step-warm-open-observations", {
      path: observationsPath,
      contentType: "application/json",
    });
  });
});

test.describe("Native run inspection with a simulated runtime and actual browser bytes", () => {
  test("fails, corrects, saves a linked rerun and verifies/downloads actual artifact bytes", async ({
    page,
  }, info) => {
    const service = await mockService(page),
      runtime = await mockRunService(page, service.records);
    await openExample(page);
    await expect(page.getByTestId("native-run-start")).toBeDisabled();
    await page.getByTestId("native-save").click();
    await expect(page.getByTestId("native-status")).toContainText(
      "Saved revision",
    );
    await page.getByTestId("native-run-start").click();
    await expect(page.getByTestId("native-run-state")).toHaveText("failed");
    await expect(page.getByTestId("native-run-reason")).toContainText(
      "Correct the terms",
    );
    await page.getByTestId("native-correct-brief-check").click();
    await page
      .getByTestId("native-config-terms")
      .fill("Verified fixture artifact");
    await page.getByTestId("native-apply-step").click();
    await expect(page.getByTestId("native-run-derived")).toBeDisabled();
    await page.getByTestId("native-save").click();
    await expect(page.getByTestId("native-status")).toContainText(
      "Saved revision 2",
    );
    await page.getByTestId("native-run-derived").click();
    await expect(page.getByTestId("native-run-state")).toHaveText("succeeded");
    expect(runtime.submissions[1].derived_from_run_id).toBe("run-1");
    await page.getByTestId("native-inspect-artifact-artifact-run-2").click();
    await expect(
      page.getByTestId("native-artifact-content-artifact-run-2"),
    ).toHaveValue(runtime.content.toString("utf8"));
    await page.getByTestId("native-provenance-artifact-run-2").click();
    await expect(
      page.getByTestId("native-artifact-artifact-run-2"),
    ).toContainText("simulated_runtime");
    const downloadPromise = page.waitForEvent("download");
    await page.getByTestId("native-download-artifact-run-2").click();
    const download = await downloadPromise,
      bytes = readFileSync((await download.path())!);
    expect(createHash("sha256").update(bytes).digest("hex")).toBe(
      runtime.digest,
    );
    const results = await new AxeBuilder({ page })
      .include('[data-testid="native-run-panel"]')
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
    await page
      .getByTestId("native-artifact-artifact-run-2")
      .screenshot({ path: info.outputPath("verified-artifact.png") });
  });
  test("rejects altered artifact bytes without exposing a preview or download", async ({
    page,
  }) => {
    const service = await mockService(page),
      runtime = await mockRunService(page, service.records, "succeeded");
    await openExample(page);
    await page.getByTestId("native-save").click();
    await expect(page.getByTestId("native-status")).toContainText(
      "Saved revision",
    );
    await page.getByTestId("native-run-start").click();
    await expect(page.getByTestId("native-run-state")).toHaveText("succeeded");
    runtime.setTamper();
    await page.getByTestId("native-inspect-artifact-artifact-run-1").click();
    await expect(
      page.getByTestId("native-artifact-artifact-run-1"),
    ).toContainText("Artifact digest does not match");
    await expect(
      page.getByTestId("native-download-artifact-run-1"),
    ).toHaveCount(0);
    await expect(
      page.getByTestId("native-artifact-content-artifact-run-1"),
    ).toHaveCount(0);
  });
  test("reconnects to a retained running snapshot and cancels through the service", async ({
    page,
  }) => {
    const service = await mockService(page),
      runtime = await mockRunService(page, service.records, "running");
    await openExample(page);
    await page.getByTestId("native-save").click();
    await expect(page.getByTestId("native-status")).toContainText(
      "Saved revision",
    );
    await page.getByTestId("native-run-start").click();
    await expect(page.getByTestId("native-run-state")).toHaveText("running");
    runtime.setUnavailable(true);
    await page.getByTestId("native-run-refresh").click();
    await expect(page.getByTestId("native-run-disconnected")).toBeVisible();
    await expect(page.getByTestId("native-run-state")).toHaveText("running");
    runtime.setUnavailable(false);
    await page.getByTestId("native-run-reconnect").click();
    await expect(page.getByTestId("native-run-disconnected")).toHaveCount(0);
    await page.getByTestId("native-run-cancel").click();
    await expect(page.getByTestId("native-run-state")).toHaveText("cancelled");
    expect(runtime.cancellations()).toBe(1);
    await expect(page.getByTestId("native-run-cancel")).toHaveCount(0);
  });
});

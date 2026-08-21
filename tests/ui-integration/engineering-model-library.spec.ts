import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page, type Request } from "@playwright/test";

const digest = "d".repeat(64);
const observationDigest = "e".repeat(64);

const snapshot = {
  snapshot_id: "bundled-models-1",
  catalog_digest: digest,
  freshness: "bundled",
  offline: true,
  channel: "bundled",
  sequence: 1,
};

const approvedModel = {
  model_id: "wright-affine-test",
  display_name: "Wright affine engineering fixture",
  description: "Deterministic typed engineering-model lifecycle fixture.",
  tasks: ["predict"],
  source: {
    kind: "wright",
    uri: "wright://generated/affine",
    immutable_revision: digest,
    access: "public",
  },
  license: {
    expression: "MIT",
    attribution: "Wright deterministic test fixture.",
    redistribution: "allowed",
    acceptance_required: false,
  },
  readiness: "approved",
  compatibility: { state: "compatible", reasons: [] },
  evidence: {
    source: "bundled",
    license: "bundled",
    runtime: "bundled",
    test: "bundled",
  },
  limitations: [
    {
      limitation_id: "test-only",
      description: "Test-only affine behavior; not a production design model.",
    },
  ],
  variants: [
    {
      variant_id: "json-cpu-f64",
      format: "wright-affine-json",
      precision: "float64",
      accelerator: "none",
      resources: {
        download_bytes: 256,
        installed_bytes: 256,
        ram_bytes: 1_048_576,
      },
      compatibility: { state: "compatible", reasons: [] },
    },
  ],
  blockers: [],
  generator: {
    kind: "deterministic_recipe",
    recipe: "Generate bounded affine coefficients and exact vectors.",
    inputs: { scale: 2, offset: 1 },
    constraints: ["No network", "No model weights in Git"],
    manifest_digest: digest,
    artifact_set_digest: observationDigest,
  },
  manifest_digest: digest,
  entry_digest: observationDigest,
  snapshot,
};

const blockedModel = {
  ...approvedModel,
  model_id: "external-point-cloud-candidate",
  display_name: "External point-cloud candidate",
  description: "Visible for evidence review but not installable.",
  source: {
    kind: "huggingface",
    uri: "https://huggingface.co/example/point-cloud",
    immutable_revision: "a".repeat(40),
    access: "public",
  },
  license: {
    expression: "Apache-2.0",
    attribution: "Publisher model-card attribution.",
    redistribution: "review_required",
    acceptance_required: false,
  },
  readiness: "needs_review",
  compatibility: {
    state: "blocked",
    reasons: ["Exact runtime and vector evidence are incomplete."],
  },
  variants: [],
  blockers: [
    {
      category: "runtime_missing",
      message: "The separately reviewed runtime is not available.",
      recovery: "Keep this candidate evaluation-only until Gate D passes.",
    },
  ],
  generator: null,
  manifest_digest: "f".repeat(64),
  entry_digest: "1".repeat(64),
};

function plan() {
  return {
    schema_version: "1.0",
    plan_id: "plan-browser-1",
    plan_digest: digest,
    principal_id: "local-engineer",
    operation_kind: "install",
    model_id: approvedModel.model_id,
    package_revision: 1,
    variant_id: "json-cpu-f64",
    snapshot_id: snapshot.snapshot_id,
    manifest_digest: approvedModel.manifest_digest,
    effects: [
      {
        kind: "write",
        description: "Stage and verify declared deterministic data.",
        safe_location: "Wright model cache",
        exact_bytes: 256,
        maximum_bytes: 256,
        reversible: true,
      },
      {
        kind: "activate",
        description: "Activate only after exact verification.",
        maximum_bytes: 0,
        reversible: true,
      },
    ],
    blockers: [],
    requirements: {
      network: "none",
      credential: "none",
      license_action: "none",
      runtime_change: "none",
    },
    compatibility: { state: "compatible" },
    prompts: [],
    runtime_requirement: { adapter_id: "wright-deterministic" },
    references: [],
    rollback: "Remove the inactive installation projection.",
    cleanup: "Delete operation staging and preserve verified shared bytes.",
    created_at: "2026-08-13T12:00:00Z",
    expires_at: "2099-08-13T12:10:00Z",
    state: "confirmable",
  };
}

function operation(state: "running" | "cancelled" | "succeeded") {
  return {
    schema_version: "1.0",
    operation_id: "operation-browser-1",
    plan_id: "plan-browser-1",
    plan_digest: digest,
    kind: "install",
    state,
    phase: state === "running" ? "verifying" : state,
    progress: {
      completed_items: state === "succeeded" ? 1 : 0,
      total_items: 1,
      completed_bytes: state === "succeeded" ? 256 : 128,
      maximum_bytes: 256,
      message:
        state === "running"
          ? "Verifying immutable content."
          : state === "cancelled"
            ? "Cancelled before activation."
            : "Installed without claiming runtime readiness.",
    },
    result:
      state === "succeeded"
        ? { installation_id: "installation-browser-1" }
        : null,
    cleanup_state: state === "running" ? "pending" : "clean",
    trace_id: "trace-browser-1",
    created_at: "2026-08-13T12:00:00Z",
    updated_at: "2026-08-13T12:00:01Z",
  };
}

async function mockModelLibrary(page: Page) {
  let confirmCount = 0;
  let archived = false;
  let maintenanceState = "ready";
  const maintenancePlans = new Map<string, { kind: string; target?: string }>();
  const observedRequests: Request[] = [];
  page.on("request", (request) => observedRequests.push(request));

  await page.route("**/api/**", (route) => route.fulfill({ json: {} }));
  await page.route("**/api/auth/session/status", (route) =>
    route.fulfill({ json: { auth_required: false, authenticated: true } }),
  );
  await page.route("**/api/setup/status", (route) =>
    route.fulfill({
      json: { is_configured: true, active_agent: "hermes", theme: "dark" },
    }),
  );
  await page.route("**/api/mcp/servers", (route) =>
    route.fulfill({ json: { servers: [] } }),
  );
  await page.route("**/api/mcp/tools", (route) =>
    route.fulfill({ json: { tools: [] } }),
  );
  await page.route("**/api/v1/engineering-models/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path.endsWith("/catalog")) {
      return route.fulfill({
        json: {
          snapshot,
          models: [approvedModel, blockedModel],
          next_cursor: null,
          total: 2,
        },
      });
    }
    if (path.endsWith(`/catalog/${approvedModel.model_id}`))
      return route.fulfill({ json: approvedModel });
    if (path.endsWith(`/catalog/${blockedModel.model_id}`))
      return route.fulfill({ json: blockedModel });
    if (path.endsWith("/installations") && method === "GET") {
      return route.fulfill({
        json: {
          installations:
            confirmCount >= 2
              ? [
                  {
                    installation_id: "installation-browser-1",
                    model_id: approvedModel.model_id,
                    package_revision: 1,
                    variant_id: "json-cpu-f64",
                    manifest_digest: digest,
                    state: maintenanceState,
                    active_revision: true,
                    runtime_adapter_id: "wright-deterministic",
                    runtime_adapter_version: "1.0.0",
                    installed_at: "2026-08-13T12:00:00Z",
                  },
                ]
              : [],
        },
      });
    }
    if (path.endsWith("/plans") && method === "POST") {
      const body = request.postDataJSON() as {
        operation_kind: string;
        target_installation_id?: string;
      };
      if (body.operation_kind === "install")
        return route.fulfill({ json: plan() });
      const planId = `plan-${body.operation_kind}`;
      maintenancePlans.set(planId, {
        kind: body.operation_kind,
        target: body.target_installation_id,
      });
      return route.fulfill({
        json: {
          ...plan(),
          plan_id: planId,
          operation_kind: body.operation_kind,
          effects: [
            {
              kind: body.operation_kind === "purge" ? "delete" : "write",
              description: `Apply exact ${body.operation_kind} effects.`,
              maximum_bytes: body.operation_kind === "purge" ? 256 : 0,
              reversible: body.operation_kind !== "purge",
            },
          ],
        },
      });
    }
    if (path.endsWith("/plans/plan-browser-1/confirm")) {
      confirmCount += 1;
      return route.fulfill({
        json: operation(confirmCount === 1 ? "running" : "succeeded"),
      });
    }
    const maintenanceConfirmation = path.match(
      /\/plans\/(plan-[a-z]+)\/confirm$/,
    );
    if (maintenanceConfirmation) {
      const selected = maintenancePlans.get(maintenanceConfirmation[1]);
      if (!selected)
        return route.fulfill({ status: 404, json: { detail: "Unknown plan" } });
      const states: Record<string, string> = {
        rollback: "testing_required",
        disable: "disabled",
        uninstall: "uninstalled",
        purge: "succeeded",
      };
      maintenanceState = states[selected.kind] ?? maintenanceState;
      return route.fulfill({
        json: {
          ...operation("succeeded"),
          operation_id: `operation-${selected.kind}`,
          plan_id: maintenanceConfirmation[1],
          kind: selected.kind,
          result:
            selected.kind === "export"
              ? {
                  artifact_id: "export-a1",
                  sha256: "9".repeat(64),
                  size: 512,
                }
              : {
                  installation_id: "installation-browser-1",
                  state: maintenanceState,
                  target_installation_id: selected.target,
                },
        },
      });
    }
    if (path.endsWith("/operations/operation-browser-1/cancel"))
      return route.fulfill({ json: operation("cancelled") });
    if (path.endsWith("/standard-test") && method === "POST") {
      return route.fulfill({
        json: {
          installation_id: "installation-browser-1",
          installation_state: "ready",
          adapter_id: "wright-deterministic",
          adapter_version: "1.0.0",
          evidence: [
            {
              evidence_id: "evidence-browser-1",
              state: "passed",
              material_digest: digest,
              observation_digest: observationDigest,
            },
          ],
        },
      });
    }
    if (path.endsWith("/evidence")) {
      return route.fulfill({
        json: {
          installation_id: "installation-browser-1",
          installation_state: "installed",
          adapter_id: "wright-deterministic",
          adapter_version: "1.0.0",
          evidence: [],
        },
      });
    }
    if (path.endsWith("/bindings") && method === "POST") {
      return route.fulfill({
        json: {
          binding_id: "binding-browser-1",
          binding_digest: "b".repeat(64),
          workspace_id: "workspace-browser",
          installation_id: "installation-browser-1",
          task_id: "predict",
          tool_name: "wright_model__wright_affine_test__predict",
          policy_snapshot_digest: "c".repeat(64),
          state: "enabled",
        },
      });
    }
    if (path.endsWith("/compare-update")) {
      return route.fulfill({
        json: {
          current_manifest_digest: digest,
          candidate_manifest_digest: observationDigest,
          changed_facets: ["artifacts", "vectors", "limitations"],
          diff_digest: "a".repeat(64),
          requires_retest: true,
          requires_license_review: false,
        },
      });
    }
    if (path.includes("/references/") && method === "PATCH") {
      archived = true;
      return route.fulfill({
        json: { reference_id: "reference-workflow", state: "archived" },
      });
    }
    if (path.endsWith("/maintenance") && method === "GET") {
      return route.fulfill({
        json: {
          installation_id: "installation-browser-1",
          state: maintenanceState,
          active: true,
          reclaimable_bytes: 0,
          blockers: archived
            ? []
            : [
                {
                  kind: "workflow",
                  owner_id: "reviewed-workflow",
                  reference_id: "reference-workflow",
                },
              ],
          references: archived
            ? [
                {
                  kind: "workflow",
                  owner_id: "reviewed-workflow",
                  reference_id: "reference-workflow",
                  state: "archived",
                },
              ]
            : [],
        },
      });
    }
    return route.fulfill({ status: 404, json: { detail: "Unmocked route" } });
  });

  return { observedRequests };
}

test.describe("Engineering model library", () => {
  test("supports an instrumented no-download decision path while offline", async ({
    page,
  }) => {
    const { observedRequests } = await mockModelLibrary(page);
    const started = Date.now();
    await page.goto("/engineering-models");
    await expect(page.getByTestId("model-snapshot-state")).toContainText(
      "Offline snapshot",
    );
    await page.getByTestId(`model-inspect-${blockedModel.model_id}`).click();
    const dialog = page.getByRole("dialog", {
      name: blockedModel.display_name,
    });
    await expect(dialog).toContainText("Apache-2.0");
    await expect(dialog).toContainText("runtime missing");
    await expect(dialog).toContainText("evaluation-only");
    expect(Date.now() - started).toBeLessThan(120_000);
    expect(
      observedRequests.filter(
        (request) =>
          request.method() !== "GET" &&
          (request.url().includes("huggingface.co") ||
            request.url().includes("/engineering-models/plans")),
      ),
    ).toEqual([]);
  });

  test("recovers from cancellation, proves readiness, and completes maintenance journeys", async ({
    page,
  }) => {
    await mockModelLibrary(page);
    await page.goto("/engineering-models");
    await page.getByTestId("model-workspace-id").fill("workspace-browser");
    const inspect = page.getByTestId(`model-inspect-${approvedModel.model_id}`);
    await inspect.click();
    let dialog = page.getByRole("dialog", { name: approvedModel.display_name });
    await dialog.getByTestId("model-install-review").click();
    await expect(dialog.getByTestId("model-install-plan")).toContainText(
      "Wright model cache",
    );
    await dialog.getByTestId("model-install-confirm").click();
    await expect(dialog.getByTestId("model-install-operation")).toContainText(
      "verifying",
    );
    await dialog.getByTestId("model-install-cancel").click();
    await expect(dialog.getByTestId("model-install-operation")).toContainText(
      "cancelled",
    );
    await expect(dialog.getByTestId("model-install-operation")).toContainText(
      "Cleanup: clean",
    );

    await dialog.getByTestId("model-detail-close").click();
    await inspect.click();
    dialog = page.getByRole("dialog", { name: approvedModel.display_name });
    await dialog.getByTestId("model-install-review").click();
    await dialog.getByTestId("model-install-confirm").click();
    await dialog
      .getByRole("button", { name: "Run mandatory standard test" })
      .click();
    await expect(dialog).toContainText("Ready for workspace use");
    await dialog.getByRole("button", { name: "Enable for workspace" }).click();
    await expect(dialog).toContainText(
      "wright_model__wright_affine_test__predict",
    );

    await dialog.getByTestId("model-detail-close").click();
    await inspect.click();
    dialog = page.getByRole("dialog", { name: approvedModel.display_name });
    await expect(dialog).toContainText("Maintain this exact installation");

    await expect(dialog).toContainText("reviewed-workflow");
    await dialog
      .getByRole("button", { name: "Archive reviewed-workflow" })
      .click();

    await dialog
      .getByRole("button", { name: "Compare available revision" })
      .click();
    await expect(
      dialog.getByRole("status").filter({ hasText: "Changed facets" }),
    ).toContainText("artifacts, vectors, limitations");
    await dialog
      .getByLabel("Rollback installation identity")
      .fill("installation-browser-0");
    await dialog.getByRole("button", { name: "Prepare rollback" }).click();
    await dialog.getByRole("button", { name: "Confirm rollback" }).click();
    await expect(dialog).toContainText("Current state: testing_required");

    await dialog.getByRole("button", { name: "Create offline export" }).click();
    await dialog.getByRole("button", { name: "Confirm export" }).click();
    await expect(dialog).toContainText("Export export-a1 is ready");
    await dialog.getByRole("button", { name: "Disable installation" }).click();
    await dialog.getByRole("button", { name: "Confirm disable" }).click();
    await dialog
      .getByRole("button", { name: "Uninstall but retain verified bytes" })
      .click();
    await dialog.getByRole("button", { name: "Confirm uninstall" }).click();
    await dialog.getByRole("button", { name: "Purge verified bytes" }).click();
    await dialog.getByRole("button", { name: "Confirm purge" }).click();
    await expect(dialog).toContainText("Current state: succeeded");
  });

  test("supports keyboard-only modal use, focus restoration, 200% zoom, and accessible status", async ({
    page,
  }) => {
    await mockModelLibrary(page);
    await page.setViewportSize({ width: 720, height: 900 });
    await page.goto("/engineering-models");
    const inspect = page.getByTestId(`model-inspect-${approvedModel.model_id}`);
    await inspect.focus();
    await page.keyboard.press("Enter");
    const dialog = page.getByRole("dialog", {
      name: approvedModel.display_name,
    });
    const close = dialog.getByTestId("model-detail-close");
    await expect(close).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(dialog).toContainText("Approved");
    expect(
      await dialog.evaluate((element) =>
        element.contains(document.activeElement),
      ),
    ).toBe(true);
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(inspect).toBeFocused();

    await inspect.press("Enter");
    await page.evaluate(() => {
      document.documentElement.style.zoom = "2";
    });
    await expect(
      page.getByRole("dialog", { name: approvedModel.display_name }),
    ).toBeVisible();
    const accessibility = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();
    expect(
      accessibility.violations.filter((violation) =>
        ["critical", "serious"].includes(violation.impact || ""),
      ),
    ).toEqual([]);
  });
});

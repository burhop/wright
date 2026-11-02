import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, type Page } from "@playwright/test";

const WORKSPACE_ID = "ws-recovery";
const SESSION_ID = "session-recovery";
export const WORKFLOW_PATH = "workflows/mounting-bracket.workflow.wflow";

export const publicWorkflowSource = readFileSync(
  resolve(
    process.cwd(),
    "specs/080-canonical-workflow-recovery/fixtures/mounting-bracket.workflow.wflow",
  ),
  "utf8",
);

interface WorkflowSourceDocument {
  workspace_id: string;
  path: string;
  storage_revision: number;
  storage_digest: string;
  definition_revision: number;
  metadata_authority: "wright_host";
  size_bytes: number;
  source: string;
  layout: Record<string, unknown> | null;
  layout_revision: number;
  layout_status: "missing" | "current" | "stale";
}

export interface RecoveryWorkspaceMock {
  current(): WorkflowSourceDocument | null;
  sourceAt(path: string): WorkflowSourceDocument | null;
  createCount(): number;
  missingReadCount(): number;
  runCount(): number;
  runRequestCount(): number;
  updateCount(): number;
  conflictNextUpdate(): void;
}

export interface RecoveryWorkflowRunMock {
  events: Array<Record<string, unknown>>;
  result: Record<string, unknown>;
  recentRuns?: Array<Record<string, unknown>>;
}

function workflowDocument(
  source: string,
  storageRevision: number,
  definitionRevision: number,
  path = WORKFLOW_PATH,
): WorkflowSourceDocument {
  return {
    workspace_id: WORKSPACE_ID,
    path,
    storage_revision: storageRevision,
    storage_digest: createHash("sha256").update(source, "utf8").digest("hex"),
    definition_revision: definitionRevision,
    metadata_authority: "wright_host",
    size_bytes: Buffer.byteLength(source, "utf8"),
    source,
    layout: null,
    layout_revision: 0,
    layout_status: "missing",
  };
}

function conflictEnvelope(current: WorkflowSourceDocument | null) {
  return {
    error_code: "workflow_source_conflict",
    message: "The workflow source changed after it was read",
    trace_id: "trace-workflow-recovery-test",
    details: {
      current_storage_revision: current?.storage_revision ?? 1,
      current_storage_digest: current?.storage_digest ?? "0".repeat(64),
    },
  };
}

export async function mockRecoveryWorkspace(
  page: Page,
  options: {
    source?: string | null;
    run?: RecoveryWorkflowRunMock;
    readiness?: "not_template" | "setup_required";
  } = {},
): Promise<RecoveryWorkspaceMock> {
  await page.addInitScript(() => {
    window.localStorage.setItem("wright.workspaceSurfaces.testEnabled", "1");
  });
  let document =
    options.source === null
      ? null
      : workflowDocument(options.source ?? publicWorkflowSource, 1, 2);
  let currentPath = WORKFLOW_PATH;
  const documents = new Map<string, WorkflowSourceDocument>();
  if (document !== null) documents.set(currentPath, document);
  let sourceReadiness: "not_template" | "setup_required" =
    options.readiness ?? "not_template";
  let creates = 0;
  let missingReads = 0;
  let runs = 0;
  let runRequests = 0;
  let updates = 0;
  let rejectNextUpdate = false;

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path === "/api/auth/session/status") {
      return route.fulfill({
        json: { auth_required: false, authenticated: true },
      });
    }
    if (path === "/api/setup/status") {
      return route.fulfill({
        json: { is_configured: true, active_agent: "hermes", theme: "dark" },
      });
    }
    if (
      path === "/api/health" ||
      path === "/api/agent/health" ||
      path === "/api/inference/health"
    ) {
      return route.fulfill({
        json: { status: "ok", state: "connected", latencyMs: 1 },
      });
    }
    if (path === "/api/mcp/servers")
      return route.fulfill({ json: { servers: [] } });
    if (path === "/api/mcp/servers/installed")
      return route.fulfill({ json: { servers: [] } });
    if (path === "/api/mcp/tools")
      return route.fulfill({ json: { tools: [] } });
    if (path === "/api/agent/commands") return route.fulfill({ json: [] });
    if (path === "/api/agent/active") return route.fulfill({ json: "hermes" });
    if (path === "/api/agent/models") {
      return route.fulfill({
        json: {
          current_value: null,
          current_provider: null,
          current_model: null,
          groups: [],
        },
      });
    }
    if (path === "/api/agent/sessions") {
      return route.fulfill({
        json: { sessions: [{ session_id: SESSION_ID, title: "Default" }] },
      });
    }
    if (path === `/api/agent/sessions/${SESSION_ID}/history`) {
      return route.fulfill({ json: { messages: [] } });
    }
    if (path === `/api/workspace/by-id/${WORKSPACE_ID}`) {
      return route.fulfill({
        json: {
          workspace_id: WORKSPACE_ID,
          session_id: SESSION_ID,
          workspace_name: "Bracket development",
          local_path: "D:/engineering/bracket-development",
        },
      });
    }
    if (path === `/api/workspace/by-id/${WORKSPACE_ID}/sessions`) {
      return route.fulfill({
        json: { sessions: [{ session_id: SESSION_ID, title: "Default" }] },
      });
    }
    if (path === `/api/workspace/by-id/${WORKSPACE_ID}/tools`) {
      return route.fulfill({
        json: { workspace_id: WORKSPACE_ID, enabled_tools: [] },
      });
    }
    if (path === `/api/workspace/by-id/${WORKSPACE_ID}/mcp-status`) {
      return route.fulfill({ json: { servers: [] } });
    }
    if (path === "/api/workspace/activate") {
      return route.fulfill({
        json: {
          success: true,
          session_id: SESSION_ID,
          workspace_path: "D:/engineering/bracket-development",
        },
      });
    }
    if (path === "/api/workspace/files") {
      return route.fulfill({
        json: {
          workspace: {
            name: "bracket-development",
            path: "/",
            type: "directory",
            children: [...documents.keys()].map((workflowPath) => ({
              name: workflowPath.split("/").at(-1)!,
              path: `/${workflowPath}`,
              type: "file",
              children: null,
            })),
          },
        },
      });
    }
    if (path === "/api/workspace/git/status") {
      return route.fulfill({ json: { branch: "codex/test", files: [] } });
    }
    if (path === "/api/workspace/surfaces/events") {
      return route.fulfill({
        contentType: "text/event-stream",
        body: ": keepalive\n\n",
      });
    }
    if (path === "/api/workspace/surfaces") {
      return route.fulfill({ json: { items: [] } });
    }
    if (
      path === "/api/workspace/workflow-sources/input-files" &&
      method === "GET"
    ) {
      if (url.searchParams.get("session_id") !== SESSION_ID) {
        return route.fulfill({
          status: 404,
          json: { message: "Workspace not found" },
        });
      }
      return route.fulfill({
        headers: { "Cache-Control": "no-store" },
        json: {
          workspace_id: WORKSPACE_ID,
          files: [
            { path: "design/requirements.md", name: "requirements.md" },
            { path: "references/bracket.png", name: "bracket.png" },
          ],
        },
      });
    }
    if (
      path === "/api/workspace/workflow-sources/reviews" &&
      method === "GET"
    ) {
      return route.fulfill({ json: { reviews: [] } });
    }
    if (path === "/api/workspace/workflow-sources/runs" && method === "GET") {
      return route.fulfill({
        headers: { "Cache-Control": "no-store" },
        json: {
          workspace_id: WORKSPACE_ID,
          workflow_path: currentPath,
          runs: options.run?.recentRuns ?? [],
        },
      });
    }
    if (path === "/api/workspace/workflow-sources/run" && method === "POST") {
      runRequests += 1;
      if (!options.run || !document) {
        return route.fulfill({
          status: 501,
          json: { detail: { message: "No workflow run was configured" } },
        });
      }
      const body = request.postDataJSON() as {
        session_id: string;
        path: string;
        expected_storage_digest: string;
      };
      if (
        body.session_id !== SESSION_ID ||
        body.path !== currentPath ||
        body.expected_storage_digest !== document.storage_digest
      ) {
        return route.fulfill({
          status: 409,
          json: { detail: { message: "Run subject did not match" } },
        });
      }
      runs += 1;
      const terminal =
        typeof options.run.result.status === "string" &&
        ["pending_review", "awaiting_approval"].includes(
          options.run.result.status,
        )
          ? options.run.result.status
          : "completed";
      return route.fulfill({
        contentType: "application/x-ndjson",
        body: [
          ...options.run.events,
          { kind: terminal, result: options.run.result },
        ]
          .map((event) => JSON.stringify(event))
          .join("\n"),
      });
    }
    if (
      path === "/api/workspace/workflow-source-templates" &&
      method === "GET"
    ) {
      const ids = [
        "printed-replacement-part",
        "raspberry-pi-enclosure",
        "sheet-metal-supplier-handoff",
        "lightweight-equipment-bracket",
        "sensor-interface-pcb",
        "parametric-drill-jig",
        "robot-tracking-diagnosis",
        "heat-spreader-sizing",
        "sensor-fan-harness",
        "water-heater-sizing",
      ];
      return route.fulfill({
        json: {
          catalog_version: "1.0.0",
          templates: ids.map((id, index) => ({
            template_id: id,
            version: "1.0.0",
            title:
              index === 0
                ? "3D Printed Replacement Part"
                : id
                    .split("-")
                    .map((part) => part[0].toUpperCase() + part.slice(1))
                    .join(" "),
            summary: "A real engineering workflow with measurable outputs.",
            discipline: "Engineering",
            preview: {
              asset: `previews/${id}.svg`,
              alt: `${id} engineering workflow preview`,
            },
            provided_inputs: [{ name: "Demo fixture" }],
            requested_inputs: [{ name: "Engineering requirements" }],
            expected_outputs: [{ name: "Checked engineering artifact" }],
            external_effects: index === 0 ? ["printer_transfer"] : [],
            source_digest: "d".repeat(64),
            readiness: {
              state: index < 3 ? "setup_required" : "reference",
              definition_valid: true,
              configured: false,
              qualified: false,
              available: false,
              verified_run: false,
              facts: [],
              blocking_reasons: [
                "Connect and qualify the required engineering tools.",
              ],
            },
          })),
        },
      });
    }
    const previewMatch =
      /^\/api\/workspace\/workflow-source-templates\/[^/]+\/preview$/.exec(
        path,
      );
    if (previewMatch && method === "GET") {
      return route.fulfill({
        contentType: "image/svg+xml",
        body: '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="360"><rect width="800" height="360" fill="#075985"/></svg>',
      });
    }
    const instanceMatch =
      /^\/api\/workspace\/workflow-source-templates\/([^/]+)\/instances$/.exec(
        path,
      );
    if (instanceMatch && method === "POST") {
      const body = request.postDataJSON() as {
        session_id: string;
        workflow_path: string;
      };
      currentPath = body.workflow_path;
      sourceReadiness = "setup_required";
      document = workflowDocument(publicWorkflowSource, 1, 1, currentPath);
      documents.set(currentPath, document);
      return route.fulfill({
        status: 201,
        json: {
          ...document,
          workflow_id: "workflow.template-instance",
          template: {
            template_id: instanceMatch[1],
            version: "1.0.0",
            source_digest: "d".repeat(64),
          },
        },
      });
    }
    if (
      path === "/api/workspace/workflow-sources/readiness" &&
      method === "GET"
    ) {
      return route.fulfill({
        headers: { "Cache-Control": "no-store" },
        json: {
          state: sourceReadiness,
          template_id:
            sourceReadiness === "setup_required"
              ? "printed-replacement-part"
              : null,
          template_version:
            sourceReadiness === "setup_required" ? "1.0.0" : null,
          source_digest: null,
          layout_digest: null,
          definition_valid: true,
          configured: sourceReadiness !== "setup_required",
          qualified: sourceReadiness !== "setup_required",
          available: sourceReadiness !== "setup_required",
          verified_run: false,
          facts: [],
          blocking_reasons:
            sourceReadiness === "setup_required"
              ? ["Connect and qualify the required engineering tools."]
              : [],
          message: null,
        },
      });
    }
    if (path === "/api/workspace/workflow-sources" && method === "GET") {
      const requestedPath = url.searchParams.get("path");
      if (
        url.searchParams.get("session_id") !== SESSION_ID ||
        requestedPath === null ||
        !/^workflows\/[a-z0-9][a-z0-9-]{0,62}\.workflow\.wflow$/.test(
          requestedPath,
        )
      ) {
        return route.fulfill({
          status: 400,
          json: { message: "Unexpected workflow source identity" },
        });
      }
      const requestedDocument = documents.get(requestedPath) ?? null;
      if (requestedDocument === null) {
        missingReads += 1;
        return route.fulfill({
          status: 404,
          json: {
            error_code: "workflow_source_not_found",
            message: "Workflow source not found",
          },
        });
      }
      return route.fulfill({
        headers: { "Cache-Control": "no-store" },
        json: requestedDocument,
      });
    }
    if (path === "/api/workspace/workflow-sources" && method === "POST") {
      const body = request.postDataJSON() as {
        session_id: string;
        path: string;
        source: string;
      };
      if (
        body.session_id !== SESSION_ID ||
        !/^workflows\/[a-z0-9][a-z0-9-]{0,62}\.workflow\.wflow$/.test(
          body.path,
        ) ||
        documents.has(body.path)
      ) {
        return route.fulfill({
          status: 409,
          json: conflictEnvelope(documents.get(body.path) ?? null),
        });
      }
      creates += 1;
      currentPath = body.path;
      document = workflowDocument(body.source, 1, 1, currentPath);
      documents.set(currentPath, document);
      return route.fulfill({
        status: 201,
        headers: { "Cache-Control": "no-store" },
        json: document,
      });
    }
    if (path === "/api/workspace/workflow-sources" && method === "PUT") {
      const body = request.postDataJSON() as {
        session_id: string;
        path: string;
        source: string;
        expected_storage_revision: number;
        expected_storage_digest: string;
        semantic_change_validated: boolean;
        layout?: Record<string, unknown>;
        expected_layout_revision?: number;
      };
      updates += 1;
      const previous = documents.get(body.path) ?? null;
      const stale =
        previous === null ||
        body.session_id !== SESSION_ID ||
        body.expected_storage_revision !== previous.storage_revision ||
        body.expected_storage_digest !== previous.storage_digest ||
        typeof body.semantic_change_validated !== "boolean" ||
        (body.layout !== undefined &&
          body.expected_layout_revision !== previous.layout_revision);
      if (rejectNextUpdate || stale || previous === null) {
        rejectNextUpdate = false;
        return route.fulfill({ status: 409, json: conflictEnvelope(previous) });
      }
      currentPath = body.path;
      const sourceChanged = body.source !== previous.source;
      document = workflowDocument(
        body.source,
        previous.storage_revision + Number(sourceChanged),
        previous.definition_revision +
          Number(sourceChanged && body.semantic_change_validated),
        currentPath,
      );
      if (body.layout !== undefined) {
        document.layout_revision = previous.layout_revision + 1;
        document.layout = {
          ...body.layout,
          semanticRevision: document.definition_revision,
          layoutRevision: document.layout_revision,
        };
        document.layout_status = "current";
      } else {
        document.layout_revision = previous.layout_revision;
        document.layout = sourceChanged ? null : previous.layout;
        document.layout_status =
          sourceChanged && previous.layout_revision > 0
            ? "stale"
            : previous.layout_status;
      }
      documents.set(currentPath, document);
      return route.fulfill({
        headers: { "Cache-Control": "no-store" },
        json: document,
      });
    }
    if (path === "/api/workspace/recent" || path === "/api/workspace/list") {
      return route.fulfill({
        json: {
          workspaces: [
            {
              workspace_id: WORKSPACE_ID,
              session_id: SESSION_ID,
              workspace_name: "Bracket development",
              local_path: "D:/engineering/bracket-development",
            },
          ],
        },
      });
    }
    return route.fulfill({
      status: 404,
      json: { detail: `Unmocked recovery-workspace API: ${method} ${path}` },
    });
  });

  return {
    current: () => document,
    sourceAt: (workflowPath) => documents.get(workflowPath) ?? null,
    createCount: () => creates,
    missingReadCount: () => missingReads,
    runCount: () => runs,
    runRequestCount: () => runRequests,
    updateCount: () => updates,
    conflictNextUpdate: () => {
      rejectNextUpdate = true;
    },
  };
}

async function collapseAgentConsole(page: Page): Promise<void> {
  const collapseAgent = page.getByTitle("Collapse Agent Console");
  if (await collapseAgent.isVisible()) await collapseAgent.click();
  await expect(page.getByTestId("agent-sidebar")).toBeHidden();
  await expect
    .poll(() =>
      page
        .getByTestId("workspace-panel")
        .evaluate(
          (element) =>
            element
              .getAnimations()
              .filter(
                (animation) =>
                  animation.pending || animation.playState === "running",
              ).length,
        ),
    )
    .toBe(0);
}

export async function openRecoveryEditor(page: Page): Promise<void> {
  await page.goto(`/workspace/${WORKSPACE_ID}`);
  const files = page.getByTestId("activity-bar-explorer-btn");
  await expect(files).toBeVisible();
  if ((await files.getAttribute("aria-expanded")) !== "true")
    await files.click();
  const navigation = page.getByRole("region", { name: "Workspace navigation" });
  const savedFile = navigation.getByText(WORKFLOW_PATH.split("/").at(-1)!, {
    exact: true,
  });
  if (!(await savedFile.isVisible())) {
    await navigation.getByText("bracket-development", { exact: true }).click();
  }
  await savedFile.click();
  await expect(page).toHaveURL(
    (url) =>
      url.pathname === `/workspace/${WORKSPACE_ID}` &&
      url.searchParams.get("workflow") === "canonical" &&
      url.searchParams.get("workflowPath") === WORKFLOW_PATH,
  );
  await expect(
    page.getByRole("region", {
      name: `Bracket development workflow ${WORKFLOW_PATH}`,
    }),
  ).toBeVisible();
  await collapseAgentConsole(page);
}

export async function openNewRecoveryEditor(page: Page): Promise<void> {
  await page.goto(`/workspace/${WORKSPACE_ID}`);
  const workflows = page.getByTestId("activity-bar-workflows-btn");
  await expect(workflows).toBeVisible();
  await workflows.click();
  const picker = page.getByRole("dialog");
  await expect(
    picker.getByRole("heading", { name: "Workflows", exact: true }),
  ).toBeVisible();
  await picker
    .getByRole("button", { name: "New workflow", exact: true })
    .click();
  await expect(picker).toBeHidden();
  await expect(page).toHaveURL(
    (url) =>
      url.pathname === `/workspace/${WORKSPACE_ID}` &&
      url.searchParams.get("workflow") === "canonical" &&
      /^workflows\/untitled-workflow-[a-f0-9-]{12}\.workflow\.wflow$/.test(
        url.searchParams.get("workflowPath") ?? "",
      ),
  );
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await collapseAgentConsole(page);
}

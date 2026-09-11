import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, type Page } from "@playwright/test";

const WORKSPACE_ID = "ws-recovery";
const SESSION_ID = "session-recovery";
const WORKFLOW_PATH = "workflows/mounting-bracket.workflow.wflow";

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
  createCount(): number;
  missingReadCount(): number;
  updateCount(): number;
  conflictNextUpdate(): void;
}

function workflowDocument(
  source: string,
  storageRevision: number,
  definitionRevision: number,
): WorkflowSourceDocument {
  return {
    workspace_id: WORKSPACE_ID,
    path: WORKFLOW_PATH,
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
  options: { source?: string | null } = {},
): Promise<RecoveryWorkspaceMock> {
  await page.addInitScript(() => {
    window.localStorage.setItem("wright.workspaceSurfaces.testEnabled", "1");
  });
  let document = options.source === null
    ? null
    : workflowDocument(options.source ?? publicWorkflowSource, 1, 2);
  let creates = 0;
  let missingReads = 0;
  let updates = 0;
  let rejectNextUpdate = false;

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path === "/api/auth/session/status") {
      return route.fulfill({ json: { auth_required: false, authenticated: true } });
    }
    if (path === "/api/setup/status") {
      return route.fulfill({ json: { is_configured: true, active_agent: "hermes", theme: "dark" } });
    }
    if (path === "/api/health" || path === "/api/agent/health" || path === "/api/inference/health") {
      return route.fulfill({ json: { status: "ok", state: "connected", latencyMs: 1 } });
    }
    if (path === "/api/mcp/servers") return route.fulfill({ json: { servers: [] } });
    if (path === "/api/mcp/servers/installed") return route.fulfill({ json: { servers: [] } });
    if (path === "/api/mcp/tools") return route.fulfill({ json: { tools: [] } });
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
      return route.fulfill({ json: { sessions: [{ session_id: SESSION_ID, title: "Default" }] } });
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
      return route.fulfill({ json: { sessions: [{ session_id: SESSION_ID, title: "Default" }] } });
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
            children: document === null
              ? []
              : [{ name: "mounting-bracket.workflow.wflow", path: `/${WORKFLOW_PATH}`, type: "file", children: null }],
          },
        },
      });
    }
    if (path === "/api/workspace/git/status") {
      return route.fulfill({ json: { branch: "codex/test", files: [] } });
    }
    if (path === "/api/workspace/surfaces/events") {
      return route.fulfill({ contentType: "text/event-stream", body: ": keepalive\n\n" });
    }
    if (path === "/api/workspace/surfaces") {
      return route.fulfill({ json: { items: [] } });
    }
    if (path === "/api/workspace/workflow-sources/input-files" && method === "GET") {
      if (url.searchParams.get("session_id") !== SESSION_ID) {
        return route.fulfill({ status: 404, json: { message: "Workspace not found" } });
      }
      return route.fulfill({ headers: { "Cache-Control": "no-store" }, json: {
        workspace_id: WORKSPACE_ID,
        files: [
          { path: "design/requirements.md", name: "requirements.md" },
          { path: "references/bracket.png", name: "bracket.png" },
        ],
      } });
    }
    if (path === "/api/workspace/workflow-sources" && method === "GET") {
      if (url.searchParams.get("session_id") !== SESSION_ID || url.searchParams.get("path") !== WORKFLOW_PATH) {
        return route.fulfill({ status: 400, json: { message: "Unexpected workflow source identity" } });
      }
      if (document === null) {
        missingReads += 1;
        return route.fulfill({ status: 404, json: { error_code: "workflow_source_not_found", message: "Workflow source not found" } });
      }
      return route.fulfill({ headers: { "Cache-Control": "no-store" }, json: document });
    }
    if (path === "/api/workspace/workflow-sources" && method === "POST") {
      const body = request.postDataJSON() as {
        session_id: string;
        path: string;
        source: string;
      };
      if (body.session_id !== SESSION_ID || body.path !== WORKFLOW_PATH || document !== null) {
        return route.fulfill({ status: 409, json: conflictEnvelope(document) });
      }
      creates += 1;
      document = workflowDocument(body.source, 1, 1);
      return route.fulfill({ status: 201, headers: { "Cache-Control": "no-store" }, json: document });
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
      const stale = document === null
        || body.session_id !== SESSION_ID
        || body.path !== WORKFLOW_PATH
        || body.expected_storage_revision !== document.storage_revision
        || body.expected_storage_digest !== document.storage_digest
        || typeof body.semantic_change_validated !== "boolean"
        || (body.layout !== undefined && body.expected_layout_revision !== document.layout_revision);
      if (rejectNextUpdate || stale) {
        rejectNextUpdate = false;
        return route.fulfill({ status: 409, json: conflictEnvelope(document) });
      }
      const previous = document;
      const sourceChanged = body.source !== previous.source;
      document = workflowDocument(
        body.source,
        previous.storage_revision + Number(sourceChanged),
        previous.definition_revision + Number(sourceChanged && body.semantic_change_validated),
      );
      if (body.layout !== undefined) {
        document.layout_revision = previous.layout_revision + 1;
        document.layout = { ...body.layout, semanticRevision: document.definition_revision, layoutRevision: document.layout_revision };
        document.layout_status = "current";
      } else {
        document.layout_revision = previous.layout_revision;
        document.layout = sourceChanged ? null : previous.layout;
        document.layout_status = sourceChanged && previous.layout_revision > 0 ? "stale" : previous.layout_status;
      }
      return route.fulfill({ headers: { "Cache-Control": "no-store" }, json: document });
    }
    if (path === "/api/workspace/recent" || path === "/api/workspace/list") {
      return route.fulfill({
        json: {
          workspaces: [{
            workspace_id: WORKSPACE_ID,
            session_id: SESSION_ID,
            workspace_name: "Bracket development",
            local_path: "D:/engineering/bracket-development",
          }],
        },
      });
    }
    return route.fulfill({ status: 404, json: { detail: `Unmocked recovery-workspace API: ${method} ${path}` } });
  });

  return {
    current: () => document,
    createCount: () => creates,
    missingReadCount: () => missingReads,
    updateCount: () => updates,
    conflictNextUpdate: () => { rejectNextUpdate = true; },
  };
}

export async function openRecoveryEditor(page: Page): Promise<void> {
  await page.goto(`/workspace/${WORKSPACE_ID}`);
  const workflows = page.getByTestId("activity-bar-workflows-btn");
  await expect(workflows).toBeVisible();
  await workflows.click();
  await expect(page).toHaveURL(new RegExp(`/workspace/${WORKSPACE_ID}\\?workflow=canonical$`));
  await expect(page.getByTestId("workflow-workspace-context")).toContainText("Bracket development");
  const collapseAgent = page.getByTitle("Collapse Agent Console");
  if (await collapseAgent.isVisible()) await collapseAgent.click();
}

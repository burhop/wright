import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test, type Page } from "@playwright/test";


type JsonRow = Record<string, any>;

const fixture = JSON.parse(
  readFileSync(
    resolve("packages/core/tests/fixtures/workflow_drafts/representative-workflow.json"),
    "utf8",
  ),
) as JsonRow;
const draftRoute = `/workflow-composer?draft=${fixture.draft_id}`;

function canonicalJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value !== null && typeof value === "object") {
    const row = value as Record<string, unknown>;
    return `{${Object.keys(row).sort().map(
      (key) => `${JSON.stringify(key)}:${canonicalJson(row[key])}`,
    ).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value: unknown): string {
  const material = typeof value === "string" ? value : canonicalJson(value);
  return createHash("sha256").update(material).digest("hex");
}

function etag(draft: JsonRow): string {
  return `"${sha256(draft)}"`;
}

interface MockState {
  validateBodies: JsonRow[];
  saveBodies: JsonRow[];
  saveEtags: (string | undefined)[];
}

async function mockComposer(page: Page): Promise<MockState> {
  const state: MockState = { validateBodies: [], saveBodies: [], saveEtags: [] };
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === `/api/workflow-drafts/${fixture.draft_id}` && request.method() === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: canonicalJson(fixture),
        headers: { ETag: etag(fixture) },
      });
    }
    if (path.endsWith("/validate") && request.method() === "POST") {
      const candidate = request.postDataJSON() as JsonRow;
      state.validateBodies.push(candidate);
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        json: {
          valid: true,
          semantic_sha256: candidate.semantic_sha256,
          layout_sha256: candidate.layout_sha256,
          diagnostics: [],
        },
      });
    }
    if (path === `/api/workflow-drafts/${fixture.draft_id}` && request.method() === "PUT") {
      const candidate = request.postDataJSON() as JsonRow;
      state.saveBodies.push(candidate);
      state.saveEtags.push(request.headers()["if-match"]);
      const saved = { ...candidate, revision: 2 };
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: canonicalJson(saved),
        headers: { ETag: etag(saved) },
      });
    }
    if (path === "/api/auth/session/status") {
      return route.fulfill({ json: { auth_required: false, authenticated: true } });
    }
    if (path === "/api/setup/status") {
      return route.fulfill({ json: { is_configured: true, active_agent: "hermes", theme: "dark" } });
    }
    if (path === "/api/mcp/servers") return route.fulfill({ json: { servers: [] } });
    if (path === "/api/mcp/tools") return route.fulfill({ json: { tools: [] } });
    if (path === "/api/agent/sessions") return route.fulfill({ json: { sessions: [] } });
    if (path === "/api/workspace/recent" || path === "/api/workspace/list") {
      return route.fulfill({ json: { workspaces: [] } });
    }
    if (
      path === "/api/health" ||
      path === "/api/agent/health" ||
      path === "/api/inference/health"
    ) {
      return route.fulfill({ json: { state: "connected", latencyMs: 1 } });
    }
    return route.fulfill({ status: 404, json: { detail: "Unmocked API" } });
  });
  return state;
}

test("edits, contains an invalid connection, corrects it, and saves only the valid draft", async ({
  page,
}) => {
  const requests = await mockComposer(page);
  await page.goto(draftRoute);
  await expect(page.getByTestId("workflow-composer-canvas")).toBeVisible();

  await page.getByTestId("workflow-canvas-select-block.review-product-definition").click();
  await expect(page.getByTestId("workflow-composer-inspector"))
    .toContainText("block.review-product-definition");

  await page.getByTestId("workflow-inspector-title").fill("Review the product definition");
  await page.getByTestId("workflow-inspector-purpose")
    .fill("Check completeness and record bounded corrections.");
  await page.getByTestId("workflow-inspector-apply-definition").click();
  await page.getByTestId("workflow-inspector-position-x").fill("720");
  await page.getByTestId("workflow-inspector-position-y").fill("96");
  await page.getByTestId("workflow-inspector-apply-position").click();

  await expect(page.getByTestId("workflow-composer-canvas"))
    .toContainText("Review the product definition");
  await expect(page.getByTestId("workflow-composer-text"))
    .toContainText("Review the product definition");
  await expect(
    page.getByTestId("workflow-composer-canvas")
      .locator('[data-semantic-id="block.review-product-definition"]'),
  ).toHaveAttribute("data-layout-x", "720");

  await page.getByTestId("workflow-connection-delete-connection.definition-to-review").click();
  await expect(
    page.getByTestId("workflow-composer-canvas")
      .locator('[data-semantic-id="connection.definition-to-review"]'),
  ).toHaveCount(0);

  await page.getByTestId("workflow-connection-source").selectOption("port.product-definition-out");
  await page.getByTestId("workflow-connection-target").selectOption("port.accepted-definition-out");
  await page.getByTestId("workflow-connection-create").click();

  const diagnostic = page.getByTestId("workflow-diagnostic-CONNECTION_TARGET_INVALID");
  await expect(diagnostic).toContainText("port.accepted-definition-out");
  await expect(diagnostic).toContainText("not an existing input port");
  await expect(diagnostic).toContainText("Choose an existing input port");
  await expect(
    page.getByTestId("workflow-composer-canvas")
      .locator('[data-semantic-id="port.accepted-definition-out"]'),
  ).toHaveAttribute("data-diagnostic", "true");
  expect(requests.validateBodies).toHaveLength(0);
  expect(requests.saveBodies).toHaveLength(0);
  await expect(page.getByLabel("Working draft authority")).toContainText("Revision 1");

  await page.getByTestId("workflow-connection-target").selectOption("port.product-definition-in");
  await page.getByTestId("workflow-connection-create").click();
  await expect(page.getByTestId("workflow-composer-diagnostics")).toHaveCount(0);
  await expect(page.getByTestId("workflow-composer-canvas"))
    .toContainText("port.product-definition-out → port.product-definition-in");
  await expect(page.getByTestId("workflow-composer-text"))
    .toContainText("port.product-definition-out → port.product-definition-in");

  await page.getByTestId("workflow-composer-validate").click();
  await expect(page.getByText("Validation passed. The working draft is structurally valid."))
    .toBeVisible();
  await page.getByTestId("workflow-composer-save").click();
  await expect(page.getByText("Saved revision 2.")).toBeVisible();

  expect(requests.validateBodies).toHaveLength(2);
  expect(requests.saveBodies).toHaveLength(1);
  expect(requests.saveEtags).toEqual([etag(fixture)]);
  const saved = requests.saveBodies[0];
  expect(saved.semantic.blocks.find((block: JsonRow) => block.id === "block.review-product-definition").title)
    .toBe("Review the product definition");
  expect(saved.layout.positions.find((position: JsonRow) => position.semantic_id === "block.review-product-definition"))
    .toEqual(expect.objectContaining({ x: 720, y: 96 }));
  expect(saved.semantic.connections).toContainEqual(expect.objectContaining({
    source_port_id: "port.product-definition-out",
    target_port_id: "port.product-definition-in",
  }));
  expect(saved.semantic.connections).not.toContainEqual(expect.objectContaining({
    target_port_id: "port.accepted-definition-out",
  }));
});

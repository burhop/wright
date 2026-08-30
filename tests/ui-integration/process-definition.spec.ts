import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import AxeBuilder from "@axe-core/playwright";
import {
  expect,
  test,
  type Page,
  type Request as PlaywrightRequest,
} from "@playwright/test";

const PROCESS_ROUTE = "/processes/product-definition-v1";
const PROCESS_API_ROUTE = "/api/process-definitions/product-definition-v1";
const PROCESS_SOURCE_ID = "process-definitions/product-definition-v1.json";

interface IdentifiedFixture {
  id: string;
}

interface ProcessDefinitionFixture {
  process_id: string;
  schema_version: string;
  title: string;
  purpose: string;
  phases: IdentifiedFixture[];
  actions: IdentifiedFixture[];
  ports: IdentifiedFixture[];
  gates: IdentifiedFixture[];
  feedback_paths: IdentifiedFixture[];
  artifacts: IdentifiedFixture[];
}

interface ObservedProcessRequest {
  method: string;
  path: string;
  body: string | null;
}

const definitionBytes = readFileSync(
  resolve(
    "src/wright_engineering/static/process-definitions/product-definition-v1.json",
  ),
);
const definition = JSON.parse(
  definitionBytes.toString("utf8"),
) as ProcessDefinitionFixture;

function canonicalString(value: string): string {
  let encoded = '"';
  for (const token of value) {
    const code = token.codePointAt(0) ?? 0;
    if (token === '"') encoded += '\\"';
    else if (token === "\\") encoded += "\\\\";
    else if (token === "\b") encoded += "\\b";
    else if (token === "\t") encoded += "\\t";
    else if (token === "\n") encoded += "\\n";
    else if (token === "\f") encoded += "\\f";
    else if (token === "\r") encoded += "\\r";
    else if (code < 0x20) encoded += `\\u${code.toString(16).padStart(4, "0")}`;
    else encoded += token;
  }
  return `${encoded}"`;
}

function compareUtf8(left: string, right: string): number {
  return Buffer.compare(Buffer.from(left, "utf8"), Buffer.from(right, "utf8"));
}

function canonicalJson(value: unknown): string {
  if (value === null) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "string") return canonicalString(value);
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value) || Object.is(value, -0)) {
      throw new Error("Fixture contains a non-canonical number");
    }
    return String(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(canonicalJson).join(",")}]`;
  }
  if (typeof value === "object") {
    const row = value as Record<string, unknown>;
    return `{${Object.keys(row)
      .sort(compareUtf8)
      .map((key) => `${canonicalString(key)}:${canonicalJson(row[key])}`)
      .join(",")}}`;
  }
  throw new Error("Fixture contains an unsupported canonical value");
}

function sha256(value: string | Buffer): string {
  return createHash("sha256").update(value).digest("hex");
}

const envelopeWithoutEtag = {
  definition,
  source_kind: "packaged_fallback",
  source_id: PROCESS_SOURCE_ID,
  source_sha256: sha256(definitionBytes),
  source_available: true,
  supported_schema_versions: ["1.0.0"],
};
const processEnvelope = {
  ...envelopeWithoutEtag,
  etag: sha256(canonicalJson(envelopeWithoutEtag)),
};
const processEnvelopeBody = canonicalJson(processEnvelope);
const expectedSemanticIds = [
  { id: definition.process_id },
  ...definition.phases,
  ...definition.actions,
  ...definition.ports,
  ...definition.gates,
  ...definition.feedback_paths,
  ...definition.artifacts,
]
  .map((item) => item.id)
  .sort();

function observeProcessRequest(
  request: PlaywrightRequest,
  observed: ObservedProcessRequest[],
): void {
  const path = new URL(request.url()).pathname;
  if (path !== PROCESS_API_ROUTE) return;
  observed.push({
    method: request.method(),
    path,
    body: request.postData(),
  });
}

async function mockProcessDefinition(
  page: Page,
): Promise<ObservedProcessRequest[]> {
  const observed: ObservedProcessRequest[] = [];
  page.on("request", (request) => observeProcessRequest(request, observed));

  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === PROCESS_API_ROUTE) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: processEnvelopeBody,
        headers: {
          ETag: `"${processEnvelope.etag}"`,
          "X-Trace-Id": "trace-process-definition-browser",
        },
      });
    }
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
    if (path === "/api/mcp/servers") {
      return route.fulfill({ json: { servers: [] } });
    }
    if (path === "/api/mcp/tools") {
      return route.fulfill({ json: { tools: [] } });
    }
    if (path === "/api/agent/sessions") {
      return route.fulfill({ json: { sessions: [] } });
    }
    if (path === "/api/workspace/recent" || path === "/api/workspace/list") {
      return route.fulfill({ json: { workspaces: [] } });
    }
    if (
      path === "/api/health" ||
      path === "/api/agent/health" ||
      path === "/api/inference/health"
    ) {
      return route.fulfill({
        json: { state: "connected", latencyMs: 1 },
      });
    }
    return route.fulfill({ status: 404, json: { detail: "Unmocked API" } });
  });
  return observed;
}

async function openProcessPage(page: Page): Promise<void> {
  await page.goto(PROCESS_ROUTE);
  await expect(page.getByTestId("page-process-definition")).toBeVisible();
}

async function uniqueSemanticIds(
  page: Page,
  containerTestId: string,
): Promise<string[]> {
  return page
    .getByTestId(containerTestId)
    .locator("[data-semantic-id]")
    .evaluateAll((elements) =>
      Array.from(
        new Set(
          elements
            .map((element) => element.getAttribute("data-semantic-id"))
            .filter((value): value is string => value !== null),
        ),
      ).sort(),
    );
}

test.describe("Read-only process definition journey", () => {
  test("opens from customer navigation and presents one matching text and diagram definition", async ({
    page,
  }) => {
    const observed = await mockProcessDefinition(page);
    await page.goto("/");

    const navigation = page.getByTestId("nav-process-definition");
    await expect(navigation).toBeVisible();
    await navigation.focus();
    await expect(navigation).toBeFocused();
    await page.keyboard.press("Enter");

    await expect(page).toHaveURL(PROCESS_ROUTE);
    await expect(page.getByTestId("page-process-definition")).toBeVisible();
    await expect(page.getByTestId("process-definition-title")).toContainText(
      definition.title,
    );
    await expect(
      page
        .getByTestId("page-process-definition")
        .getByText(definition.purpose, { exact: true })
        .first(),
    ).toBeVisible();
    await expect(page.getByTestId("process-definition-text")).toBeVisible();
    await expect(page.getByTestId("process-definition-diagram")).toBeVisible();
    await expect(
      page.getByTestId("process-definition-source-details"),
    ).toBeVisible();

    expect(await uniqueSemanticIds(page, "process-definition-text")).toEqual(
      expectedSemanticIds,
    );
    expect(await uniqueSemanticIds(page, "process-definition-diagram")).toEqual(
      expectedSemanticIds,
    );
    expect(observed.length).toBeGreaterThan(0);
    expect(observed).toEqual(
      expect.arrayContaining([
        { method: "GET", path: PROCESS_API_ROUTE, body: null },
      ]),
    );
    expect(observed.every((request) => request.method === "GET")).toBe(true);
  });

  test("supports the native source disclosure by keyboard with no serious or critical Axe findings", async ({
    page,
  }) => {
    await mockProcessDefinition(page);
    await openProcessPage(page);

    const toggle = page.getByTestId("process-definition-source-toggle");
    await toggle.focus();
    await expect(toggle).toBeFocused();
    await page.keyboard.press("Enter");
    await expect
      .poll(() =>
        toggle.evaluate((element) => element.closest("details")?.open === true),
      )
      .toBe(true);
    await expect(
      page.getByTestId("process-definition-source-details"),
    ).toContainText(PROCESS_SOURCE_ID);

    const accessibility = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();
    expect(
      accessibility.violations.filter((violation) =>
        ["critical", "serious"].includes(violation.impact ?? ""),
      ),
    ).toEqual([]);
  });

  test("keeps the complete definition reachable at 200 percent zoom with reduced motion", async ({
    page,
  }) => {
    await mockProcessDefinition(page);
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await openProcessPage(page);
    await page.evaluate(() => {
      document.documentElement.style.zoom = "2";
    });

    expect(
      await page.evaluate(
        () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      ),
    ).toBe(true);
    await expect(page.getByTestId("process-definition-title")).toBeVisible();
    await expect(page.getByTestId("process-definition-text")).toBeVisible();
    await expect(page.getByTestId("process-definition-diagram")).toBeVisible();
    await expect(
      page
        .getByTestId("process-definition-text")
        .locator('[data-semantic-id="released-definition-package"]'),
    ).toBeVisible();

    const movingElements = await page
      .getByTestId("page-process-definition")
      .evaluate((root) => {
        const elements = [root, ...Array.from(root.querySelectorAll("*"))];
        const durationInMilliseconds = (duration: string) => {
          const parsed = Number.parseFloat(duration);
          return duration.trim().endsWith("ms") ? parsed : parsed * 1000;
        };
        const hasMeaningfulDuration = (value: string) =>
          value
            .split(",")
            .some((duration) => durationInMilliseconds(duration) > 1);
        return elements
          .filter((element) => {
            const style = getComputedStyle(element);
            return (
              hasMeaningfulDuration(style.animationDuration) ||
              hasMeaningfulDuration(style.transitionDuration)
            );
          })
          .map(
            (element) =>
              element.getAttribute("data-testid") ??
              element.getAttribute("data-semantic-id") ??
              element.tagName,
          );
      });
    expect(movingElements).toEqual([]);
  });

  test("preserves explicit non-color meaning at 320 pixels with forced colors", async ({
    page,
  }) => {
    await mockProcessDefinition(page);
    await page.setViewportSize({ width: 320, height: 800 });
    await page.emulateMedia({ forcedColors: "active" });
    await openProcessPage(page);

    expect(
      await page.evaluate(
        () => window.matchMedia("(forced-colors: active)").matches,
      ),
    ).toBe(true);
    const diagram = page.getByTestId("process-definition-diagram");
    await expect(diagram).toContainText(/Input/i);
    await expect(diagram).toContainText(/Output/i);
    await expect(diagram).toContainText(/Pass/i);
    await expect(diagram).toContainText(/Fail|Return for revision/i);
    await expect(diagram).toContainText(/Expected artifact/i);
    await expect(
      diagram.locator('[data-semantic-id="definition-approval"]'),
    ).toBeVisible();
    await expect(
      diagram.locator('[data-semantic-id="revise-definition"]'),
    ).toBeVisible();
    await expect(
      page
        .getByTestId("process-definition-text")
        .locator('[data-semantic-id="released-definition-package"]'),
    ).toBeVisible();
    await page
      .getByTestId("process-definition-source-toggle")
      .scrollIntoViewIfNeeded();
    await expect(
      page.getByTestId("process-definition-source-toggle"),
    ).toBeVisible();
  });
});

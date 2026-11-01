import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { test, expect } from "@playwright/test";
import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
} from "./fixtures/workflow-recovery";

const source = readFileSync(
  resolve(
    process.cwd(),
    "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/lightweight-equipment-bracket.workflow.wflow",
  ),
  "utf8",
).replaceAll("__instance__", "binding_test");
const cadId = "block.create-bracket-binding-test";

test("a template qualification rejection explains responsibility and recovery without implying a bad input or executed task", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page, { source });
  await page.route("**/api/workspace/workflow-sources/runs?*", (route) =>
    route.fulfill({
      json: {
        workspace_id: "ws-recovery",
        workflow_path: "workflows/untitled.workflow.wflow",
        runs: [],
      },
    }),
  );
  await page.route("**/api/workspace/workflow-sources/tools?*", (route) =>
    route.fulfill({
      json: {
        tools: [
          {
            name: "test__create",
            server_id: "test",
            server_name: "Qualification test server",
            tool_name: "create",
            title: "Create",
            description: "",
            input_schema: {},
            schema_digest: "test",
          },
        ],
      },
    }),
  );
  let runRequests = 0;
  await page.route("**/api/workspace/workflow-sources/run", (route) => {
    runRequests += 1;
    return route.fulfill({
      status: 409,
      json: {
        error_code: "workflow_template_setup_required",
        message:
          "This engineering template needs setup or qualification before a live run.",
        details: {
          correction:
            "Bracket geometry and CalculiX D034 integration require clean-environment qualification.",
        },
        trace_id: "trace-template-test",
      },
    });
  });
  await openRecoveryEditor(page);
  for (const id of [cadId, "block.solve-and-compare-binding-test"]) {
    const block = page.getByTestId(`workflow-recovery-block-${id}`);
    await block.focus();
    await block.press("Enter");
    await page
      .getByTestId("workflow-recovery-task-server")
      .selectOption("test");
  }
  await page.getByTestId("workflow-recovery-inspector-close").click();
  await page.getByTestId("workflow-recovery-run-start").click();
  await expect(page.getByTestId("workflow-native-run-summary")).toContainText(
    "Run not started",
  );
  await expect(
    page.getByTestId("workflow-recovery-run-details-toggle"),
  ).toContainText("Run not started");
  const issue = page.getByTestId("workflow-run-issue");
  await expect(issue).toContainText("Wright template/integration maintainers");
  await expect(issue).toContainText(
    "Changing your design request will not remove this blocker",
  );
  await expect(issue).toContainText(
    "MCP availability and selection are separate requirements",
  );
  await expect(
    page.getByTestId("workflow-recovery-native-run-input"),
  ).toHaveCount(0);
  await expect(
    page.getByTestId("workflow-recovery-native-run-mode"),
  ).not.toContainText("Preparing the saved inputs");
  expect(runRequests).toBe(1);
  await page.screenshot({
    path: "test-results/workflow-template-blocked-desktop.png",
  });
  await page.setViewportSize({ width: 796, height: 791 });
  await page.screenshot({
    path: "test-results/workflow-template-blocked-narrow.png",
  });
  expect(
    await issue.evaluate(
      (element) => element.scrollWidth <= element.clientWidth + 1,
    ),
  ).toBe(true);
  await page.getByText("Technical log and telemetry", { exact: true }).click();
  await expect(page.getByTestId("workflow-run-error-diagnostic")).toContainText(
    "trace-template-test",
  );
  await expect(page.getByTestId("workflow-run-error-diagnostic")).toContainText(
    "CalculiX",
  );
});

test("workspace reference tasks expose an MCP choice, retain it across save/reopen, and block missing bindings", async ({
  page,
}) => {
  const state = await mockRecoveryWorkspace(page, { source });
  await page.route("**/api/workspace/workflow-sources/runs?*", (route) =>
    route.fulfill({
      json: {
        workspace_id: "ws-recovery",
        workflow_path: "workflows/untitled.workflow.wflow",
        runs: [],
      },
    }),
  );
  const runRequests: string[] = [];
  page.on("request", (request) => {
    if (
      request.method() === "POST" &&
      /workflow-sources.*run/.test(request.url())
    )
      runRequests.push(request.url());
  });
  await page.route("**/api/workspace/workflow-sources/tools?*", (route) =>
    route.fulfill({
      json: {
        tools: ["a", "b"].map((id) => ({
          name: `${id}__create`,
          server_id: id,
          server_name: `CAD server ${id}`,
          tool_name: "create",
          title: "Create",
          description: "",
          input_schema: {},
          schema_digest: id,
        })),
      },
    }),
  );
  await openRecoveryEditor(page);
  const cad = page.getByTestId(`workflow-recovery-block-${cadId}`);
  await expect(cad).toContainText("MCP: not selected");
  await page.getByTestId("workflow-recovery-run-start").click();
  await expect(
    page.getByTestId("workflow-recovery-diagnostic-WFR-MCP-SERVER-REQUIRED"),
  ).toHaveCount(2);
  expect(runRequests).toEqual([]);
  await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
    "Template candidate: BREP MCP. No server is bound.",
  );
  await page.getByTestId("workflow-recovery-dismiss-diagnostics").click();
  const selector = page.getByTestId("workflow-recovery-task-server");
  await selector.selectOption("a");
  await expect(cad).toContainText("MCP: CAD server a");
  await expect(
    page.getByTestId(`workflow-recovery-block-instructions-${cadId}`),
  ).toHaveValue(
    "Create bracket CAD, export STEP, and record mass and controlled dimensions.",
  );
  await expect(page.getByTestId("workflow-recovery-delete")).toHaveCount(0);
  await selector.selectOption("b");
  await expect(cad).toContainText("MCP: CAD server b");
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(cad).toContainText("MCP: CAD server a");
  await page.getByTestId("workflow-recovery-save").click();
  await expect(page.getByTestId("workflow-recovery-save-status")).toHaveText(
    "Saved",
  );
  expect(state.current()?.source).toContain('"mcp_server":"a"');
  expect(state.current()?.source).toContain('"mcp_server_name":"CAD server a"');
  await page.reload();
  await cad.focus();
  await cad.press("Enter");
  await expect(selector).toHaveValue("a");
  await expect(cad).toContainText("MCP: CAD server a");
  await page.screenshot({ path: "test-results/workflow-mcp-binding.png" });
});

test("clicking a block and Delete uses confirmation while instruction editing remains safe", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page, { source });
  await page.route("**/api/workspace/workflow-sources/tools?*", (route) =>
    route.fulfill({ json: { tools: [] } }),
  );
  await openRecoveryEditor(page);
  const cad = page.getByTestId(`workflow-recovery-block-${cadId}`);
  await cad.click();
  await expect(page.getByTestId("workflow-recovery-inspector")).toBeVisible();
  await expect(page.getByTestId("workflow-recovery-delete")).toHaveCount(0);
  const instructions = page.getByTestId(
    `workflow-recovery-block-instructions-${cadId}`,
  );
  await instructions.focus();
  await instructions.press("Home");
  await instructions.press("Delete");
  await expect(
    page.getByTestId("workflow-recovery-delete-confirm"),
  ).toHaveCount(0);
  await expect(cad).toBeVisible();
  await cad.click();
  await page.keyboard.press("Delete");
  await expect(page.getByRole("dialog")).toContainText("2 connection(s)");
  await page.getByTestId("workflow-recovery-delete-confirm").click();
  await expect(cad).toHaveCount(0);
  await page.getByTestId("workflow-recovery-undo").click();
  await expect(cad).toBeVisible();
});

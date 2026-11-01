import { expect, test } from "@playwright/test";
import {
  mockRecoveryWorkspace,
  openNewRecoveryEditor,
} from "./fixtures/workflow-recovery";

// Capability/file responses here are fixtures. They prove navigation and draft
// behavior, never provider installation, qualification, or engineering readiness.
for (const width of [1280, 700]) {
  test(`missing tool setup retains its exact subject through ${width}px layout and return without side effects`, async ({
    page,
  }, testInfo) => {
    // Existing native narrow mode has no Workflows activity control. Enter via
    // the ordinary desktop workspace, then verify safe fallback on narrowing.
    await page.setViewportSize({ width: 1280, height: 900 });
    const workspace = await mockRecoveryWorkspace(page);
    let available = false;
    let failRefresh = false;
    const scopes: unknown[] = [];
    const writes: string[] = [];
    const roles = ["construction", "geometry", "slicer", "inspection"];
    const profiles = [
      "machine",
      "process_original",
      "process_orca",
      "filament",
    ];
    await page.route("**/api/workspace/workflow-sources/readiness?*", (route) =>
      route.fulfill({
        json: {
          state: "setup_required",
          template_id: "replacement-drawer-handle",
          template_version: "1.0.1",
          definition_valid: true,
          configured: false,
          qualified: false,
          available: false,
          verified_run: false,
          facts: [],
          blocking_reasons: ["Fixture tool setup required"],
        },
      }),
    );
    await page.route(
      "**/api/workspace/workflow-sources/input-files?*",
      (route) =>
        route.fulfill({
          json: {
            workspace_id: "ws-recovery",
            files: profiles.map((role) => ({
              path: `profiles/${role}.json`,
              name: `${role}.json`,
            })),
          },
        }),
    );
    await page.route("**/replacement-drawer-handle/setup/options", (route) => {
      const scope = route.request().postDataJSON();
      scopes.push(scope);
      if (failRefresh)
        return route.fulfill({
          status: 409,
          json: {
            detail: { message: "Fixture current-source refresh unavailable" },
          },
        });
      return route.fulfill({
        json: {
          workspace_id: "ws-recovery",
          path: scope.path,
          workflow_id: "workflow.fixture",
          recipe: {
            id: "printed-handle-orca",
            version: "2",
            digest: "b".repeat(64),
          },
          workspace_mount: "/isolated-fixture/workspace",
          requirements: [
            "Fixture exact FreeCAD requirement; native execution is not exercised.",
            "Providers must use this same absolute workspace path.",
          ],
          profiles: { mode: "workspace_files", roles: profiles },
          tools: Object.fromEntries(
            roles.map((role) => [
              role,
              role === "construction" && !available
                ? []
                : [
                    {
                      server_id: `fixture-${role}`,
                      name: `fixture-${role}__tool`,
                      tool_name: `${role}_tool`,
                      schema_digest: "c".repeat(64),
                    },
                  ],
            ]),
          ),
        },
      });
    });
    page.on("request", (request) => {
      if (request.method() !== "GET" && request.url().includes("/api/"))
        writes.push(`${request.method()} ${new URL(request.url()).pathname}`);
    });
    await openNewRecoveryEditor(page);
    const document = workspace.current()!;
    await page.getByTestId("workflow-handle-setup-open").click();
    for (const role of profiles)
      await page
        .getByTestId(`handle-setup-profile-${role}`)
        .selectOption(`profiles/${role}.json`);
    await page.getByTestId("handle-setup-orientation").selectOption("side");
    const configure = page.getByRole("button", {
      name: "Configure the CAD tool",
    });
    await configure.scrollIntoViewIfNeeded();
    await page.screenshot({
      path: testInfo.outputPath("missing-capability-action.png"),
    });
    await configure.click();
    const help = page.getByRole("region", { name: "Configure the CAD tool" });
    await expect(help).toBeVisible();
    if (width === 700) {
      await page.setViewportSize({ width, height: 900 });
      await expect(
        page.getByTestId("printed-handle-setup-dialog"),
      ).toBeVisible();
      await expect(
        page.getByRole("alert").filter({ hasText: "workspace layout changed" }),
      ).toBeVisible();
      await expect(
        page.getByTestId("handle-setup-profile-machine"),
      ).toHaveValue("profiles/machine.json");
      await page.setViewportSize({ width: 1280, height: 900 });
      await expect(page.getByTestId("workspace-panel")).not.toHaveAttribute(
        "data-layout-mode",
        "narrow",
      );
      await configure.click();
      await expect(help).toBeVisible();
    }
    await expect(
      page.getByTestId("printed-handle-setup-dialog"),
    ).not.toBeVisible();
    await expect(help).toContainText("FreeCAD constructs the solid handle");
    await expect(
      help.getByRole("link", { name: "Open Tool Registry (new tab)" }),
    ).toHaveAttribute("href", "/tool-registry");
    await help.getByText("Read provider setup guide (bundled copy)").click();
    await expect(help.getByText(/# FreeCAD MCP usage guide/)).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath("configuration-and-bundled-help.png"),
    });
    await help.getByText("Read provider setup guide (bundled copy)").click();
    available = true;
    await help.getByRole("button", { name: "Return to job setup" }).click();
    await expect(page.getByTestId("printed-handle-setup-dialog")).toBeVisible();
    await expect(
      page.getByTestId("handle-setup-tool-construction").locator("option"),
    ).toHaveCount(2);
    await expect(
      page.getByTestId("handle-setup-tool-construction"),
    ).toHaveValue("");
    await expect(page.getByTestId("handle-setup-orientation")).toHaveValue(
      "side",
    );
    for (const role of profiles)
      await expect(
        page.getByTestId(`handle-setup-profile-${role}`),
      ).toHaveValue(`profiles/${role}.json`);
    await expect(page.getByTestId("handle-setup-propose")).toBeDisabled();
    expect(scopes).toHaveLength(2);
    expect(scopes[1]).toEqual(scopes[0]);
    expect(scopes[1]).toMatchObject({
      expected_storage_digest: document.storage_digest,
      path: document.path,
      session_id: "session-recovery",
    });
    await page
      .getByTestId("handle-setup-tool-construction")
      .selectOption("fixture-construction__tool");
    await expect(page.getByTestId("handle-setup-propose")).toBeEnabled();
    await page.getByTestId("handle-setup-orientation").scrollIntoViewIfNeeded();
    await page.screenshot({
      path: testInfo.outputPath("retained-setup-selections.png"),
    });
    failRefresh = true;
    await page.getByRole("button", { name: "Refresh choices" }).click();
    await expect(
      page
        .getByRole("alert")
        .filter({ hasText: "Fixture current-source refresh unavailable" }),
    ).toBeVisible();
    await expect(page.getByTestId("handle-setup-accept")).toBeDisabled();
    failRefresh = false;
    available = false;
    await page.getByRole("button", { name: "Refresh choices" }).click();
    await expect(
      page.getByRole("button", { name: "Configure the CAD tool" }),
    ).toBeVisible();
    await expect(page.getByTestId("handle-setup-profile-machine")).toHaveValue(
      "profiles/machine.json",
    );
    await expect(page.getByTestId("handle-setup-propose")).toBeDisabled();
    await page.getByRole("button", { name: "Close handle setup" }).click();
    await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible();
    expect(workspace.current()?.storage_digest).toBe(document.storage_digest);
    expect(workspace.updateCount()).toBe(0);
    expect(workspace.runRequestCount()).toBe(0);
    expect(
      writes.filter((path) =>
        /setup\/(proposals|accept)|\/run|\/install|\/enable/.test(path),
      ),
    ).toEqual([]);
    await testInfo.attach("labelled-fixture-scopes-and-actions", {
      body: JSON.stringify({ scopes, writes, fixture: true }, null, 2),
      contentType: "application/json",
    });
  });
}

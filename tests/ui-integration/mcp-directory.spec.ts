import { test, expect } from "@playwright/test";

const liveExpect = expect.configure({ timeout: 60_000 });

test.describe("MCP Tool Registry Directory E2E Flow @live", () => {
  test("previews an advanced local MCP without registering it", async ({
    page,
  }) => {
    test.setTimeout(90_000);
    // 1. Navigate to the tool registry page
    await page.goto("/tool-registry");
    await liveExpect(
      page.getByRole("heading", { name: "Engineering MCP Server Library" }),
    ).toBeVisible();

    // 2. Confirm the current catalog projection loaded. Its contents can vary
    // with the active signed snapshot and are not part of this custom flow.
    await liveExpect(page.getByTestId("capability-results")).toBeVisible();

    // 3. Open the guided flow and choose an advanced local command.
    await page.getByRole("button", { name: "Add custom MCP server" }).click();
    const dialog = page.getByRole("dialog", {
      name: "Add custom MCP server",
    });
    await liveExpect(dialog).toBeVisible();
    await dialog.getByTestId("onboarding-source-kind").selectOption("local");

    // 4. Fill only literal, non-shell fields.
    const serverName = `Playwright Test CLI - ${Date.now()}`;
    await dialog.getByLabel("Display name").fill(serverName);
    await dialog.getByLabel("Literal executable").fill("python");
    await dialog.getByLabel("Literal arguments").fill("scripts/dummy.py");

    // 5. Preflight is read-only. Review the exact local command without
    // registering it or requiring an irrelevant publisher acknowledgement.
    await dialog.getByRole("button", { name: "Review install plan" }).click();
    await liveExpect(dialog.getByText("Confirm this installation")).toBeVisible();
    await liveExpect(dialog.getByText("What Wright will do")).toBeVisible();

    // 6. The preview did not register a server row.
    await dialog.getByRole("button", { name: "Close onboarding" }).click();
    await liveExpect(
      page.getByRole("heading", { name: serverName }),
    ).not.toBeVisible();
  });
});

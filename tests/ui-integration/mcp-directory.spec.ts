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

    // 2. Check default seeded CalculiX card exists
    await liveExpect(
      page.getByRole("heading", { name: "CalculiX Simulation" }),
    ).toBeVisible();

    // 3. Open the guided flow and choose an advanced local command.
    await page.getByRole("button", { name: "Add custom MCP server" }).click();
    await liveExpect(page.getByRole("dialog")).toBeVisible();
    await page.getByLabel("Source").selectOption("local");

    // 4. Fill only literal, non-shell fields.
    const serverName = `Playwright Test CLI - ${Date.now()}`;
    await page.getByLabel("Display name").fill(serverName);
    await page.getByLabel("Literal executable").fill("python");
    await page.getByLabel("Literal arguments").fill("scripts/dummy.py");

    // 5. Preflight is read-only. Review the exact local command without
    // registering it or requiring an irrelevant publisher acknowledgement.
    await page.getByRole("button", { name: "Review install plan" }).click();
    await liveExpect(page.getByText("Confirm this installation")).toBeVisible();
    await liveExpect(page.getByText("What Wright will do")).toBeVisible();

    // 6. The preview did not register a server row.
    await page.getByRole("button", { name: "Close onboarding" }).click();
    await liveExpect(
      page.getByRole("heading", { name: serverName }),
    ).not.toBeVisible();
  });
});

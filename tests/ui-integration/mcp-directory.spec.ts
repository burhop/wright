import { test, expect } from "@playwright/test";

const liveExpect = expect.configure({ timeout: 15_000 });

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

    // 5. Preflight is read-only and imported sources remain blocked until the
    // independent publisher/license review is complete.
    await page.getByRole("button", { name: "Continue" }).click();
    await liveExpect(page.getByText("Review exact plan")).toBeVisible();
    await liveExpect(page.getByText("Plan is blocked")).toBeVisible();

    // 6. The preview did not register a server row.
    await page.getByRole("button", { name: "Close onboarding" }).click();
    await liveExpect(
      page.getByRole("heading", { name: serverName }),
    ).not.toBeVisible();
  });
});

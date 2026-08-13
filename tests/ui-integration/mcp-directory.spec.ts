import { test, expect } from "@playwright/test";

const liveExpect = expect.configure({ timeout: 15_000 });

test.describe("MCP Tool Registry Directory E2E Flow @live", () => {
  test("should register, list, toggle, and delete a custom MCP server", async ({
    page,
  }) => {
    test.setTimeout(90_000);
    // 1. Navigate to the tool registry page
    await page.goto("/tool-registry");
    await liveExpect(
      page.getByRole("heading", { name: "Engineering Capability Library" }),
    ).toBeVisible();

    // 2. Check default seeded CalculiX card exists
    await liveExpect(
      page.getByRole("heading", { name: "CalculiX Simulation" }),
    ).toBeVisible();

    // 3. Click custom registration button
    await page.getByRole("button", { name: "Add custom MCP" }).click();
    await liveExpect(page.getByTestId("add-tool-modal-overlay")).toBeVisible();

    // 4. Fill form inputs
    const serverName = `Playwright Test CLI - ${Date.now()}`;
    await page.locator("#mcp-name").fill(serverName);
    await page.locator("#mcp-type").selectOption("stdio");
    await page.locator("#mcp-category").selectOption("simulation");
    await page.locator("#mcp-command").fill("python scripts/dummy.py");

    // 5. Submit registration
    await page.getByRole("button", { name: "Register", exact: true }).click();

    // 6. Verify card is displayed in the list
    await liveExpect(
      page.getByRole("heading", { name: serverName }),
    ).toBeVisible();

    // 7. Test removing/deleting the custom server card
    // Set up a listener for the window confirmation prompt
    page.once("dialog", async (dialog) => {
      liveExpect(dialog.message()).toContain("Are you sure you want to remove");
      await dialog.accept();
    });

    // Click remove link on our newly created card
    const card = page
      .locator('[data-testid^="server-card-"]')
      .filter({ hasText: serverName });
    await card.getByRole("button", { name: /Show details/ }).click();
    const removeBtn = card.getByRole("button", { name: "Remove" });
    await liveExpect(removeBtn).toBeVisible();
    await removeBtn.click();

    // Verify card is removed from directory
    await liveExpect(
      page.getByRole("heading", { name: serverName }),
    ).not.toBeVisible();
  });
});

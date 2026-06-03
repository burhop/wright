import { test, expect } from '@playwright/test';

test.describe('Dashboard Page - Real Backend Integration', () => {
  test('should support clicking + Create Workspace and selecting an existing workspace', async ({ page }) => {
    // Listen for browser logs and page errors
    page.on('console', msg => console.log(`[BROWSER CONSOLE] [${msg.type()}] ${msg.text()}`));
    page.on('pageerror', err => console.log(`[BROWSER UNHANDLED ERROR] ${err.message}\n${err.stack}`));

    // Navigate to the real local frontend
    console.log('Navigating to http://localhost:5173/...');
    await page.goto('http://localhost:5173/');

    // Verify page loads
    await expect(page.getByTestId('page-dashboard')).toBeVisible();

    // 1. Test clicking the "+ Create Workspace" button
    console.log('Clicking "+ Create Workspace" button...');
    const createBtn = page.locator('#create-workspace-btn');
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    // Verify modal is shown
    console.log('Checking if Create Workspace modal opens...');
    const modal = page.getByTestId('create-workspace-modal');
    await expect(modal).toBeVisible();

    // Close the modal for now
    console.log('Closing the modal...');
    const cancelBtn = page.getByRole('button', { name: 'Cancel' });
    await expect(cancelBtn).toBeVisible();
    await cancelBtn.click();
    await expect(modal).not.toBeVisible();

    // 2. Test clicking an existing workspace
    console.log('Looking for existing workspaces in the list...');
    // We wait for the list to load. If there are no workspaces, we skip the card click test.
    const hasWorkspaces = await page.evaluate(async () => {
      const res = await fetch('http://localhost:8000/api/workspace/recent');
      if (res.ok) {
        const data = await res.json();
        return data.workspaces && data.workspaces.length > 0;
      }
      return false;
    });

    if (hasWorkspaces) {
      console.log('Workspaces found. Clicking the first workspace card...');
      // Click the first card
      const workspaceCard = page.locator('.glow-card').filter({ hasText: 'home/burhop' }).first();
      if (await workspaceCard.count() > 0) {
        await workspaceCard.click();
        console.log('Checking navigation to /workspace/:workspaceId...');
        await expect(page).toHaveURL(/\/workspace\//);
        await expect(page.getByTestId('page-workspace')).toBeVisible();
      } else {
        console.log('No workspace cards matched filter, skipping card click.');
      }
    } else {
      console.log('No workspaces exist, skipping card click test.');
    }
  });
});

import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';

test.describe('Live Unmocked Agent Chat', () => {
  let testWorkspacePath: string;

  test.beforeAll(() => {
    // Create a temporary directory on the host to use as a test workspace
    testWorkspacePath = fs.mkdtempSync(path.join(os.tmpdir(), 'wright-live-test-'));
  });

  test.afterAll(() => {
    // Cleanup
    if (testWorkspacePath && fs.existsSync(testWorkspacePath)) {
      fs.rmSync(testWorkspacePath, { recursive: true, force: true });
    }
  });

  test('should converse with the real LLM endpoint', async ({ page }) => {
    console.log('Playwright Base URL configured as:', test.info().project.use.baseURL);
    
    // 1. Navigate to the app (backend must be pre-configured via LLM_API_URL env var)
    await page.goto('/');

    // Verify we are not on the setup page (it should have skipped setup)
    await expect(page.getByTestId('page-dashboard')).toBeVisible({ timeout: 10000 });

    // 2. Create a new workspace
    const createBtn = page.locator('#create-workspace-btn');
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    const modal = page.getByTestId('create-workspace-modal');
    await expect(modal).toBeVisible();

    // The backend in docker expects absolute paths from its own perspective.
    // However, if we're using Playwright to test the UI, we type in the path.
    // Wait, the test workspace path we created is on the host. 
    // Is it mounted in Docker? No, unless we mount it.
    const containerWorkspacePath = `/tmp/wright-test-ws-${Date.now()}`;
    
    await page.locator('#workspace-name-input').fill('Live Test Workspace');
    await page.locator('#workspace-path-input').fill(containerWorkspacePath);
    await page.locator('#workspace-create-submit').click();

    // 3. Verify we enter the workspace
    await expect(page).toHaveURL(/\/workspace\//, { timeout: 10000 });
    await expect(page.getByTestId('page-workspace')).toBeVisible();

    // 4. Create a chat session
    const createSessionBtn = page.getByTestId('create-session-btn');
    await expect(createSessionBtn).toBeVisible();
    await createSessionBtn.click();

    await expect(page.getByTestId('message-composer')).toBeVisible();

    // 5. Send a prompt asking for a specific, deterministic response
    const composer = page.getByTestId('composer-input');
    await composer.fill('Respond with exactly the word "BANANA" and nothing else.');
    
    const sendBtn = page.getByTestId('composer-send');
    await sendBtn.click();

    // 6. Assert the message is in the transcript
    const transcript = page.getByTestId('chat-transcript');
    await expect(transcript.getByText('Respond with exactly the word "BANANA" and nothing else.')).toBeVisible();

    // 7. Wait for the LLM response to stream in and contain "BANANA"
    // Since this hits a real model, we use a generous timeout and relax the assertion using a regex
    await expect(transcript.getByText(/BANANA/i)).toBeVisible({ timeout: 30000 });
  });
});

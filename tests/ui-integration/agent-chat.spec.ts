import { test, expect } from '@playwright/test';

test.describe('Agent Chat Page', () => {
  test('should support session creation, messaging flow, and workspace toggle', async ({ page }) => {
    await page.goto('/agent-chat');

    await expect(page.getByTestId('chat-layout')).toBeVisible();
    await expect(page.getByTestId('sessions-sidebar')).toBeVisible();
    await expect(page.getByTestId('chat-transcript')).toBeVisible();
    await expect(page.getByTestId('workspace-panel')).toBeVisible();

    const createBtn = page.getByTestId('create-session-btn');
    await expect(createBtn).toBeVisible();
    await createBtn.click();

    await expect(page.getByTestId('message-composer')).toBeVisible();

    const composer = page.getByTestId('composer-input');
    await composer.fill('Run stiffness analysis');
    
    const sendBtn = page.getByTestId('composer-send');
    await sendBtn.click();

    await expect(page.getByTestId('chat-transcript').getByText('Run stiffness analysis')).toBeVisible();
    await expect(page.getByTestId('active-tool')).toBeVisible();
    await expect(page.getByText(/processing your mechanical designs/i)).toBeVisible({ timeout: 10000 });

    const toggleBtn = page.getByTestId('toggle-workspace-btn');
    await toggleBtn.click();
    await expect(page.getByTestId('workspace-panel')).not.toBeVisible();

    await toggleBtn.click();
    await expect(page.getByTestId('workspace-panel')).toBeVisible();
  });
});

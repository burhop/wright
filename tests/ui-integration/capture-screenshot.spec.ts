import { test, expect } from '@playwright/test';

test('capture all screenshots', async ({ page }) => {
  // Capture initial dashboard view
  console.log('Navigating to /...');
  await page.goto('/');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/home/burhop/repos/wright/screenshot_initial.png' });

  // Get or create workspace ID to capture agent chat view
  let workspaceId = 'ws-screenshot';
  try {
    const response = await page.evaluate(async () => {
      const res = await fetch('/api/workspace/recent');
      if (res.ok) {
        const data = await res.json();
        if (data.workspaces && data.workspaces.length > 0) {
          return data.workspaces[0].workspace_id;
        }
      }
      return null;
    });

    if (response) {
      console.log(`Found existing workspace to screenshot: ${workspaceId}`);
      workspaceId = response;
    } else {
      console.log('No existing workspaces found. Creating a temporary workspace...');
      const newWs = await page.evaluate(async () => {
        const res = await fetch('/api/workspace/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Screenshot Project', local_path: '/home/burhop/repos/wright' })
        });
        if (res.ok) {
          const data = await res.json();
          return data.workspace_id;
        }
        return null;
      });
      if (newWs) {
        workspaceId = newWs;
      }
    }
  } catch (err) {
    console.warn('Error finding/creating workspace for screenshot:', err);
  }

  // Navigate to workspace page
  const chatPath = `/workspace/${workspaceId}`;
  console.log(`Navigating to ${chatPath}...`);
  await page.goto(chatPath);
  await page.waitForTimeout(4000); // Allow workspace loading thinking-dots to complete
  await page.screenshot({ path: '/home/burhop/repos/wright/screenshot_agent_chat.png' });

  // Capture tool registry
  console.log('Navigating to /tool-registry...');
  await page.goto('/tool-registry');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/home/burhop/repos/wright/screenshot_tool_registry.png' });

  // Capture file vault
  console.log('Navigating to /file-vault...');
  await page.goto('/file-vault');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/home/burhop/repos/wright/screenshot_file_vault.png' });

  console.log('All screenshots captured successfully!');
});

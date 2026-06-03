import { test } from '@playwright/test';

test('capture all screenshots', async ({ page }) => {
  const routes = [
    { name: 'initial', path: '/' },
    { name: 'agent_chat', path: '/agent-chat' },
    { name: 'tool_registry', path: '/tool-registry' },
    { name: 'file_vault', path: '/file-vault' }
  ];

  for (const route of routes) {
    console.log(`Navigating to http://localhost:5173${route.path}...`);
    await page.goto(`http://localhost:5173${route.path}`);
    await page.waitForTimeout(3000);
    const screenshotPath = `/home/burhop/repos/wright/screenshot_${route.name}.png`;
    console.log(`Saving screenshot to ${screenshotPath}...`);
    await page.screenshot({ path: screenshotPath });
  }
  console.log('All screenshots captured!');
});

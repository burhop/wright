import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const ssDir = path.join(process.cwd(), 'test-results', 'ui-smoke-screenshots');
  await mkdir(ssDir, { recursive: true });

  // Capture errors
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log(`  [HTTP ${response.status()}] ${response.url()}`);
    }
  });

  console.log('=== Step 1: Open app & create workspace ===');
  await page.goto('http://127.0.0.1:8090', { waitUntil: 'networkidle', timeout: 30000 });
  await page.click('#create-workspace-btn');
  await page.waitForSelector('[data-testid="create-workspace-modal"]', { timeout: 5000 });
  await page.fill('#workspace-name-input', 'Chat Test');
  await page.fill('#workspace-path-input', '/home/agent/workspace');
  await page.click('#workspace-create-submit');
  await page.waitForTimeout(3000);
  console.log('Workspace created');

  console.log('\n=== Step 2: Open workspace ===');
  await page.locator('text=Chat Test').first().click();
  await page.waitForTimeout(2000);
  console.log('Opened workspace');

  console.log('\n=== Step 3: Create session ===');
  await page.locator('[data-testid="create-session-btn"]').click({ force: true });
  await page.waitForTimeout(5000);

  // Check if session appeared in the dropdown
  const sessionSelect = page.locator('[data-testid="sessions-sidebar"]');
  const options = await sessionSelect.locator('option').allTextContents();
  console.log('Session options:', options);

  // Select the session if it exists but isn't selected
  if (options.length > 0 && options[0] !== 'No sessions') {
    // Select the first non-empty option
    const firstOption = await sessionSelect.locator('option').first();
    const value = await firstOption.getAttribute('value');
    if (value) {
      await sessionSelect.selectOption(value);
      console.log('Selected session:', value);
      await page.waitForTimeout(3000);
    }
  }

  await page.screenshot({ path: `${ssDir}/step3-session-selected.png`, fullPage: true });

  console.log('\n=== Step 4: Find chat input ===');
  // Check for textarea after session selection
  let chatInput = page.locator('textarea').first();
  let hasChatInput = await chatInput.isVisible({ timeout: 5000 }).catch(() => false);
  console.log('Textarea visible:', hasChatInput);

  if (!hasChatInput) {
    // Maybe it's an input or contenteditable
    const allInputs = await page.locator('input, textarea, [contenteditable]').count();
    console.log('Total input elements:', allInputs);
    
    // Dump the right panel HTML
    const rightPanel = await page.evaluate(() => {
      // Find elements containing "Agent" or "chat"
      const elements = document.querySelectorAll('*');
      let html = '';
      for (const el of elements) {
        if (el.className && typeof el.className === 'string' && 
            (el.className.includes('chat') || el.className.includes('agent') || el.className.includes('composer'))) {
          html += `<${el.tagName} class="${el.className}">${el.innerHTML.substring(0, 200)}\n`;
        }
      }
      return html || 'No chat/agent/composer elements found';
    });
    console.log('Chat-related elements:', rightPanel.substring(0, 1000));
  }

  if (hasChatInput) {
    console.log('\n=== Step 5: Send message ===');
    await chatInput.fill('Hello! Say the word Banana.');
    
    const sendBtn = page.locator('button[aria-label="Send"], button[title="Send"]').first();
    if (await sendBtn.isVisible().catch(() => false)) {
      await sendBtn.click();
    } else {
      await chatInput.press('Enter');
    }
    console.log('Message sent');

    console.log('\n=== Step 6: Wait for response ===');
    try {
      await page.waitForFunction(
        () => document.body.innerText.includes('Banana') || document.body.innerText.includes('banana'),
        { timeout: 45000 }
      );
      console.log('✅ SUCCESS: "Banana" appeared in the chat!');
    } catch {
      console.log('⚠ Timeout');
    }
    await page.screenshot({ path: `${ssDir}/step6-response.png`, fullPage: true });
  } else {
    console.log('❌ No chat input found');
    await page.screenshot({ path: `${ssDir}/step4-no-chat.png`, fullPage: true });
  }

  await browser.close();
})();

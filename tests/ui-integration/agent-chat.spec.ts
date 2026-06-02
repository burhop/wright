import { test, expect } from '@playwright/test';

test.describe('Agent Chat Page', () => {
  test('should support session creation, messaging flow, and workspace toggle', async ({ page }) => {
    // Mock health endpoints
    await page.route('**/api/agent/health', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ state: 'connected', latencyMs: 5.0 }),
      });
    });

    await page.route('**/api/inference/health', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ state: 'connected', latencyMs: 12.0 }),
      });
    });

    // Mock session list
    await page.route('**/api/agent/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: [] }),
      });
    });

    // Mock session creation
    await page.route('**/api/agent/sessions/new', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'session123',
          title: 'Untitled',
          created_at: Date.now(),
        }),
      });
    });

    // Mock chat turn initiation
    await page.route('**/api/agent/chat/start', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          stream_id: 'stream123',
          session_id: 'session123',
        }),
      });
    });

    // Mock SSE chat response stream
    await page.route('**/api/agent/chat/stream*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        headers: {
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
        body: [
          'event: tool\n',
          'data: {"name": "calculate_stress", "preview": "Analyzing stress fields..."}\n\n',
          'event: token\n',
          'data: {"text": "I have received your request: \\"Run stiffness analysis\\". As a local offline assistant in v1, I am processing your mechanical designs."}\n\n',
          'event: stream_end\n',
          'data: {"session_id": "session123"}\n\n'
        ].join(''),
      });
    });

    // Mock EventSource to simulate streaming over time with delays
    await page.addInitScript(() => {
      class MockEventSource extends EventTarget {
        url: string;
        constructor(url: string) {
          super();
          this.url = url;
          // Simulate streaming events with delay so the UI stays in intermediate states long enough for assertions
          setTimeout(() => {
            const event = new MessageEvent('tool', {
              data: JSON.stringify({ name: 'calculate_stress', preview: 'Analyzing stress fields...' })
            });
            this.dispatchEvent(event);
          }, 100);

          setTimeout(() => {
            const event = new MessageEvent('progress', {
              data: JSON.stringify({ percentage: 50, message: 'Solving stiffness equations (50% done)...' })
            });
            this.dispatchEvent(event);
          }, 150);

          setTimeout(() => {
            const event = new MessageEvent('token', {
              data: JSON.stringify({ text: 'I have received your request: **Run stiffness analysis**. As a local offline assistant in v1, I am processing your mechanical designs.' })
            });
            this.dispatchEvent(event);
          }, 200);

          setTimeout(() => {
            const event = new MessageEvent('stream_end', {
              data: JSON.stringify({ session_id: 'session123' })
            });
            this.dispatchEvent(event);
          }, 400);
        }
        close() {}
      }
      (window as any).EventSource = MockEventSource;
    });

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
    
    // Check tool progress displays correctly
    await expect(page.getByTestId('progress-percentage')).toHaveText('50%');
    await expect(page.getByTestId('progress-bar')).toBeVisible();

    await expect(page.getByText(/processing your mechanical designs/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('chat-transcript').locator('strong')).toHaveText('Run stiffness analysis');

    const toggleBtn = page.getByTestId('toggle-workspace-btn');
    await toggleBtn.click();
    await expect(page.getByTestId('workspace-panel')).not.toBeVisible();

    await toggleBtn.click();
    await expect(page.getByTestId('workspace-panel')).toBeVisible();
  });
});

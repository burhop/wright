import { test, expect } from '@playwright/test';

test.describe('Pluggable Viewer Panel Lifecycle E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Mock setup status
    await page.route('**/api/setup/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ is_configured: true, theme: 'dark' }),
      });
    });

    // Mock active agent
    await page.route('**/api/agent/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify('hermes'),
      });
    });

    // Mock agent sessions list
    await page.route('**/api/agent/sessions*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          sessions: [
            {
              session_id: 'session-1',
              title: 'Default Session',
              created_at: Date.now(),
              updated_at: Date.now(),
            },
          ],
        }),
      });
    });

    // Mock workspace info
    await page.route('**/api/workspace/by-id/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspace_id: 'ws-1',
          session_id: 'session-1',
          workspace_name: 'Test Project',
          local_path: '/home/burhop/repos/wright',
          git_remote_url: null,
          git_username: null,
        }),
      });
    });

    // Mock workspace activation
    await page.route('**/api/workspace/activate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          session_id: 'session-1',
          workspace_path: '/home/burhop/repos/wright',
        }),
      });
    });

    // Mock file tree list
    await page.route('**/api/workspace/files?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workspace: {
            name: 'wright',
            path: '/',
            type: 'directory',
            children: [
              {
                name: 'cube.stl',
                path: '/cube.stl',
                type: 'file',
                size: 80,
                last_modified: 1000,
                git_status: 'Clean',
                children: null,
              },
              {
                name: 'script.py',
                path: '/script.py',
                type: 'file',
                size: 200,
                last_modified: 1000,
                git_status: 'Clean',
                children: null,
              },
              {
                name: 'document.pdf',
                path: '/document.pdf',
                type: 'file',
                size: 300,
                last_modified: 1000,
                git_status: 'Clean',
                children: null,
              },
              {
                name: 'image.png',
                path: '/image.png',
                type: 'file',
                size: 500,
                last_modified: 1000,
                git_status: 'Clean',
                children: null,
              },
              {
                name: 'sandbox.html',
                path: '/sandbox.html',
                type: 'file',
                size: 150,
                last_modified: 1000,
                git_status: 'Clean',
                children: null,
              },
              {
                name: 'error_script.py',
                path: '/error_script.py',
                type: 'file',
                size: 200,
                last_modified: 1000,
                git_status: 'Clean',
                children: null,
              },
            ],
          },
        }),
      });
    });

    // Mock file contents
    await page.route('**/api/workspace/files/content?*', async (route) => {
      const url = new URL(route.request().url());
      const filePath = url.searchParams.get('path') || '';

      if (filePath.endsWith('.stl')) {
        // Return dummy binary data for STL
        const buffer = Buffer.alloc(80);
        await route.fulfill({
          status: 200,
          contentType: 'application/octet-stream',
          body: buffer,
        });
      } else if (filePath.endsWith('error_script.py')) {
        await route.fulfill({
          status: 200,
          contentType: 'text/plain',
          body: "raise ValueError('Mocked execution error')",
        });
      } else if (filePath.endsWith('.py')) {
        // Return python code
        await route.fulfill({
          status: 200,
          contentType: 'text/plain',
          body: "print('Hello Playwright Pluggable Viewer')",
        });
      } else if (filePath.endsWith('.pdf')) {
        // Return dummy PDF buffer
        const buffer = Buffer.from('%PDF-1.4 ... mock pdf content ...');
        await route.fulfill({
          status: 200,
          contentType: 'application/pdf',
          body: buffer,
        });
      } else if (filePath.endsWith('.png')) {
        const buffer = Buffer.alloc(20);
        await route.fulfill({
          status: 200,
          contentType: 'image/png',
          body: buffer,
        });
      } else if (filePath.endsWith('.html')) {
        await route.fulfill({
          status: 200,
          contentType: 'text/html',
          body: '<html><body><h3>Hello HTML Sandbox</h3></body></html>',
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'text/plain',
          body: 'Plain fallback content',
        });
      }
    });

    // Mock git status and history to avoid console errors
    await page.route('**/api/workspace/git/status?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ branch_name: 'main', changes: [] }),
      });
    });
    await page.route('**/api/workspace/git/history?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ commits: [] }),
      });
    });

    // Mock file run endpoint
    await page.route('**/api/workspace/files/run', async (route) => {
      if (route.request().method() === 'POST') {
        const body = JSON.parse(route.request().postData() || '{}');
        if (body.path && body.path.includes('error_script.py')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              success: false,
              stdout: '',
              stderr: 'Traceback (most recent call):\nValueError: Mocked execution error',
              exit_code: 1,
            }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              success: true,
              stdout: 'Hello script execution output!\n[Done]',
              stderr: '',
              exit_code: 0,
            }),
          });
        }
      } else {
        await route.fallback();
      }
    });
  });

  test('should open and mount the 3D STL viewer when clicking cube.stl', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand the root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Find and click the stl file in explorer tree
    const stlFile = page.locator('[data-testid="file-node-/cube.stl"]');
    await expect(stlFile).toBeVisible();
    await stlFile.click();

    // Verify tab created and active
    const stlTab = page.locator('[data-testid="editor-tab-/cube.stl"]');
    await expect(stlTab).toBeVisible();
    await expect(stlTab).toHaveAttribute('data-testid', 'editor-tab-/cube.stl');

    // Verify 3D canvas inside the viewer-container
    const canvas = page.locator('[data-testid="3d-canvas"]');
    await expect(canvas).toBeVisible();
  });

  test('should open and mount the Code Editor when clicking script.py', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand the root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Find and click the python file in explorer tree
    const pyFile = page.locator('[data-testid="file-node-/script.py"]');
    await expect(pyFile).toBeVisible();
    await pyFile.click();

    // Verify tab created and active
    const pyTab = page.locator('[data-testid="editor-tab-/script.py"]');
    await expect(pyTab).toBeVisible();

    // Verify textarea editor is loaded with content
    const textarea = page.locator('[data-testid="viewer-container"] textarea');
    await expect(textarea).toBeVisible();
    await expect(textarea).toHaveValue("print('Hello Playwright Pluggable Viewer')");

    // Verify syntax highlighting overlay has print keyword and string styled
    const overlay = page.locator('[data-testid="code-editor-highlight-overlay"]');
    await expect(overlay).toBeVisible();
    const overlayHtml = await overlay.innerHTML();
    expect(overlayHtml).toContain('color: #569cd6'); // keyword color
    expect(overlayHtml).toContain('color: #ce9178'); // string color

    // Verify Run button is visible and execute it
    const runBtn = page.locator('[data-testid="run-python-btn"]');
    await expect(runBtn).toBeVisible();
    await runBtn.click();

    // Verify execution output console shows up
    const consolePanel = page.locator('[data-testid="code-editor-console"]');
    await expect(consolePanel).toBeVisible();
    const consoleBody = page.locator('[data-testid="code-editor-console-body"]');
    await expect(consoleBody).toContainText('Hello script execution output!');

    // Make edits and check if dirty changes trigger Save button visibility
    await textarea.fill("print('Hello Playwright Pluggable Viewer Edited')");
    const saveButton = page.locator('button:has-text("Save Changes")');
    await expect(saveButton).toBeVisible();
  });

  test('should open and mount the PDF Document Viewer when clicking document.pdf', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand the root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Find and click the pdf file in explorer tree
    const pdfFile = page.locator('[data-testid="file-node-/document.pdf"]');
    await expect(pdfFile).toBeVisible();
    await pdfFile.click();

    // Verify tab created and active
    const pdfTab = page.locator('[data-testid="editor-tab-/document.pdf"]');
    await expect(pdfTab).toBeVisible();

    // Verify pdf iframe inside the viewer-container
    const pdfIframe = page.locator('[data-testid="pdf-iframe"]');
    await expect(pdfIframe).toBeVisible();
  });

  test('should open and mount the Image Viewer when clicking image.png', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand the root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Find and click the image file in explorer tree
    const imgFile = page.locator('[data-testid="file-node-/image.png"]');
    await expect(imgFile).toBeVisible();
    imgFile.click();

    // Verify tab created and active
    const imgTab = page.locator('[data-testid="editor-tab-/image.png"]');
    await expect(imgTab).toBeVisible();

    // Verify image inside the viewer-container
    const imgElement = page.locator('[data-testid="image-viewer-img"]');
    await expect(imgElement).toBeVisible();
    const src = await imgElement.getAttribute('src');
    expect(src).toContain('path=%2Fimage.png');
    expect(src).toContain('session_id=session-1');
  });

  test('should open and mount the HTML Previewer when clicking sandbox.html', async ({ page }) => {
    await page.goto('/workspace/ws-1');

    // Expand the root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Find and click the html file in explorer tree
    const htmlFile = page.locator('[data-testid="file-node-/sandbox.html"]');
    await expect(htmlFile).toBeVisible();
    htmlFile.click();

    // Verify tab created and active
    const htmlTab = page.locator('[data-testid="editor-tab-/sandbox.html"]');
    await expect(htmlTab).toBeVisible();

    // Verify iframe sandbox inside the viewer-container
    const iframeSandbox = page.locator('[data-testid="iframe-sandbox"]');
    await expect(iframeSandbox).toBeVisible();
    const src = await iframeSandbox.getAttribute('src');
    expect(src).toContain('path=%2Fsandbox.html');
    expect(src).toContain('session_id=session-1');
  });

  test('should show fix button on error output and trigger agent chat on click', async ({ page }) => {
    let lastSentMessage = '';
    await page.route('**/api/agent/chat/start', async (route) => {
      const body = JSON.parse(route.request().postData() || '{}');
      lastSentMessage = body.message;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ stream_id: 'mock-stream-123' }),
      });
    });

    await page.route('**/api/agent/chat/stream?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: 'event: done\ndata: {"session": {"sessionId": "session-1", "messages": []}}\n\n',
      });
    });

    await page.goto('/workspace/ws-1');

    // Expand root folder
    const rootFolder = page.locator('[data-testid="file-node-/"]');
    await expect(rootFolder).toBeVisible();
    await rootFolder.click();

    // Click error python script
    const pyFile = page.locator('[data-testid="file-node-/error_script.py"]');
    await expect(pyFile).toBeVisible();
    await pyFile.click();

    // Verify textarea is loaded
    const textarea = page.locator('[data-testid="viewer-container"] textarea');
    await expect(textarea).toBeVisible();

    // Click Run button
    const runBtn = page.locator('[data-testid="run-python-btn"]');
    await expect(runBtn).toBeVisible();
    await runBtn.click();

    // Verify console panel opens and error output is shown
    const consolePanel = page.locator('[data-testid="code-editor-console"]');
    await expect(consolePanel).toBeVisible();

    // Verify fix-error-btn is visible and click it
    const fixBtn = page.locator('[data-testid="fix-error-btn"]');
    await expect(fixBtn).toBeVisible();
    await fixBtn.click();

    // Assert that the message was sent to the session containing correct prompt
    expect(lastSentMessage).toContain('When executing @error_script.py we got this output. Fix any problems:');
    expect(lastSentMessage).toContain('Traceback (most recent call):');
    expect(lastSentMessage).toContain('ValueError: Mocked execution error');
  });
});

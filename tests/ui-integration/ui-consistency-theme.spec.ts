import { test, expect } from '@playwright/test';

const MOCK_SERVER_METADATA = {
  verification_state: "verified_mcp",
  installability_tier: "might_work",
  risk_level: "low",
  deployment_mode: "unknown",
  platform_support: {
    windows_11_x64: { status: "unknown", tested: false, notes: "not tested" },
    linux_x64: { status: "unknown", tested: false, notes: "not tested" },
    linux_arm64: { status: "unknown", tested: false, notes: "not tested" },
    macos_x64: { status: "unknown", tested: false, notes: "not tested" },
    macos_arm64: { status: "unknown", tested: false, notes: "not tested" },
  },
  host_software_required: [],
  credentials_required: [],
  default_enabled: true,
  approval_gates: [],
  validation_result: {
    status: "not_tested",
    message: "Not yet validated in this environment",
    missing_dependencies: [],
  },
};

const MOCK_SERVERS = [
  {
    ...MOCK_SERVER_METADATA,
    server_id: "calc-mcp-id",
    name: "CalculiX Simulation",
    type: "stdio",
    command: ["uv", "run", "calculix-mcp"],
    is_active: false,
    is_installed: false,
    status: "inactive",
    error_message: null,
    category: "simulation",
    created_at: 1000,
    updated_at: 1000,
    image_url: "https://github.com/CalculiX.png?size=64",
    description: "Finite element analysis solver.",
    source_url: "https://github.com/calculix/calculix-mcp",
    installed_version: "2.21.0"
  },
  {
    ...MOCK_SERVER_METADATA,
    installability_tier: "tested",
    server_id: "openscad-mcp-id",
    name: "OpenSCAD Geometry",
    type: "stdio",
    command: ["uv", "run", "openscad-mcp"],
    is_active: false,
    is_installed: true,
    status: "inactive",
    error_message: null,
    category: "cad",
    created_at: 1000,
    updated_at: 1000,
    image_url: "https://github.com/openscad.png?size=64",
    description: "OpenSCAD 3D CAD modeler. Fast, script-based solid modeling tool.",
    source_url: "https://github.com/quellant/openscad-mcp",
    installed_version: "1.0.0"
  }
];

const MOCK_TOOLS: any[] = [];

test.describe('UI Consistency and Theme Configuration', () => {

  test('should propagate the backend-configured dark theme to the document element', async ({ page }) => {
    // Mock setup status returning dark theme
    await page.route('**/api/setup/status', async (route) => {
      await route.fulfill({
        json: {
          is_configured: true,
          llm_api_url: "http://127.0.0.1:8000",
          active_agent: "hermes",
          theme: "dark"
        }
      });
    });

    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.goto('/tool-registry');

    // Confirm that the document root (html or body) contains the data-theme attribute
    const themeAttr = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
    expect(themeAttr).toBe('dark');
  });

  test('should propagate the backend-configured light theme to the document element', async ({ page }) => {
    // Mock setup status returning light theme
    await page.route('**/api/setup/status', async (route) => {
      await route.fulfill({
        json: {
          is_configured: true,
          llm_api_url: "http://127.0.0.1:8000",
          active_agent: "hermes",
          theme: "light"
        }
      });
    });

    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.goto('/tool-registry');

    const themeAttr = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
    expect(themeAttr).toBe('light');
  });

  test('should ensure cards do not overlap and elements align correctly', async ({ page }) => {
    await page.route('**/api/setup/status', async (route) => {
      await route.fulfill({
        json: {
          is_configured: true,
          llm_api_url: "http://127.0.0.1:8000",
          active_agent: "hermes",
          theme: "dark"
        }
      });
    });

    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.goto('/tool-registry');

    // Check sizes of cards to make sure they are aligned
    const calcCard = page.locator('[data-testid="server-card-calc-mcp-id"]');
    const openscadCard = page.locator('[data-testid="server-card-openscad-mcp-id"]');

    await expect(calcCard).toBeVisible();
    await expect(openscadCard).toBeVisible();

    const calcBox = await calcCard.boundingBox();
    const openscadBox = await openscadCard.boundingBox();

    expect(calcBox).not.toBeNull();
    expect(openscadBox).not.toBeNull();

    // Verify there is no direct overlapping (non-zero width/height, non-equal top-left coordinates if rendering side-by-side or stacked)
    if (calcBox && openscadBox) {
      expect(calcBox.width).toBeGreaterThan(0);
      expect(openscadBox.width).toBeGreaterThan(0);
      
      // Ensure they don't occupy exactly the same coordinate space (overlapping)
      const isOverlapping = !(
        calcBox.x + calcBox.width <= openscadBox.x ||
        openscadBox.x + openscadBox.width <= calcBox.x ||
        calcBox.y + calcBox.height <= openscadBox.y ||
        openscadBox.y + openscadBox.height <= calcBox.y
      );
      expect(isOverlapping).toBe(false);
    }
  });
});

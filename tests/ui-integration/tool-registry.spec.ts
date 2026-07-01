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
    description: "Finite element analysis solver. Installing this server sets up the CalculiX MCP bridge via uvx.",
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
  },
  {
    ...MOCK_SERVER_METADATA,
    server_id: "network-mcp-id",
    name: "Custom SSE Link",
    type: "sse",
    command: "http://127.0.0.1:9000/sse",
    is_active: false,
    is_installed: false,
    status: "inactive",
    error_message: null,
    category: "analysis",
    created_at: 1000,
    updated_at: 1000,
    image_url: null,
    description: "Connect to a remote analysis server running over SSE.",
    source_url: null,
    installed_version: null
  }
];

const MOCK_TOOLS = [
  {
    tool_id: "calc-mcp-id:mesh_calc",
    server_id: "calc-mcp-id",
    name: "mesh_calc",
    description: "Calculate mesh density",
    input_schema: { type: "object" },
    is_enabled: true,
    created_at: 1000
  }
];

test.describe('Tool Registry Enhanced UI', () => {
  test.beforeEach(async ({ page }) => {
    // Mock setup status
    await page.route('**/api/setup/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_configured: true,
          llm_api_url: 'http://localhost:8000',
          active_agent: 'hermes',
          theme: 'dark'
        }),
      });
    });
  });

  test('should display server cards with logo, badge, description @US1', async ({ page }) => {
    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.goto('/tool-registry');
    
    // Assert logo/fallback
    await expect(page.getByTestId('server-card-logo-calc-mcp-id')).toBeVisible();
    await expect(page.getByTestId('server-card-logo-network-mcp-id')).toBeVisible();
    await expect(page.getByTestId('server-card-logo-network-mcp-id')).toHaveText('C');

    // Assert badges
    await expect(page.getByTestId('server-type-badge-stdio').first()).toBeVisible();
    await expect(page.getByTestId('server-type-badge-sse')).toBeVisible();

    // Assert description
    await expect(page.getByTestId('server-card-description-calc-mcp-id')).toBeVisible();
    await expect(page.getByTestId('server-card-description-calc-mcp-id')).toContainText('Finite element analysis solver.');

    // Test Search input
    const searchInput = page.getByTestId('tool-registry-search-input');
    await expect(searchInput).toBeVisible();
    await searchInput.fill('CalculiX');
    await expect(page.getByRole('heading', { name: 'CalculiX Simulation' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'OpenSCAD Geometry' })).not.toBeVisible();

    // Test sidebar category filters
    await searchInput.fill('');
    const localFilter = page.getByTestId('tool-registry-category-local');
    await localFilter.click();
    await expect(page.getByRole('heading', { name: 'CalculiX Simulation' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Custom SSE Link' })).not.toBeVisible();

    const networkFilter = page.getByTestId('tool-registry-category-network');
    await networkFilter.click();
    await expect(page.getByRole('heading', { name: 'Custom SSE Link' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'CalculiX Simulation' })).not.toBeVisible();
  });

  test('should install a local server showing progress and version @US2', async ({ page }) => {
    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.route('**/api/mcp/servers/calc-mcp-id/install*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 200));
      await route.fulfill({
        json: {
          server_id: "calc-mcp-id",
          is_installed: true,
          status: "inactive",
          error_message: null
        }
      });
    });

    await page.goto('/tool-registry');

    // Wait for initial render before overriding mock for post-install refresh
    await expect(page.getByTestId('server-card-install-btn-calc-mcp-id')).toBeVisible();

    await page.route('**/api/mcp/servers', async (route) => {
      const updatedServers = [...MOCK_SERVERS] as any[];
      updatedServers[0] = { ...updatedServers[0], is_installed: true, installed_version: "2.21.0" };
      await route.fulfill({ json: { servers: updatedServers } });
    });

    const installBtn = page.getByTestId('server-card-install-btn-calc-mcp-id');
    await expect(installBtn).toBeVisible();
    await expect(installBtn).toHaveText('Install');
    
    await installBtn.click();
    await expect(page.getByText('v2.21.0')).toBeVisible();
    await expect(page.getByTestId('server-card-uninstall-btn-calc-mcp-id')).toBeVisible();
  });

  test('should show error banner when install fails @US2', async ({ page }) => {
    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.route('**/api/mcp/servers/calc-mcp-id/install*', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: "Mock Installation Failure" })
      });
    });

    await page.goto('/tool-registry');

    await page.getByTestId('server-card-details-toggle-calc-mcp-id').click();

    const installBtn = page.getByTestId('server-card-install-btn-calc-mcp-id');
    await installBtn.click();

    const errorBanner = page.getByTestId('server-card-error-calc-mcp-id');
    await expect(errorBanner).toBeVisible();
    await expect(errorBanner).toContainText('Mock Installation Failure');

    await errorBanner.getByRole('button').click();
    await expect(errorBanner).not.toBeVisible();
  });

  test('should check for updates and run update flow @US3', async ({ page }) => {
    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.route('**/api/mcp/servers/openscad-mcp-id/version-check', async (route) => {
      await route.fulfill({
        json: {
          server_id: "openscad-mcp-id",
          installed: "1.0.0",
          latest: "1.2.0",
          update_available: true,
          error: null
        }
      });
    });

    await page.route('**/api/mcp/servers/openscad-mcp-id/update', async (route) => {
      await route.fulfill({
        json: {
          server_id: "openscad-mcp-id",
          installed_version: "1.2.0",
          success: true,
          error: null
        }
      });
    });

    await page.goto('/tool-registry');

    await page.getByTestId('server-card-details-toggle-openscad-mcp-id').click();

    const checkBtn = page.getByTestId('server-card-check-update-btn-openscad-mcp-id');
    await expect(checkBtn).toBeVisible();
    await checkBtn.click();

    const updateBanner = page.getByTestId('server-card-update-banner-openscad-mcp-id');
    await expect(updateBanner).toBeVisible();
    await expect(updateBanner).toContainText('v1.0.0 → v1.2.0');

    await page.route('**/api/mcp/servers', async (route) => {
      const updatedServers = [...MOCK_SERVERS] as any[];
      updatedServers[1] = { ...updatedServers[1], installed_version: "1.2.0" };
      await route.fulfill({ json: { servers: updatedServers } });
    });

    const updateBtn = page.getByTestId('server-card-update-btn-openscad-mcp-id');
    await expect(updateBtn).toBeVisible();
    await updateBtn.click();

    await expect(updateBanner).not.toBeVisible();
    await expect(page.getByText('v1.2.0')).toBeVisible();
    await expect(page.getByTestId('server-card-uninstall-btn-openscad-mcp-id')).toBeVisible();
  });

  test('should display Connect button for network servers and support connect/disconnect @US4', async ({ page }) => {
    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.route('**/api/mcp/servers/network-mcp-id/install*', async (route) => {
      await route.fulfill({
        json: {
          server_id: "network-mcp-id",
          is_installed: true,
          status: "active",
          error_message: null
        }
      });
    });

    await page.goto('/tool-registry');

    const connectBtn = page.getByTestId('server-card-connect-btn-network-mcp-id');
    await expect(connectBtn).toBeVisible();
    await expect(connectBtn).toHaveText('Connect');
    await expect(page.locator('[data-testid="server-card-install-btn-network-mcp-id"]')).not.toBeVisible();

    await page.route('**/api/mcp/servers', async (route) => {
      const updatedServers = [...MOCK_SERVERS] as any[];
      updatedServers[2] = { ...updatedServers[2], is_installed: true, status: "active" };
      await route.fulfill({ json: { servers: updatedServers } });
    });

    await connectBtn.click();

    const disconnectBtn = page.getByTestId('server-card-disconnect-btn-network-mcp-id');
    await expect(disconnectBtn).toBeVisible();
    await expect(disconnectBtn).toHaveText('Disconnect');
  });

  test('should prompt and uninstall local server, reverting to install state @US5', async ({ page }) => {
    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.route('**/api/mcp/servers/openscad-mcp-id/uninstall*', async (route) => {
      await route.fulfill({
        json: {
          server_id: "openscad-mcp-id",
          is_installed: false,
          status: "inactive",
          error_message: null
        }
      });
    });

    await page.goto('/tool-registry');

    // Wait for initial render before overriding mock for post-uninstall refresh
    await expect(page.getByTestId('server-card-uninstall-btn-openscad-mcp-id')).toBeVisible();

    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toContain('Are you sure you want to uninstall');
      await dialog.accept();
    });

    await page.route('**/api/mcp/servers', async (route) => {
      const updatedServers = [...MOCK_SERVERS] as any[];
      updatedServers[1] = { ...updatedServers[1], is_installed: false, status: "inactive" };
      await route.fulfill({ json: { servers: updatedServers } });
    });

    const uninstallBtn = page.getByTestId('server-card-uninstall-btn-openscad-mcp-id');
    await expect(uninstallBtn).toBeVisible();
    await uninstallBtn.click();

    await expect(page.getByTestId('server-card-install-btn-openscad-mcp-id')).toBeVisible();
  });

  test('should keep network type badge after a failed install/connect error', async ({ page }) => {
    await page.route('**/api/mcp/servers', async (route) => {
      await route.fulfill({ json: { servers: MOCK_SERVERS } });
    });
    await page.route('**/api/mcp/tools', async (route) => {
      await route.fulfill({ json: { tools: MOCK_TOOLS } });
    });

    await page.route('**/api/mcp/servers/network-mcp-id/install*', async (route) => {
      await route.fulfill({
        json: {
          server_id: "network-mcp-id",
          is_installed: true,
          status: "error",
          error_message: "Connection failed to network endpoint"
        }
      });
    });

    await page.goto('/tool-registry');

    // Confirm starting type is network
    const card = page.getByTestId('server-card-network-mcp-id');
    await expect(card.getByTestId('server-type-badge-sse')).toBeVisible();
    await page.getByTestId('server-card-details-toggle-network-mcp-id').click();

    const connectBtn = page.getByTestId('server-card-connect-btn-network-mcp-id');
    await connectBtn.click();

    // Verify error banner is shown
    const errorBanner = page.getByTestId('server-card-error-network-mcp-id');
    await expect(errorBanner).toBeVisible();
    await expect(errorBanner).toContainText('Connection failed to network endpoint');

    // Verify it is still a network badge and has NOT changed to stdio/local
    await expect(card.getByTestId('server-type-badge-sse')).toBeVisible();
    await expect(card.getByTestId('server-type-badge-stdio')).not.toBeVisible();
  });

  test('should display tool registry page heading @smoke', async ({ page }) => {
    await page.goto('/tool-registry');
    await expect(page.getByRole('heading', { name: 'Engineering Tool Registry' })).toBeVisible();
  });
});


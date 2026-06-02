import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ToolRegistryPage } from '../src/components/pages/ToolRegistryPage';
import { useTools } from '../src/store/tools';
import type { McpServer, McpTool } from '../src/services/mcp-service';

// Mock the useTools hook
vi.mock('../src/store/tools', () => ({
  useTools: vi.fn(),
  ToolsProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock logger hook to avoid logging output clutter
vi.mock('../src/hooks/useLogger', () => ({
  default: () => ({
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
  }),
}));

describe('ToolRegistryPage', () => {
  const mockServers: McpServer[] = [
    {
      server_id: 'server-1',
      name: 'Simulation Solver',
      type: 'stdio',
      command: ['uv', 'run', 'sim'],
      is_active: false,
      status: 'inactive',
      category: 'simulation',
      created_at: 1000,
      updated_at: 1000,
    },
    {
      server_id: 'server-2',
      name: 'CAD Extractor',
      type: 'sse',
      command: 'http://127.0.0.1:9090/sse',
      is_active: true,
      status: 'active',
      category: 'cad',
      created_at: 1000,
      updated_at: 1000,
    },
  ];

  const mockTools: McpTool[] = [
    {
      tool_id: 'server-2:get_layers',
      server_id: 'server-2',
      name: 'get_layers',
      description: 'Get CAD layers',
      input_schema: { type: 'object' },
      is_enabled: true,
      created_at: 1000,
    },
  ];

  const mockToggleServerState = vi.fn();
  const mockDeleteServerState = vi.fn();
  const mockToggleToolState = vi.fn();
  const mockRegisterCustomServer = vi.fn();
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useTools as any).mockReturnValue({
      servers: mockServers,
      tools: mockTools,
      isLoading: false,
      error: null,
      fetchServersAndTools: mockFetch,
      registerCustomServer: mockRegisterCustomServer,
      toggleServerState: mockToggleServerState,
      deleteServerState: mockDeleteServerState,
      toggleToolState: mockToggleToolState,
    });
  });

  it('renders registered servers and tools list', () => {
    render(<ToolRegistryPage />);

    expect(screen.getByText('Simulation Solver')).toBeInTheDocument();
    expect(screen.getByText('CAD Extractor')).toBeInTheDocument();
    
    // Server 1: stdio command display
    expect(screen.getByText('uv run sim')).toBeInTheDocument();
    // Server 2: URL display
    expect(screen.getByText('http://127.0.0.1:9090/sse')).toBeInTheDocument();
  });

  it('filters servers by search query input', () => {
    render(<ToolRegistryPage />);

    const searchInput = screen.getByPlaceholderText('Search MCP servers by name...');
    fireEvent.change(searchInput, { target: { value: 'Simulation' } });

    expect(screen.getByText('Simulation Solver')).toBeInTheDocument();
    expect(screen.queryByText('CAD Extractor')).not.toBeInTheDocument();
  });

  it('filters servers by category sidebar selection', () => {
    render(<ToolRegistryPage />);

    const cadBtn = screen.getByRole('button', { name: 'cad' });
    fireEvent.click(cadBtn);

    expect(screen.queryByText('Simulation Solver')).not.toBeInTheDocument();
    expect(screen.getByText('CAD Extractor')).toBeInTheDocument();
  });

  it('toggles server status and tools sub-checkboxes', async () => {
    render(<ToolRegistryPage />);

    // Click to enable server 1
    const enableBtn = screen.getAllByRole('button', { name: /Enable|Disable/ })[0]; // Simulation is Enable
    expect(enableBtn.textContent).toBe('Enable');
    
    fireEvent.click(enableBtn);
    expect(mockToggleServerState).toHaveBeenCalledWith('server-1', true);
  });
});

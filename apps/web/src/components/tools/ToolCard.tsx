import { useState } from 'react';
import type { McpServer, McpTool } from '../../services/mcp-service';
import { workspaceService, type WorkspaceInfo } from '../../services/workspace-service';

interface ToolCardProps {
  server: McpServer;
  tools: McpTool[];
  onInstall: (serverId: string, sessionId?: string | null) => Promise<void>;
  onUninstall: (serverId: string, sessionId?: string | null) => Promise<void>;
  onDelete: (serverId: string) => Promise<void>;
  onToggleTool: (toolId: string, enabled: boolean) => Promise<void>;
  workspaces: WorkspaceInfo[];
  activeSessionId: string | null;
  onRefreshWorkspaces: () => Promise<void>;
}

export function ToolCard({
  server,
  tools,
  onInstall,
  onUninstall,
  onDelete,
  onToggleTool,
  workspaces,
  activeSessionId,
  onRefreshWorkspaces,
}: ToolCardProps) {
  const [isInstalling, setIsInstalling] = useState(false);
  const [isUninstalling, setIsUninstalling] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [togglingWorkspaceId, setTogglingWorkspaceId] = useState<string | null>(null);

  const handleInstall = async () => {
    setIsInstalling(true);
    try {
      await onInstall(server.server_id, activeSessionId);
      await onRefreshWorkspaces();
    } catch (err) {
      console.error(err);
    } finally {
      setIsInstalling(false);
    }
  };

  const handleUninstall = async () => {
    if (!window.confirm(`Are you sure you want to uninstall "${server.name}"?`)) {
      return;
    }
    setIsUninstalling(true);
    try {
      await onUninstall(server.server_id, activeSessionId);
      await onRefreshWorkspaces();
    } catch (err) {
      console.error(err);
    } finally {
      setIsUninstalling(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to remove the MCP server "${server.name}"?`)) {
      return;
    }
    setIsDeleting(true);
    try {
      await onDelete(server.server_id);
    } catch (err) {
      console.error(err);
      setIsDeleting(false);
    }
  };

  const handleToggleWorkspace = async (w: WorkspaceInfo, isEnabled: boolean) => {
    setTogglingWorkspaceId(w.workspace_id);
    try {
      await workspaceService.toggleWorkspaceTool(w.session_id, server.server_id, isEnabled);
      await onRefreshWorkspaces();
    } catch (err) {
      console.error(err);
    } finally {
      setTogglingWorkspaceId(null);
    }
  };

  const getWorkspaceName = (path: string) => {
    const parts = path.split('/');
    return parts[parts.length - 1] || path;
  };

  const getStatusColor = () => {
    if (!server.is_installed) return 'rgba(255, 255, 255, 0.3)';
    if (server.status === 'active') return 'var(--color-success)';
    if (server.status === 'error') return 'var(--color-error)';
    return 'var(--color-secondary)';
  };

  return (
    <div
      data-testid={`server-card-${server.server_id}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-xl)',
        gap: 'var(--space-md)',
        transition: 'all var(--transition-smooth)',
        boxShadow: 'var(--shadow-md)',
        position: 'relative',
        opacity: isDeleting || isUninstalling ? 0.5 : 1,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--color-secondary)';
        e.currentTarget.style.boxShadow = 'var(--shadow-glow)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--color-border)';
        e.currentTarget.style.boxShadow = 'var(--shadow-md)';
      }}
    >
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-md)' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-ui)', color: 'var(--color-primary)', fontWeight: 600 }}>
            {server.name}
          </h3>
          <span
            style={{
              display: 'inline-block',
              fontSize: '0.7rem',
              textTransform: 'uppercase',
              backgroundColor: 'var(--color-surface-subtle)',
              color: 'var(--color-secondary)',
              padding: '2px 8px',
              borderRadius: '20px',
              marginTop: 'var(--space-xs)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              fontWeight: 600,
              letterSpacing: '0.5px',
            }}
          >
            {server.category}
          </span>
        </div>

        {/* Global Install Button / Status Badge */}
        <div>
          {!server.is_installed ? (
            <button
              onClick={handleInstall}
              disabled={isInstalling || isDeleting}
              style={{
                padding: 'var(--space-sm) var(--space-lg)',
                borderRadius: 'var(--radius-lg)',
                fontSize: '0.85rem',
                fontWeight: 600,
                border: 'none',
                backgroundColor: 'var(--color-secondary)',
                color: 'var(--color-surface-subtle)',
                cursor: isInstalling ? 'not-allowed' : 'pointer',
                transition: 'all var(--transition-smooth)',
                boxShadow: 'var(--shadow-glow)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = 'var(--shadow-glow-active)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'var(--shadow-glow)';
              }}
            >
              {isInstalling ? 'Installing...' : 'Install'}
            </button>
          ) : (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--color-success)',
                backgroundColor: 'rgba(34, 197, 94, 0.08)',
                border: '1px solid rgba(34, 197, 94, 0.2)',
                padding: '4px 10px',
                borderRadius: '20px',
              }}
            >
              ✓ Installed
            </span>
          )}
        </div>
      </div>

      {/* Connection Info / Code Command */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: 'var(--color-surface-subtle)',
          padding: 'var(--space-md)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          color: 'rgba(255, 255, 255, 0.7)',
          wordBreak: 'break-all',
          gap: 'var(--space-xs)',
        }}
      >
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          <span style={{ color: 'var(--color-primary)', fontWeight: 500 }}>Transport:</span>
          <span style={{ color: 'var(--color-secondary)' }}>{server.type}</span>
        </div>
        {server.command && (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--color-primary)', fontWeight: 500 }}>Endpoint/Command:</span>
            <span style={{ whiteSpace: 'pre-wrap', marginTop: '2px', color: 'var(--color-secondary)', fontSize: '0.75rem' }}>
              {Array.isArray(server.command) ? server.command.join(' ') : server.command}
            </span>
          </div>
        )}
      </div>

      {/* Workspace Enablement List (Only if installed) */}
      {server.is_installed && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-sm)',
            borderTop: '1px solid var(--color-border)',
            paddingTop: 'var(--space-md)',
            marginTop: 'var(--space-xs)',
            textAlign: 'left',
          }}
        >
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Enable in Workspaces
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)', maxHeight: '150px', overflowY: 'auto', paddingRight: '4px' }}>
            {workspaces.length === 0 ? (
              <span style={{ fontSize: '0.8rem', color: 'var(--color-secondary)', fontStyle: 'italic' }}>
                No workspaces available.
              </span>
            ) : (
              workspaces.map((w) => {
                const isEnabled = w.enabled_tools?.includes(server.server_id) || w.enabled_tools?.includes(server.name) || false;
                const isTogglingW = togglingWorkspaceId === w.workspace_id;
                return (
                  <label
                    key={w.workspace_id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '6px var(--space-md)',
                      backgroundColor: isEnabled ? 'rgba(56, 189, 248, 0.04)' : 'rgba(255,255,255,0.01)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.8rem',
                      cursor: isTogglingW ? 'not-allowed' : 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', overflow: 'hidden' }}>
                      <input
                        type="checkbox"
                        checked={isEnabled}
                        disabled={isTogglingW}
                        onChange={(e) => handleToggleWorkspace(w, e.target.checked)}
                        style={{ accentColor: 'var(--color-secondary)', cursor: 'pointer' }}
                      />
                      <span style={{ fontWeight: 500, color: isEnabled ? 'var(--color-primary)' : 'var(--color-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {getWorkspaceName(w.local_path)}
                      </span>
                    </div>
                    {isTogglingW && <span style={{ fontSize: '0.7rem', color: 'var(--color-secondary)' }}>Updating...</span>}
                  </label>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Status Indicators & Control Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-md)', marginTop: 'var(--space-xs)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          <span
            className={server.is_installed && server.status === 'active' ? 'pulse-success-glow' : undefined}
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: getStatusColor(),
              boxShadow: `0 0 8px ${getStatusColor()}`,
              display: 'inline-block',
            }}
          />
          <span style={{ color: 'var(--color-primary)', textTransform: 'capitalize', fontWeight: 500 }}>
            {server.is_installed ? server.status : 'Not Installed'}
          </span>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          {server.is_installed && (
            <button
              onClick={handleUninstall}
              disabled={isUninstalling}
              style={{
                color: 'var(--color-error)',
                fontSize: '0.85rem',
                fontWeight: 500,
                cursor: 'pointer',
                border: 'none',
                background: 'none',
                opacity: 0.8,
                transition: 'opacity var(--transition-fast)',
              }}
              onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
              onMouseLeave={(e) => e.currentTarget.style.opacity = '0.8'}
            >
              {isUninstalling ? 'Uninstalling...' : 'Uninstall'}
            </button>
          )}

          {server.name !== 'CalculiX Simulation' && server.name !== 'OpenSCAD Geometry' && (
            <button
              onClick={handleDelete}
              disabled={isDeleting || isInstalling || isUninstalling}
              style={{
                color: 'rgba(255, 255, 255, 0.4)',
                fontSize: '0.85rem',
                fontWeight: 500,
                cursor: 'pointer',
                border: 'none',
                background: 'none',
                transition: 'color var(--transition-fast)',
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = '#ef4444'}
              onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255, 255, 255, 0.4)'}
            >
              Remove
            </button>
          )}
        </div>
      </div>

      {/* Error block if any */}
      {server.error_message && (
        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid var(--color-error)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-md)',
            fontSize: '0.8rem',
            color: 'var(--color-error)',
            wordBreak: 'break-word',
            textAlign: 'left',
          }}
        >
          <strong>Connection Error:</strong> {server.error_message}
        </div>
      )}

      {/* Discovered Tools Dropdown */}
      {server.is_installed && tools.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-md)', marginTop: 'var(--space-xs)' }}>
          <button
            onClick={() => setShowTools(!showTools)}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              width: '100%',
              fontSize: '0.85rem',
              color: 'var(--color-secondary)',
              cursor: 'pointer',
              textAlign: 'left',
              fontWeight: 600,
              border: 'none',
              background: 'none',
            }}
          >
            <span>Exposed Tools ({tools.length})</span>
            <span>{showTools ? '▲' : '▼'}</span>
          </button>

          {showTools && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)', marginTop: 'var(--space-md)' }}>
              {tools.map((tool) => (
                <div
                  key={tool.tool_id}
                  style={{
                    backgroundColor: 'var(--color-surface-subtle)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-lg)',
                    padding: 'var(--space-md)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-xs)',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--color-primary)', fontWeight: 600 }}>
                      {tool.name}
                    </span>
                    
                    {/* Tool Toggle Checkbox */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.6)', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={tool.is_enabled}
                        onChange={(e) => onToggleTool(tool.tool_id, e.target.checked)}
                        style={{ cursor: 'pointer', accentColor: 'var(--color-secondary)' }}
                      />
                      {tool.is_enabled ? 'Enabled' : 'Disabled'}
                    </label>
                  </div>
                  {tool.description && (
                    <p style={{ fontSize: '0.8rem', color: 'var(--color-secondary)', fontStyle: 'italic', lineHeight: 1.4 }}>
                      {tool.description}
                    </p>
                  )}
                  {tool.input_schema && Object.keys(tool.input_schema).length > 0 && (
                    <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.4)', marginTop: '4px' }}>
                      <span style={{ fontWeight: 600 }}>Schema keys:</span>{' '}
                      {Object.keys(tool.input_schema.properties || {}).join(', ') || 'none'}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

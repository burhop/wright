import { useEffect, useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useLogger from '../../hooks/useLogger';
import { AgentChatIcon, ToolRegistryIcon, FileVaultIcon } from '../common/Icons';
import { workspaceService, type WorkspaceInfo } from '../../services/workspace-service';
import { useChat } from '../../store/sessions';

export function DashboardPage() {
  const logger = useLogger('DashboardPage');
  const navigate = useNavigate();
  const { selectSession } = useChat();

  const [recentWorkspaces, setRecentWorkspaces] = useState<WorkspaceInfo[]>([]);
  const [allWorkspaces, setAllWorkspaces] = useState<WorkspaceInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logger.info('Dashboard Page loaded');
    const fetchWorkspaces = async () => {
      try {
        const recent = await workspaceService.getRecentWorkspaces();
        const all = await workspaceService.getAllWorkspaces();
        setRecentWorkspaces(recent);
        setAllWorkspaces(all);
      } catch (err) {
        logger.error('Failed to load workspaces', { err });
      }
    };
    fetchWorkspaces();
  }, [logger]);

  // Handle clicking outside of dropdown to close it
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getWorkspaceName = (path: string) => {
    const parts = path.split('/');
    return parts[parts.length - 1] || path;
  };

  const formatTimeAgo = (ts: number) => {
    const diffSec = Math.floor(Date.now() / 1000) - ts;
    if (diffSec < 60) return 'just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDays = Math.floor(diffHr / 24);
    return `${diffDays}d ago`;
  };

  const handleSelectWorkspace = async (w: WorkspaceInfo) => {
    try {
      await workspaceService.activateWorkspace(w.session_id);
      selectSession(w.session_id);
      navigate('/agent-chat');
    } catch (err) {
      console.error('Failed to switch workspace', err);
    }
  };

  const filteredWorkspaces = allWorkspaces.filter((w) => {
    const name = getWorkspaceName(w.local_path).toLowerCase();
    const path = w.local_path.toLowerCase();
    const query = searchQuery.toLowerCase();
    return name.includes(query) || path.includes(query);
  });

  return (
    <div
      data-testid="page-dashboard"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-2xl)',
        maxWidth: '1200px',
        margin: '0 auto',
        padding: 'var(--space-2xl) var(--space-xl)',
      }}
      className="animate-fade-in-up"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
        <h1 style={{ fontFamily: 'var(--font-ui)', fontSize: '2.8rem', fontWeight: 700, color: 'var(--color-primary)', textAlign: 'left', letterSpacing: '-0.75px' }}>
          Welcome to Wright
        </h1>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: '1.2rem', color: 'var(--color-secondary)', textAlign: 'left', maxWidth: '800px', lineHeight: 1.7 }}>
          A local-first multi-agent mechanical engineering appliance. Wright runs locally to orchestrate, analyze, and document your mechanical designs under complete privacy.
        </p>
      </div>

      {/* Workspace Switcher Panel */}
      <div
        className="glow-card"
        style={{
          padding: 'var(--space-2xl)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-lg)',
          textAlign: 'left',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          backgroundColor: 'var(--color-surface)',
          boxShadow: 'var(--shadow-lg)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.5rem', fontWeight: 600, color: 'var(--color-primary)' }}>
              Engineering Workspaces
            </h2>
            <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.9rem', color: 'var(--color-secondary)', marginTop: '2px' }}>
              Select a workspace repository to activate its tools and load files.
            </p>
          </div>

          {/* Search Dropdown Selector (VS Code Style) */}
          <div ref={dropdownRef} style={{ position: 'relative', width: '320px' }}>
            <div
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: 'var(--space-md) var(--space-lg)',
                backgroundColor: 'var(--color-surface-subtle)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                color: 'var(--color-primary)',
                fontSize: '0.9rem',
                cursor: 'pointer',
                userSelect: 'none',
              }}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                Open Workspace...
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-secondary)' }}>▼</span>
            </div>

            {isDropdownOpen && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  width: '100%',
                  marginTop: 'var(--space-xs)',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-lg)',
                  boxShadow: 'var(--shadow-xl)',
                  zIndex: 100,
                  display: 'flex',
                  flexDirection: 'column',
                  maxHeight: '300px',
                  overflow: 'hidden',
                }}
              >
                <div style={{ padding: 'var(--space-sm)', borderBottom: '1px solid var(--color-border)' }}>
                  <input
                    type="text"
                    placeholder="Search workspaces by folder or path..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    autoFocus
                    style={{
                      width: '100%',
                      padding: 'var(--space-md)',
                      backgroundColor: 'var(--color-surface-subtle)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--color-primary)',
                      fontSize: '0.85rem',
                      outline: 'none',
                    }}
                  />
                </div>
                <div style={{ overflowY: 'auto', flex: 1 }}>
                  {filteredWorkspaces.length === 0 ? (
                    <div style={{ padding: 'var(--space-lg)', fontSize: '0.85rem', color: 'var(--color-secondary)', textAlign: 'center' }}>
                      No workspaces found
                    </div>
                  ) : (
                    filteredWorkspaces.map((w) => (
                      <div
                        key={w.workspace_id}
                        onClick={() => {
                          handleSelectWorkspace(w);
                          setIsDropdownOpen(false);
                        }}
                        style={{
                          padding: 'var(--space-md) var(--space-lg)',
                          cursor: 'pointer',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '2px',
                          borderBottom: '1px solid rgba(255, 255, 255, 0.02)',
                        }}
                        className="dropdown-item"
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(56, 189, 248, 0.08)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--color-primary)' }}>
                          {getWorkspaceName(w.local_path)}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {w.local_path}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Recent Workspaces List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)', marginTop: 'var(--space-xs)' }}>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 600, color: 'var(--color-secondary)', letterSpacing: '1px' }}>
            Recently Opened Workspaces
          </span>

          {recentWorkspaces.length === 0 ? (
            <div style={{ padding: 'var(--space-xl)', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-lg)', textAlign: 'center', border: '1px dashed var(--color-border)' }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--color-secondary)' }}>
                No engineering workspaces opened yet. Try launching the Hermes Agent to start a session.
              </span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
              {recentWorkspaces.map((w) => (
                <div
                  key={w.workspace_id}
                  onClick={() => handleSelectWorkspace(w)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: 'var(--space-lg) var(--space-xl)',
                    backgroundColor: 'var(--color-surface-subtle)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-lg)',
                    cursor: 'pointer',
                    transition: 'all var(--transition-smooth)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--color-secondary)';
                    e.currentTarget.style.boxShadow = 'var(--shadow-glow)';
                    e.currentTarget.style.transform = 'translateX(2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--color-border)';
                    e.currentTarget.style.boxShadow = 'none';
                    e.currentTarget.style.transform = 'translateX(0)';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                    <div style={{ color: 'var(--color-secondary)' }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                      </svg>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', textAlign: 'left' }}>
                      <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-primary)' }}>
                        {getWorkspaceName(w.local_path)}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--color-secondary)' }}>
                        {w.local_path}
                      </span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-secondary)' }}>
                      {formatTimeAgo(w.updated_at)}
                    </span>
                    <span style={{ color: 'var(--color-secondary)', fontSize: '0.9rem' }}>→</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-xl)',
        }}
      >
        <Link
          to="/agent-chat"
          className="glow-card"
          style={{
            padding: 'var(--space-2xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
            textAlign: 'left',
            cursor: 'pointer',
          }}
        >
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'rgba(56, 189, 248, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-secondary)',
            boxShadow: 'var(--shadow-glow)',
          }}>
            <AgentChatIcon size={24} />
          </div>
          <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.4rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            Hermes Agent
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'var(--color-secondary)', lineHeight: 1.5 }}>
            Interact with the local engineering agent using natural language. Execute workspace scripts, generate calculations, and inspect designs transparently.
          </p>
        </Link>

        <Link
          to="/tool-registry"
          className="glow-card"
          style={{
            padding: 'var(--space-2xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
            textAlign: 'left',
            cursor: 'pointer',
          }}
        >
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'rgba(56, 189, 248, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-secondary)',
            boxShadow: 'var(--shadow-glow)',
          }}>
            <ToolRegistryIcon size={24} />
          </div>
          <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.4rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            Tool Registry
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'var(--color-secondary)', lineHeight: 1.5 }}>
            Explore available system tools, solvers, and analytical adapters. Wright exposes CAD parsers, finite element solvers, and data formatters to agents.
          </p>
        </Link>

        <Link
          to="/file-vault"
          className="glow-card"
          style={{
            padding: 'var(--space-2xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
            textAlign: 'left',
            cursor: 'pointer',
          }}
        >
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'rgba(56, 189, 248, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-secondary)',
            boxShadow: 'var(--shadow-glow)',
          }}>
            <FileVaultIcon size={24} />
          </div>
          <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.4rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            File Vault
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'var(--color-secondary)', lineHeight: 1.5 }}>
            Manage engineering artifacts, design specs, and simulation outputs. The vault operates entirely offline, keeping your raw files secure in your workspace.
          </p>
        </Link>
      </div>
    </div>
  );
}

export default DashboardPage;

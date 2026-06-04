import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { workspaceService, type WorkspaceInfo } from '../../services/workspace-service';
import WorkspacePanel from '../chat/WorkspacePanel';
import useLogger from '../../hooks/useLogger';

export function WorkspacePage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();
  const logger = useLogger('WorkspacePage');

  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!workspaceId) {
      navigate('/');
      return;
    }

    const loadWorkspace = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const ws = await workspaceService.getWorkspace(workspaceId);
        // Activate the workspace session to ensure it is registered on the backend
        await workspaceService.activateWorkspace(ws.session_id);
        // Re-load the workspace in case activation updated the session_id in the DB
        const activeWs = await workspaceService.getWorkspace(workspaceId);
        setWorkspace(activeWs);
        logger.info('Workspace loaded and activated', { workspaceId, path: activeWs.local_path });
      } catch (err) {
        logger.error('Failed to load workspace', { workspaceId, err });
        setError('Workspace not found');
      } finally {
        setIsLoading(false);
      }
    };

    loadWorkspace();
  }, [workspaceId, navigate, logger]);

  if (isLoading) {
    return (
      <div
        data-testid="page-workspace-loading"
        style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-secondary)',
          fontSize: '1rem',
          gap: 'var(--space-md)',
        }}
      >
        <div className="thinking-dot" />
        <div className="thinking-dot" />
        <div className="thinking-dot" />
      </div>
    );
  }

  if (error || !workspace) {
    return (
      <div
        data-testid="page-workspace-error"
        style={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 'var(--space-lg)',
          color: 'var(--color-secondary)',
        }}
      >
        <div style={{ fontSize: '3rem' }}>🔍</div>
        <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.4rem', fontWeight: 600, color: 'var(--color-primary)' }}>
          Workspace Not Found
        </h2>
        <p style={{ fontSize: '0.95rem', maxWidth: '400px', textAlign: 'center', lineHeight: 1.6 }}>
          The workspace you&apos;re looking for doesn&apos;t exist or may have been removed.
        </p>
        <button
          onClick={() => navigate('/')}
          style={{
            padding: 'var(--space-md) var(--space-xl)',
            backgroundColor: 'var(--color-secondary)',
            color: 'var(--color-surface-subtle)',
            fontWeight: 600,
            fontSize: '0.9rem',
            borderRadius: 'var(--radius-lg)',
            border: 'none',
            cursor: 'pointer',
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
          ← Back to Dashboard
        </button>
      </div>
    );
  }

  const handleSessionChange = (newSessionId: string) => {
    setWorkspace((prev) => (prev ? { ...prev, session_id: newSessionId } : null));
  };

  return (
    <div data-testid="chat-layout" style={{ height: '100%', width: '100%', overflow: 'hidden' }}>
      <div data-testid="page-workspace" style={{ height: '100%' }}>
        <WorkspacePanel
          workspaceId={workspace.workspace_id}
          sessionId={workspace.session_id}
          onSessionChange={handleSessionChange}
        />
      </div>
    </div>
  );
}

export default WorkspacePage;

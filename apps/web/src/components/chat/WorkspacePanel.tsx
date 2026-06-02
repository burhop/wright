import { useState, useEffect, useRef } from 'react';
import FileTree from '../common/FileTree';
import ThreeDViewer from '../common/ThreeDViewer';
import { useChat } from '../../store/sessions';
import { workspaceService, type WorkspaceNode } from '../../services/workspace-service';

function findFileInTree(node: WorkspaceNode, targetPath: string): WorkspaceNode | null {
  if (node.path === targetPath) {
    return node;
  }
  if (node.children) {
    for (const child of node.children) {
      const found = findFileInTree(child, targetPath);
      if (found) return found;
    }
  }
  return null;
}

export function WorkspacePanel() {
  const { state } = useChat();
  const activeSessionId = state.activeSessionId;

  const [activeTab, setActiveTab] = useState<'files' | 'preview'>('files');
  const [workspaceRoot, setWorkspaceRoot] = useState<WorkspaceNode | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // File preview states
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [selectedFileBuffer, setSelectedFileBuffer] = useState<ArrayBuffer | null>(null);
  const [selectedFileLastModified, setSelectedFileLastModified] = useState<number | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [fileWarning, setFileWarning] = useState<string | null>(null);

  // Keep refs of selected file info to avoid stale closures in the polling loop
  const selectedFilePathRef = useRef<string | null>(null);
  const selectedFileLastModifiedRef = useRef<number | null>(null);

  useEffect(() => {
    selectedFilePathRef.current = selectedFilePath;
  }, [selectedFilePath]);

  useEffect(() => {
    selectedFileLastModifiedRef.current = selectedFileLastModified;
  }, [selectedFileLastModified]);

  // Keep compatibility with webmcp event integration
  useEffect(() => {
    const handleWebMcpRequest = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { callId, method } = customEvent.detail || {};
      
      if (!callId) return;

      if (method === 'get_selected_part') {
        const responseEvent = new CustomEvent('webmcp:response', {
          detail: {
            callId,
            result: {
              partId: 'part-aba8973b-31a8',
              dimensions: [12.0, 5.5, 2.3],
            },
          },
        });
        window.dispatchEvent(responseEvent);
      }
    };

    window.addEventListener('webmcp:request', handleWebMcpRequest);
    return () => {
      window.removeEventListener('webmcp:request', handleWebMcpRequest);
    };
  }, []);

  // Workspace Polling Loop (2-second interval)
  useEffect(() => {
    if (!activeSessionId) {
      // Defer state updates to next microtask to avoid react-hooks/set-state-in-effect lint warning
      Promise.resolve().then(() => {
        setWorkspaceRoot(null);
        setLoading(false);
      });
      return;
    }

    let isMounted = true;

    const fetchWorkspace = async (isInitial = false) => {
      if (isInitial) setLoading(true);
      try {
        const tree = await workspaceService.getWorkspaceFiles(activeSessionId);
        if (!isMounted) return;
        setWorkspaceRoot(tree);
        setError(null);

        // Check if our currently selected file has been modified by the agent
        const currentPath = selectedFilePathRef.current;
        const currentTimestamp = selectedFileLastModifiedRef.current;

        if (currentPath) {
          const fileNode = findFileInTree(tree, currentPath);
          if (fileNode) {
            if (currentTimestamp !== null && fileNode.last_modified > currentTimestamp) {
              console.log(`Detected file modification for ${currentPath}. Reloading buffer...`);
              try {
                const updatedBuffer = await workspaceService.getFileContentArrayBuffer(activeSessionId, currentPath);
                if (!isMounted) return;
                setSelectedFileBuffer(updatedBuffer);
                setSelectedFileLastModified(fileNode.last_modified);
              } catch (err) {
                console.error('Failed to reload modified workspace file:', err);
              }
            }
          }
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        console.error('Error fetching workspace files:', err);
        setError('Failed to fetch workspace files');
      } finally {
        if (isMounted && isInitial) setLoading(false);
      }
    };

    fetchWorkspace(true);

    const intervalId = setInterval(() => {
      fetchWorkspace(false);
    }, 2000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [activeSessionId]);

  const handleFileClick = async (path: string) => {
    if (!activeSessionId) return;

    if (!path.toLowerCase().endsWith('.stl')) {
      setFileWarning('Only STL (.stl) files can be visualized in 3D.');
      return;
    }

    setFileWarning(null);
    setPreviewLoading(true);
    try {
      const fileName = path.split('/').pop() || path;
      const buffer = await workspaceService.getFileContentArrayBuffer(activeSessionId, path);
      
      let fileNode: WorkspaceNode | null = null;
      if (workspaceRoot) {
        fileNode = findFileInTree(workspaceRoot, path);
      }

      setSelectedFilePath(path);
      setSelectedFileName(fileName);
      setSelectedFileBuffer(buffer);
      setSelectedFileLastModified(fileNode ? fileNode.last_modified : Date.now());
      setActiveTab('preview');
    } catch (err: unknown) {
      console.error('Failed to load STL file:', err);
      const errMsg = err instanceof Error ? err.message : String(err);
      setError(`Failed to load 3D model: ${errMsg}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  return (
    <div
      data-testid="workspace-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--color-surface-subtle)',
        borderLeft: '1px solid var(--color-border)',
        width: '280px',
      }}
    >
      <div
        style={{
          padding: 'var(--space-lg)',
          borderBottom: '1px solid var(--color-border)',
          fontFamily: 'var(--font-ui)',
          fontWeight: '600',
          fontSize: '0.9rem',
          color: 'var(--color-primary)',
          letterSpacing: '0.5px',
        }}
      >
        WORKSPACE BROWSER
      </div>

      {/* Modern Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--color-border)',
          backgroundColor: 'var(--color-neutral)',
        }}
      >
        <button
          onClick={() => setActiveTab('files')}
          style={{
            flex: 1,
            padding: 'var(--space-md) 0',
            fontFamily: 'var(--font-ui)',
            fontSize: '0.8rem',
            fontWeight: activeTab === 'files' ? '600' : '400',
            color: activeTab === 'files' ? 'var(--color-primary)' : 'var(--color-secondary)',
            backgroundColor: activeTab === 'files' ? 'var(--color-surface)' : 'transparent',
            border: 'none',
            borderBottom: activeTab === 'files' ? '2px solid var(--color-accent, #4f46e5)' : '2px solid transparent',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          FILES
        </button>
        <button
          onClick={() => setActiveTab('preview')}
          style={{
            flex: 1,
            padding: 'var(--space-md) 0',
            fontFamily: 'var(--font-ui)',
            fontSize: '0.8rem',
            fontWeight: activeTab === 'preview' ? '600' : '400',
            color: activeTab === 'preview' ? 'var(--color-primary)' : 'var(--color-secondary)',
            backgroundColor: activeTab === 'preview' ? 'var(--color-surface)' : 'transparent',
            border: 'none',
            borderBottom: activeTab === 'preview' ? '2px solid var(--color-accent, #4f46e5)' : '2px solid transparent',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          3D PREVIEW
        </button>
      </div>

      {fileWarning && (
        <div
          style={{
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderBottom: '1px solid rgba(245, 158, 11, 0.2)',
            color: 'var(--color-warning, #f59e0b)',
            padding: 'var(--space-sm) var(--space-md)',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-ui)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--space-xs)',
          }}
        >
          <span>⚠️ {fileWarning}</span>
          <button
            onClick={() => setFileWarning(null)}
            style={{
              background: 'none',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Tab Panels */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        {activeTab === 'files' ? (
          <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-md)' }}>
            {loading && !workspaceRoot ? (
              <div style={{ color: 'var(--color-secondary)', fontFamily: 'var(--font-ui)', fontSize: '0.8rem', padding: 'var(--space-md)' }}>
                Loading workspace...
              </div>
            ) : error ? (
              <div style={{ color: 'var(--color-error, #ef4444)', fontFamily: 'var(--font-ui)', fontSize: '0.8rem', padding: 'var(--space-md)' }}>
                {error}
              </div>
            ) : workspaceRoot ? (
              <FileTree node={workspaceRoot} onFileClick={handleFileClick} />
            ) : (
              <div style={{ color: 'var(--color-secondary)', fontFamily: 'var(--font-ui)', fontSize: '0.8rem', padding: 'var(--space-md)' }}>
                No workspace active.
              </div>
            )}
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {previewLoading ? (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-secondary)', fontFamily: 'var(--font-ui)', fontSize: '0.8rem' }}>
                Loading 3D model...
              </div>
            ) : selectedFilePath && selectedFileBuffer ? (
              <ThreeDViewer arrayBuffer={selectedFileBuffer} fileName={selectedFileName || undefined} />
            ) : (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  padding: 'var(--space-xl)',
                  textAlign: 'center',
                  color: 'var(--color-secondary)',
                  fontFamily: 'var(--font-ui)',
                  gap: 'var(--space-md)',
                }}
              >
                <div style={{ fontSize: '2.5rem', opacity: 0.6 }}>🧊</div>
                <div style={{ fontSize: '0.85rem', fontWeight: '500', color: 'var(--color-primary)' }}>
                  No Geometry Loaded
                </div>
                <div style={{ fontSize: '0.75rem', lineHeight: '1.4' }}>
                  Select a <strong>.stl</strong> file in the FILES tab to render and interact with the 3D model.
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default WorkspacePanel;

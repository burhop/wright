import { useState } from 'react';
import SessionsSidebar from './SessionsSidebar';
import ChatTranscript from './ChatTranscript';
import MessageComposer from './MessageComposer';
import WorkspacePanel from './WorkspacePanel';
import { useChat } from '../../store/sessions';
import useHealthStatus from '../../hooks/useHealthStatus';

export function ChatLayout() {
  const { state, createSession, selectSession, deleteSession, sendMessage } = useChat();
  const [showWorkspace, setShowWorkspace] = useState(true);
  const statuses = useHealthStatus();

  const activeSession =
    state.sessions.find((s) => s.sessionId === state.activeSessionId) || null;

  const agentStatus = statuses.find((s) => s.serviceId === 'hermes-agent')?.state;
  const isAgentDisconnected = agentStatus === 'disconnected';

  return (
    <div
      data-testid="chat-layout"
      style={{
        display: 'grid',
        gridTemplateColumns: `260px 1fr ${showWorkspace ? '280px' : '0px'}`,
        height: '100%',
        backgroundColor: 'var(--color-neutral)',
        overflow: 'hidden',
        transition: 'grid-template-columns 0.3s ease',
      }}
    >
      <SessionsSidebar
        sessions={state.sessions}
        activeId={state.activeSessionId}
        onSelect={selectSession}
        onCreate={createSession}
        onDelete={deleteSession}
      />

      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        {isAgentDisconnected && (
          <div
            data-testid="health-banner-hermes"
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderBottom: '1px solid rgba(239, 68, 68, 0.2)',
              color: '#ef4444',
              padding: 'var(--space-md) var(--space-lg)',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 'var(--space-md)',
              fontFamily: 'var(--font-ui)',
            }}
          >
              <span style={{ fontWeight: 'bold' }}>⚠️</span>
              <span>Hermes agent is not available. Check that the wright profile WebUI is running.</span>
          </div>
        )}
        <div
          style={{
            height: '40px',
            backgroundColor: 'var(--color-neutral)',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            padding: '0 var(--space-md)',
          }}
        >
          <button
            data-testid="toggle-workspace-btn"
            onClick={() => setShowWorkspace(!showWorkspace)}
            style={{
              padding: '4px 8px',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.8rem',
              color: 'var(--color-secondary)',
              fontFamily: 'var(--font-ui)',
            }}
          >
            {showWorkspace ? 'Hide Workspace' : 'Show Workspace'}
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <ChatTranscript
            session={activeSession}
            isStreaming={state.isStreaming}
            streamedText={state.streamedText}
            activeTool={state.activeTool}
          />
        </div>

        {activeSession && (
          <div style={{ padding: 'var(--space-md) var(--space-lg)', borderTop: '1px solid var(--color-border)', backgroundColor: 'var(--color-neutral)' }}>
            <MessageComposer onSend={sendMessage} disabled={state.isStreaming} />
          </div>
        )}
      </div>

      <div style={{ overflow: 'hidden', height: '100%', display: showWorkspace ? 'block' : 'none' }}>
        <WorkspacePanel />
      </div>
    </div>
  );
}

export default ChatLayout;

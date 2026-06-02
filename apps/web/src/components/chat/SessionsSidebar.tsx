import type { ChatSessionCompact } from '../../store/types';

interface SessionsSidebarProps {
  sessions: ChatSessionCompact[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
}

export function SessionsSidebar({
  sessions,
  activeId,
  onSelect,
  onCreate,
  onDelete,
}: SessionsSidebarProps) {
  return (
    <div
      data-testid="sessions-sidebar"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--color-surface-subtle)',
        borderRight: '1px solid var(--color-border)',
        width: '260px',
      }}
    >
      <div
        style={{
          padding: 'var(--space-lg)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span
          style={{
            fontWeight: '600',
            fontSize: '0.9rem',
            color: 'var(--color-primary)',
            fontFamily: 'var(--font-ui)',
            letterSpacing: '0.5px',
          }}
        >
          SESSIONS
        </span>
        <button
          onClick={onCreate}
          data-testid="create-session-btn"
          style={{
            padding: '4px 10px',
            backgroundColor: 'var(--color-secondary)',
            color: 'var(--color-neutral)',
            fontSize: '0.75rem',
            fontWeight: 'bold',
            borderRadius: 'var(--radius-sm)',
            fontFamily: 'var(--font-ui)',
            transition: 'background-color 0.2s ease',
          }}
        >
          NEW
        </button>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 'var(--space-md) var(--space-sm)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-xs)',
        }}
      >
        {sessions.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              color: 'var(--color-secondary)',
              fontSize: '0.85rem',
              padding: 'var(--space-lg) 0',
              fontFamily: 'var(--font-body)',
            }}
          >
            No sessions.
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.sessionId === activeId;
            return (
              <div
                key={session.sessionId}
                data-testid={`session-${session.sessionId}`}
                onClick={() => onSelect(session.sessionId)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: 'var(--space-md) var(--space-lg)',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isActive ? 'var(--color-surface)' : 'transparent',
                  cursor: 'pointer',
                  borderLeft: isActive ? '3px solid var(--color-secondary)' : '3px solid transparent',
                  transition: 'all 0.2s ease',
                  userSelect: 'none',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.03)';
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <span
                  style={{
                    fontSize: '0.9rem',
                    color: isActive ? 'var(--color-primary)' : 'var(--color-secondary)',
                    fontWeight: isActive ? '600' : '400',
                    fontFamily: 'var(--font-ui)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    maxWidth: '150px',
                  }}
                >
                  {session.title}
                </span>

                <button
                  data-testid={`delete-session-${session.sessionId}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(session.sessionId);
                  }}
                  style={{
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: 'var(--color-error)',
                    opacity: isActive ? 0.7 : 0.2,
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    transition: 'opacity 0.2s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                  onMouseLeave={(e) => (e.currentTarget.style.opacity = isActive ? '0.7' : '0.2')}
                >
                  ✕
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default SessionsSidebar;

import type { ChatMessage } from '../../store/types';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  
  return (
    <div
      data-testid={`message-${message.id}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        gap: 'var(--space-xs)',
        width: '100%',
      }}
    >
      <div
        style={{
          maxWidth: '80%',
          padding: 'var(--space-md) var(--space-lg)',
          borderRadius: 'var(--radius-lg)',
          backgroundColor: isUser ? 'var(--color-surface)' : 'var(--color-surface-subtle)',
          border: '1px solid var(--color-border)',
          color: 'var(--color-primary)',
          textAlign: 'left',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          transition: 'all 0.2s ease',
        }}
      >
        <div style={{ fontFamily: 'var(--font-body)', fontSize: '1rem', whiteSpace: 'pre-wrap' }}>
          {message.content}
        </div>
        
        <div
          style={{
            marginTop: 'var(--space-xs)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-md)',
            fontSize: '0.75rem',
            color: 'var(--color-secondary)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
          {message.traceId && (
            <span style={{ opacity: 0.7 }}>ID: {message.traceId.slice(0, 8)}</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;

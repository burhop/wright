import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import type { ChatMessage, ChatSession } from '../../store/types';

interface ChatTranscriptProps {
  session: ChatSession | null;
  isStreaming?: boolean;
  streamedText?: string;
  activeTool?: { name: string; preview: string } | null;
}

export function ChatTranscript({
  session,
  isStreaming = false,
  streamedText = '',
  activeTool = null,
}: ChatTranscriptProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    const container = containerRef.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [session?.messages?.length, streamedText, activeTool]);

  if (!session) {
    return (
      <div
        data-testid="chat-transcript"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: 'var(--color-secondary)',
          fontFamily: 'var(--font-ui)',
        }}
      >
        <span>Select or create a session to start chatting.</span>
      </div>
    );
  }

  const mockStreamingMessage: ChatMessage | null =
    isStreaming && streamedText.trim()
      ? {
          id: 'streaming-msg',
          role: 'assistant',
          content: streamedText,
          timestamp: Date.now(),
          traceId: null,
        }
      : null;

  return (
    <div
      ref={containerRef}
      data-testid="chat-transcript"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-lg)',
        padding: 'var(--space-lg)',
        height: '100%',
        overflowY: 'auto',
        scrollBehavior: 'smooth',
      }}
    >
      {session.messages.length === 0 && !isStreaming && (
        <div
          style={{
            margin: 'auto',
            textAlign: 'center',
            color: 'var(--color-secondary)',
            fontFamily: 'var(--font-body)',
          }}
        >
          <p style={{ fontSize: '1.1rem' }}>No messages yet.</p>
          <p style={{ fontSize: '0.9rem', marginTop: '4px' }}>
            Send a message to start conversing with the Hermes Agent.
          </p>
        </div>
      )}

      {session.messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {activeTool && (
        <div
          data-testid="active-tool"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-md)',
            alignSelf: 'flex-start',
            padding: 'var(--space-md)',
            backgroundColor: 'var(--color-surface-subtle)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-secondary)',
            fontFamily: 'var(--font-ui)',
            fontSize: '0.85rem',
            width: '100%',
            maxWidth: '80%',
          }}
        >
          <span style={{ display: 'inline-block' }}>⚙</span>
          <div>
            <span style={{ fontWeight: '600', color: 'var(--color-primary)' }}>
              Tool: {activeTool.name}
            </span>
            <div style={{ fontSize: '0.75rem', opacity: 0.8, marginTop: '2px' }}>
              {activeTool.preview}
            </div>
          </div>
        </div>
      )}

      {mockStreamingMessage && <MessageBubble message={mockStreamingMessage} />}
      
      {isStreaming && !streamedText.trim() && (
        <div
          data-testid="thinking-indicator"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-start',
            gap: 'var(--space-xs)',
            width: '100%',
          }}
        >
          <div
            style={{
              maxWidth: '80%',
              padding: 'var(--space-md) var(--space-lg)',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', height: '1.5rem' }}>
              <span className="thinking-dot"></span>
              <span className="thinking-dot"></span>
              <span className="thinking-dot"></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatTranscript;

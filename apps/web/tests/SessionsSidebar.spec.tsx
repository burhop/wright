import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SessionsSidebar from '../src/components/chat/SessionsSidebar';
import type { ChatSessionCompact } from '../src/store/types';

describe('SessionsSidebar', () => {
  it('lists sessions and successfully renders 50 sessions', () => {
    const handleSelect = vi.fn();
    const handleCreate = vi.fn();
    const handleDelete = vi.fn();

    const mockSessions: ChatSessionCompact[] = Array.from({ length: 50 }).map((_, i) => ({
      sessionId: `sess-${i}`,
      title: `Engineering Session ${i + 1}`,
      createdAt: Date.now() - i * 1000,
      updatedAt: Date.now() - i * 1000,
    }));

    render(
      <SessionsSidebar
        sessions={mockSessions}
        activeId="sess-0"
        onSelect={handleSelect}
        onCreate={handleCreate}
        onDelete={handleDelete}
      />
    );

    expect(screen.getByTestId('sessions-sidebar')).toBeInTheDocument();
    
    const activeSession = screen.getByTestId('session-sess-0');
    expect(activeSession).toBeInTheDocument();

    for (let i = 0; i < 50; i++) {
      expect(screen.getByTestId(`session-sess-${i}`)).toBeInTheDocument();
    }
  });
});

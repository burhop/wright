import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import ChatLayout from '../src/components/chat/ChatLayout';
import { ChatProvider } from '../src/store/sessions';

describe('ChatLayout', () => {
  it('renders three-panel layout', () => {
    render(
      <MemoryRouter>
        <ChatProvider>
          <ChatLayout />
        </ChatProvider>
      </MemoryRouter>
    );

    expect(screen.getByTestId('chat-layout')).toBeInTheDocument();
    expect(screen.getByTestId('sessions-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('chat-transcript')).toBeInTheDocument();
    expect(screen.getByTestId('workspace-panel')).toBeInTheDocument();
  });
});

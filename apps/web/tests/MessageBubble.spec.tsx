import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import MessageBubble from '../src/components/chat/MessageBubble';
import type { ChatMessage } from '../src/store/types';

describe('MessageBubble', () => {
  it('renders a plain text user message correctly', () => {
    const userMsg: ChatMessage = {
      id: 'msg1',
      role: 'user',
      content: 'This is a **user** message with raw newlines\nLine 2',
      timestamp: Date.now(),
      traceId: 'tr-1',
    };

    render(<MessageBubble message={userMsg} />);

    // Since it's a user message, we preserve raw text and it should not render markdown as html
    const contentContainer = screen.getByText(/This is a \*\*user\*\* message/);
    expect(contentContainer).toBeInTheDocument();
    
    // It should not be formatted as a strong/bold element
    const boldElem = screen.queryByText('user');
    expect(boldElem).toBeNull();
  });

  it('renders an assistant message as parsed markdown correctly', () => {
    const assistantMsg: ChatMessage = {
      id: 'msg2',
      role: 'assistant',
      content: '# Hello World\nThis is **bold** text and [a link](https://google.com) and a list:\n- Item 1\n- Item 2',
      timestamp: Date.now(),
      traceId: 'tr-2',
    };

    render(<MessageBubble message={assistantMsg} />);

    // Assert headers
    const header = screen.getByRole('heading', { level: 1 });
    expect(header).toHaveTextContent('Hello World');

    // Assert bold text
    const boldText = screen.getByText('bold');
    expect(boldText.tagName).toBe('STRONG');

    // Assert links
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', 'https://google.com');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');

    // Assert lists
    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent('Item 1');
  });

  it('sanitizes dangerous links in markdown to href="#"', () => {
    const dangerousMsg: ChatMessage = {
      id: 'msg3',
      role: 'assistant',
      content: 'Click [here](javascript:alert("XSS")) or [vbscript](vbscript:msgbox("XSS"))',
      timestamp: Date.now(),
      traceId: 'tr-3',
    };

    render(<MessageBubble message={dangerousMsg} />);

    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute('href', '#');
    expect(links[1]).toHaveAttribute('href', '#');
  });

  it('makes URLs and workspace paths clickable and calls onOpenFile', () => {
    const message: ChatMessage = {
      id: 'msg4',
      role: 'assistant',
      content: 'File: /home/burhop/workspace/session-123/designs/bracket.stl and http://google.com and designs/gearbox.stl and `/home/burhop/workspace/session-123/ignore.stl`',
      timestamp: Date.now(),
      traceId: 'tr-4',
    };

    const handleOpenFile = vi.fn();

    render(
      <MessageBubble
        message={message}
        onOpenFile={handleOpenFile}
        activeSessionId="session-123"
        workspacePath="/home/burhop/workspace/session-123"
      />
    );

    // Assert that the http URL is rendered as a normal link
    const link = screen.getByRole('link', { name: 'http://google.com' });
    expect(link).toHaveAttribute('href', 'http://google.com');

    // Assert that absolute path is rendered as a button and is clickable
    const absPathBtn = screen.getByRole('button', { name: '/home/burhop/workspace/session-123/designs/bracket.stl' });
    expect(absPathBtn).toBeInTheDocument();
    
    // Click absolute path button
    fireEvent.click(absPathBtn);
    expect(handleOpenFile).toHaveBeenCalledWith('/designs/bracket.stl');

    // Assert that relative path is rendered as a button and is clickable
    const relPathBtn = screen.getByRole('button', { name: 'designs/gearbox.stl' });
    expect(relPathBtn).toBeInTheDocument();
    
    // Click relative path button
    fireEvent.click(relPathBtn);
    expect(handleOpenFile).toHaveBeenCalledWith('/designs/gearbox.stl');

    // Assert that path inside inline code block is NOT rendered as a button or link
    const codeBtn = screen.queryByRole('button', { name: '/home/burhop/workspace/session-123/ignore.stl' });
    expect(codeBtn).toBeNull();
  });
});

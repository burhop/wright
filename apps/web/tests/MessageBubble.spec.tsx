import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
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
});

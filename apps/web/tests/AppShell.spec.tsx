import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import AppShell from '../src/components/layout/AppShell';

describe('AppShell', () => {
  it('renders header, sidebar, and children content', () => {
    render(
      <MemoryRouter>
        <AppShell>
          <div data-testid="test-child">Dashboard Content</div>
        </AppShell>
      </MemoryRouter>
    );

    expect(screen.getByTestId('app-shell')).toBeInTheDocument();
    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('test-child')).toHaveTextContent('Dashboard Content');
  });
});

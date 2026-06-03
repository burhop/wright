import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import Sidebar from '../src/components/layout/Sidebar';

describe('Sidebar', () => {
  it('renders all navigation sections', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('nav-dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('nav-tool-registry')).toBeInTheDocument();
    expect(screen.getByTestId('nav-file-vault')).toBeInTheDocument();
  });
});

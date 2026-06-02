import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import StatusBar from '../src/components/layout/StatusBar';
import type { ServiceStatus, TraceContext } from '../src/store/types';

describe('StatusBar', () => {
  it('renders statuses and latest trace info correctly', () => {
    const mockStatuses: ServiceStatus[] = [
      { serviceId: 'wright-api', name: 'Wright API', endpoint: '/api/health', state: 'connected', lastChecked: Date.now() },
      { serviceId: 'hermes-agent', name: 'Hermes Agent', endpoint: '/api/agent/health', state: 'disconnected', lastChecked: Date.now() },
      { serviceId: 'inference', name: 'LLM Inference', endpoint: '/api/inference/health', state: 'unknown', lastChecked: null },
    ];

    const mockTrace: TraceContext = {
      traceId: 'tr-abc123xyz4567890',
      spanId: 'span-1',
      actionName: 'test-action',
      startTime: Date.now(),
      duration: null,
      status: 'in-progress',
    };

    render(<StatusBar statuses={mockStatuses} latestTrace={mockTrace} />);

    expect(screen.getByTestId('status-bar')).toBeInTheDocument();
    
    expect(screen.getByTestId('status-wright-api')).toBeInTheDocument();
    expect(screen.getByTestId('status-hermes-agent')).toBeInTheDocument();
    expect(screen.getByTestId('status-inference')).toBeInTheDocument();

    expect(screen.getByTestId('latest-trace')).toHaveTextContent(/TRACE: tr-abc12/);
  });
});

import StatusDot from '../common/StatusDot';
import type { ServiceStatus, TraceContext } from '../../store/types';

interface StatusBarProps {
  statuses?: ServiceStatus[];
  latestTrace?: TraceContext | null;
}

const DEFAULT_STATUSES: ServiceStatus[] = [
  { serviceId: 'wright-api', name: 'Wright API', endpoint: '/api/health', state: 'unknown', lastChecked: null },
  { serviceId: 'hermes-agent', name: 'Hermes Agent', endpoint: '/api/agent/health', state: 'unknown', lastChecked: null },
  { serviceId: 'inference', name: 'LLM Inference', endpoint: '/api/inference/health', state: 'unknown', lastChecked: null },
];

export function StatusBar({ statuses = DEFAULT_STATUSES, latestTrace = null }: StatusBarProps) {
  return (
    <div
      data-testid="status-bar"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-lg)',
        padding: '0 var(--space-md)',
        fontFamily: 'var(--font-ui)',
        fontSize: '0.85rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
        {statuses.map((svc) => (
          <StatusDot
            key={svc.serviceId}
            state={svc.state}
            label={svc.name}
            data-testid={`status-${svc.serviceId}`}
          />
        ))}
      </div>

      {latestTrace && (
        <div
          data-testid="latest-trace"
          style={{
            borderLeft: '1px solid var(--color-border)',
            paddingLeft: 'var(--space-md)',
            color: 'var(--color-secondary)',
            fontSize: '0.8rem',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <span>TRACE: {latestTrace.traceId.slice(0, 8)}...</span>
        </div>
      )}
    </div>
  );
}

export default StatusBar;

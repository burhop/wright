interface StatusDotProps {
  state: 'connected' | 'disconnected' | 'unknown';
  label?: string;
  'data-testid'?: string;
}

export function StatusDot({ state, label, 'data-testid': testId }: StatusDotProps) {
  const colorMap = {
    connected: 'var(--color-success)',
    disconnected: 'var(--color-error)',
    unknown: 'var(--color-warning)',
  };

  const isConnected = state === 'connected';

  return (
    <span
      data-testid={testId || `status-dot-${state}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--space-sm)',
        fontSize: '0.875rem',
        fontFamily: 'var(--font-ui)',
      }}
    >
      <span
        className={isConnected ? 'pulse-success-glow' : undefined}
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: colorMap[state],
          boxShadow: `0 0 8px ${colorMap[state]}`,
          transition: 'background-color 0.3s ease, box-shadow 0.3s ease',
        }}
      />
      {label && <span style={{ color: 'var(--color-primary)', fontWeight: 500 }}>{label}</span>}
    </span>
  );
}

export default StatusDot;

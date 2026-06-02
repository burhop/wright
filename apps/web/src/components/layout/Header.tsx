import { useState, useEffect } from 'react';
import StatusBar from './StatusBar';
import useHealthStatus from '../../hooks/useHealthStatus';
import telemetry from '../../services/telemetry';
import type { TraceContext } from '../../store/types';

export function Header() {
  const statuses = useHealthStatus();
  const [latestTrace, setLatestTrace] = useState<TraceContext | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      const recent = telemetry.getRecentTraces(1);
      if (recent.length > 0) {
        setLatestTrace(recent[0]);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <header
      data-testid="header"
      style={{
        height: '60px',
        backgroundColor: 'var(--color-surface-subtle)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-lg)',
        zIndex: 10,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
        <span style={{ fontSize: '1.4rem', fontWeight: 'bold', letterSpacing: '1px', fontFamily: 'var(--font-ui)', color: 'var(--color-primary)' }}>
          WRIGHT
        </span>
        <span style={{ fontSize: '0.8rem', color: 'var(--color-secondary)', border: '1px solid var(--color-border)', padding: '2px 6px', borderRadius: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          LOCAL-FIRST
        </span>
      </div>
      
      <StatusBar statuses={statuses} latestTrace={latestTrace} />
    </header>
  );
}

export default Header;

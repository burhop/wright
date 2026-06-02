import { useEffect } from 'react';
import useLogger from '../../hooks/useLogger';

export function DashboardPage() {
  const logger = useLogger('DashboardPage');

  useEffect(() => {
    logger.info('Dashboard Page loaded');
  }, [logger]);

  return (
    <div
      data-testid="page-dashboard"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-xl)',
        maxWidth: '1200px',
        margin: '0 auto',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
        <h1 style={{ fontFamily: 'var(--font-ui)', fontSize: '2.5rem', fontWeight: 600, color: 'var(--color-primary)', textAlign: 'left', letterSpacing: '-0.5px' }}>
          Welcome to Wright
        </h1>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: '1.15rem', color: 'var(--color-secondary)', textAlign: 'left', maxWidth: '800px' }}>
          A local-first multi-agent mechanical engineering appliance. Wright runs locally to orchestrate, analyze, and document your mechanical designs under complete privacy.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-xl)',
        }}
      >
        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
            textAlign: 'left',
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>🤖</span>
          <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.35rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            Hermes Agent
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'var(--color-secondary)' }}>
            Interact with the local engineering agent using natural language. Execute workspace scripts, generate calculations, and inspect designs transparently.
          </p>
        </div>

        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
            textAlign: 'left',
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>🔧</span>
          <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.35rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            Tool Registry
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'var(--color-secondary)' }}>
            Explore available system tools, solvers, and analytical adapters. Wright exposes CAD parsers, finite element solvers, and data formatters to agents.
          </p>
        </div>

        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
            textAlign: 'left',
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>📂</span>
          <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.35rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            File Vault
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'var(--color-secondary)' }}>
            Manage engineering artifacts, design specs, and simulation outputs. The vault operates entirely offline, keeping your raw files secure in your workspace.
          </p>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;

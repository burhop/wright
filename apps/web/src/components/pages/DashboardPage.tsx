import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import useLogger from '../../hooks/useLogger';
import { AgentChatIcon, ToolRegistryIcon, FileVaultIcon } from '../common/Icons';

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
        gap: 'var(--space-2xl)',
        maxWidth: '1200px',
        margin: '0 auto',
        padding: 'var(--space-2xl) var(--space-xl)',
      }}
      className="animate-fade-in-up"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
        <h1 style={{ fontFamily: 'var(--font-ui)', fontSize: '2.8rem', fontWeight: 700, color: 'var(--color-primary)', textAlign: 'left', letterSpacing: '-0.75px' }}>
          Welcome to Wright
        </h1>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: '1.2rem', color: 'var(--color-secondary)', textAlign: 'left', maxWidth: '800px', lineHeight: 1.7 }}>
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
        <Link
          to="/agent-chat"
          className="glow-card"
          style={{
            padding: 'var(--space-2xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
            textAlign: 'left',
            cursor: 'pointer',
          }}
        >
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'rgba(56, 189, 248, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-secondary)',
            boxShadow: 'var(--shadow-glow)',
          }}>
            <AgentChatIcon size={24} />
          </div>
          <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.4rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            Hermes Agent
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'var(--color-secondary)', lineHeight: 1.5 }}>
            Interact with the local engineering agent using natural language. Execute workspace scripts, generate calculations, and inspect designs transparently.
          </p>
        </Link>

        <Link
          to="/tool-registry"
          className="glow-card"
          style={{
            padding: 'var(--space-2xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
            textAlign: 'left',
            cursor: 'pointer',
          }}
        >
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'rgba(56, 189, 248, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-secondary)',
            boxShadow: 'var(--shadow-glow)',
          }}>
            <ToolRegistryIcon size={24} />
          </div>
          <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.4rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            Tool Registry
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'var(--color-secondary)', lineHeight: 1.5 }}>
            Explore available system tools, solvers, and analytical adapters. Wright exposes CAD parsers, finite element solvers, and data formatters to agents.
          </p>
        </Link>

        <Link
          to="/file-vault"
          className="glow-card"
          style={{
            padding: 'var(--space-2xl)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-md)',
            textAlign: 'left',
            cursor: 'pointer',
          }}
        >
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'rgba(56, 189, 248, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-secondary)',
            boxShadow: 'var(--shadow-glow)',
          }}>
            <FileVaultIcon size={24} />
          </div>
          <h2 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.4rem', fontWeight: 600, color: 'var(--color-primary)' }}>
            File Vault
          </h2>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', color: 'var(--color-secondary)', lineHeight: 1.5 }}>
            Manage engineering artifacts, design specs, and simulation outputs. The vault operates entirely offline, keeping your raw files secure in your workspace.
          </p>
        </Link>
      </div>
    </div>
  );
}

export default DashboardPage;

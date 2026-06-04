import React from 'react';

interface ServerTypeBadgeProps {
  type: 'stdio' | 'sse' | 'webmcp';
}

export const ServerTypeBadge: React.FC<ServerTypeBadgeProps> = ({ type }) => {
  const isLocal = type === 'stdio';
  
  const badgeStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 'var(--space-xs)',
    padding: '2px 8px',
    borderRadius: 'var(--radius-sm)',
    fontSize: '0.75rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    width: 'fit-content',
    cursor: 'default',
    border: '1px solid',
  };

  const localStyle: React.CSSProperties = {
    ...badgeStyle,
    backgroundColor: 'rgba(245, 158, 11, 0.12)',
    borderColor: 'var(--color-warning)',
    color: 'var(--color-warning)',
  };

  const networkStyle: React.CSSProperties = {
    ...badgeStyle,
    backgroundColor: 'rgba(56, 189, 248, 0.12)',
    borderColor: 'var(--color-secondary)',
    color: 'var(--color-secondary)',
  };

  const style = isLocal ? localStyle : networkStyle;
  const label = isLocal ? '⬡ Local' : '⚡ Network';
  const tooltip = isLocal 
    ? 'Runs as a local subprocess on this machine via stdio.' 
    : 'Connects to a remote endpoint via SSE or WebSocket.';

  return (
    <div 
      style={style} 
      title={tooltip}
      data-testid={`server-type-badge-${type}`}
    >
      <span>{label}</span>
    </div>
  );
};
export default ServerTypeBadge;

import { useMemo } from 'react';

interface DiffViewerProps {
  diffText: string;
}

interface DiffLine {
  text: string;
  type: 'addition' | 'deletion' | 'header' | 'hunk' | 'normal';
}

export function DiffViewer({ diffText }: DiffViewerProps) {
  const parsedLines = useMemo((): DiffLine[] => {
    if (!diffText) return [];
    
    return diffText.split('\n').map((line) => {
      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff --git')) {
        return { text: line, type: 'header' };
      }
      if (line.startsWith('@@')) {
        return { text: line, type: 'hunk' };
      }
      if (line.startsWith('+')) {
        return { text: line, type: 'addition' };
      }
      if (line.startsWith('-')) {
        return { text: line, type: 'deletion' };
      }
      return { text: line, type: 'normal' };
    });
  }, [diffText]);

  const getLineStyle = (type: DiffLine['type']): React.CSSProperties => {
    switch (type) {
      case 'addition':
        return {
          backgroundColor: 'rgba(34, 197, 94, 0.15)',
          color: 'var(--color-success, #22c55e)',
          borderLeft: '3px solid var(--color-success, #22c55e)',
        };
      case 'deletion':
        return {
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          color: 'var(--color-error, #ef4444)',
          borderLeft: '3px solid var(--color-error, #ef4444)',
        };
      case 'hunk':
        return {
          backgroundColor: 'rgba(168, 85, 247, 0.08)',
          color: 'var(--color-secondary)',
          fontStyle: 'italic',
          borderLeft: '3px solid var(--color-accent, #4f46e5)',
        };
      case 'header':
        return {
          backgroundColor: 'var(--color-neutral)',
          color: 'var(--color-primary)',
          fontWeight: 'bold',
          opacity: 0.8,
        };
      default:
        return {
          color: 'var(--color-primary)',
          opacity: 0.9,
        };
    }
  };

  if (!diffText) {
    return (
      <div style={{ color: 'var(--color-secondary)', fontSize: '0.8rem', padding: 'var(--space-md)' }}>
        No changes detected.
      </div>
    );
  }

  return (
    <div
      style={{
        flex: 1,
        overflow: 'auto',
        backgroundColor: 'var(--color-surface-subtle)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-sm)',
        fontFamily: 'monospace',
        fontSize: '0.75rem',
        textAlign: 'left',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {parsedLines.map((line, i) => (
          <div
            key={i}
            style={{
              padding: '2px var(--space-md)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
              ...getLineStyle(line.type),
            }}
          >
            {line.text}
          </div>
        ))}
      </div>
    </div>
  );
}

export default DiffViewer;

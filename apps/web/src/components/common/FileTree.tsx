import { useState } from 'react';
import type { WorkspaceFile } from '../../store/types';

interface FileTreeProps {
  node: WorkspaceFile;
  onFileClick?: (path: string) => void;
}

export function FileTree({ node, onFileClick }: FileTreeProps) {
  const [isOpen, setIsOpen] = useState(false);
  const isDir = node.type === 'directory';

  const handleClick = () => {
    if (isDir) {
      setIsOpen(!isOpen);
    } else if (onFileClick) {
      onFileClick(node.path);
    }
  };

  return (
    <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.9rem', color: 'var(--color-primary)', textAlign: 'left' }}>
      <div
        data-testid={`file-${node.name}`}
        onClick={handleClick}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-sm)',
          padding: 'var(--space-xs) var(--space-sm)',
          cursor: 'pointer',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'transparent',
          transition: 'background-color 0.2s ease',
          userSelect: 'none',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--color-surface)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
        }}
      >
        <span>{isDir ? (isOpen ? '▼' : '▶') : '📄'}</span>
        <span>{node.name}</span>
      </div>

      {isDir && isOpen && node.children && (
        <div style={{ paddingLeft: 'var(--space-lg)', borderLeft: '1px solid var(--color-border)', marginLeft: 'var(--space-sm)' }}>
          {node.children.map((child) => (
            <FileTree key={child.path} node={child} onFileClick={onFileClick} />
          ))}
        </div>
      )}
    </div>
  );
}

export default FileTree;

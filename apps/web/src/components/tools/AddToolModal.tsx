import { useState, type FormEvent } from 'react';

interface AddToolModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string, type: 'stdio' | 'sse' | 'webmcp', command: string[] | string, category: string) => Promise<void>;
}

export function AddToolModal({ isOpen, onClose, onSave }: AddToolModalProps) {
  const [name, setName] = useState('');
  const [type, setType] = useState<'stdio' | 'sse' | 'webmcp'>('stdio');
  const [category, setCategory] = useState('utilities');
  const [commandStr, setCommandStr] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    // Validation
    const cleanName = name.trim();
    if (!cleanName) {
      setErrorMsg('Server name is required.');
      return;
    }

    let command: string[] | string = '';
    if (type === 'stdio') {
      const parts = commandStr.trim().split(/\s+/).filter(Boolean);
      if (parts.length === 0) {
        setErrorMsg('CLI command is required for stdio transport.');
        return;
      }
      command = parts;
    } else if (type === 'sse') {
      const url = commandStr.trim();
      if (!url) {
        setErrorMsg('SSE server URL is required.');
        return;
      }
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        setErrorMsg('SSE server URL must start with http:// or https://');
        return;
      }
      command = url;
    }

    setIsLoading(true);
    try {
      await onSave(cleanName, type, command, category);
      // Reset form on success
      setName('');
      setType('stdio');
      setCategory('utilities');
      setCommandStr('');
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'An error occurred while saving the server.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      data-testid="add-tool-modal-overlay"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(10, 9, 8, 0.8)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000,
        padding: 'var(--space-md)',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '500px',
          backgroundColor: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-xl)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-lg)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.3)',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--color-primary)', fontFamily: 'var(--font-ui)', fontWeight: 600 }}>
            Register Custom MCP Server
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-secondary)', marginTop: 'var(--space-xs)' }}>
            Expose local CLI subprocess wrapper or remote SSE server tools to your agents.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          {/* Name Field */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
            <label htmlFor="mcp-name" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-primary)' }}>
              Server Name
            </label>
            <input
              id="mcp-name"
              type="text"
              placeholder="e.g. My Mesh Analyzer"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
              style={{
                padding: 'var(--space-md)',
                backgroundColor: 'var(--color-neutral)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-primary)',
                fontSize: '0.9rem',
              }}
            />
          </div>

          {/* Type Select */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
            <label htmlFor="mcp-type" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-primary)' }}>
              Transport Type
            </label>
            <select
              id="mcp-type"
              value={type}
              onChange={(e) => {
                setType(e.target.value as any);
                setCommandStr('');
              }}
              disabled={isLoading}
              style={{
                padding: 'var(--space-md)',
                backgroundColor: 'var(--color-neutral)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-primary)',
                fontSize: '0.9rem',
                cursor: 'pointer',
              }}
            >
              <option value="stdio">stdio (Local Command Subprocess)</option>
              <option value="sse">sse (Remote Server Sent Events Endpoint)</option>
              <option value="webmcp">webmcp (Client-side Web Bridge)</option>
            </select>
          </div>

          {/* Category Select */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
            <label htmlFor="mcp-category" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-primary)' }}>
              Category
            </label>
            <select
              id="mcp-category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              disabled={isLoading}
              style={{
                padding: 'var(--space-md)',
                backgroundColor: 'var(--color-neutral)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-primary)',
                fontSize: '0.9rem',
                cursor: 'pointer',
              }}
            >
              <option value="utilities">Utilities</option>
              <option value="simulation">Simulation</option>
              <option value="cad">CAD</option>
              <option value="analysis">Analysis</option>
            </select>
          </div>

          {/* Command or URL input */}
          {type !== 'webmcp' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
              <label htmlFor="mcp-command" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-primary)' }}>
                {type === 'stdio' ? 'CLI Command / Arguments' : 'SSE Connection URL'}
              </label>
              <input
                id="mcp-command"
                type="text"
                placeholder={type === 'stdio' ? 'e.g. python scripts/mesh_tool.py' : 'e.g. http://localhost:8080/sse'}
                value={commandStr}
                onChange={(e) => setCommandStr(e.target.value)}
                disabled={isLoading}
                style={{
                  padding: 'var(--space-md)',
                  backgroundColor: 'var(--color-neutral)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--color-primary)',
                  fontSize: '0.9rem',
                }}
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--color-secondary)' }}>
                {type === 'stdio'
                  ? 'Enter the full command path and options separated by spaces.'
                  : 'Specify the HTTP endpoint yielding Server-Sent Events.'}
              </span>
            </div>
          )}

          {/* Error Message */}
          {errorMsg && (
            <div
              style={{
                color: 'var(--color-error)',
                fontSize: '0.85rem',
                backgroundColor: 'rgba(248, 113, 113, 0.1)',
                padding: 'var(--space-sm) var(--space-md)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-error)',
              }}
            >
              {errorMsg}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-md)', marginTop: 'var(--space-md)' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              style={{
                padding: 'var(--space-md) var(--space-lg)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-primary)',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              style={{
                padding: 'var(--space-md) var(--space-lg)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-primary)',
                color: 'var(--color-neutral)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {isLoading ? 'Saving...' : 'Register'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

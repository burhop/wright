import FileTree from '../common/FileTree';
import type { WorkspaceFile } from '../../store/types';

const PLACEHOLDER_WORKSPACE: WorkspaceFile = {
  name: 'wright-workspace',
  path: '/',
  type: 'directory',
  size: null,
  children: [
    {
      name: 'designs',
      path: '/designs',
      type: 'directory',
      size: null,
      children: [
        { name: 'shaft_spec.cad', path: '/designs/shaft_spec.cad', type: 'file', size: 245000, children: null },
        { name: 'gearbox_layout.step', path: '/designs/gearbox_layout.step', type: 'file', size: 12500000, children: null },
      ]
    },
    {
      name: 'simulations',
      path: '/simulations',
      type: 'directory',
      size: null,
      children: [
        { name: 'thermal_mesh.msh', path: '/simulations/thermal_mesh.msh', type: 'file', size: 4800000, children: null },
        { name: 'stress_results.json', path: '/simulations/stress_results.json', type: 'file', size: 34200, children: null },
      ]
    },
    { name: 'calc_stiffness.py', path: '/calc_stiffness.py', type: 'file', size: 1840, children: null },
    { name: 'requirements.txt', path: '/requirements.txt', type: 'file', size: 120, children: null },
  ]
};

export function WorkspacePanel() {
  return (
    <div
      data-testid="workspace-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--color-surface-subtle)',
        borderLeft: '1px solid var(--color-border)',
        width: '280px',
      }}
    >
      <div
        style={{
          padding: 'var(--space-lg)',
          borderBottom: '1px solid var(--color-border)',
          fontFamily: 'var(--font-ui)',
          fontWeight: '600',
          fontSize: '0.9rem',
          color: 'var(--color-primary)',
          letterSpacing: '0.5px',
        }}
      >
        WORKSPACE BROWSER
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-md)' }}>
        <FileTree node={PLACEHOLDER_WORKSPACE} />
      </div>
    </div>
  );
}

export default WorkspacePanel;

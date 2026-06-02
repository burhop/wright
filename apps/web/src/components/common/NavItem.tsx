import { NavLink } from 'react-router-dom';

interface NavItemProps {
  label: string;
  path: string;
  id: string;
  icon: string;
}

export function NavItem({ label, path, id }: NavItemProps) {
  return (
    <NavLink
      to={path}
      data-testid={`nav-${id}`}
      style={({ isActive }) => ({
        display: 'block',
        padding: 'var(--space-md) var(--space-lg)',
        color: isActive ? 'var(--color-primary)' : 'var(--color-secondary)',
        backgroundColor: isActive ? 'var(--color-surface)' : 'transparent',
        borderRadius: 'var(--radius-md)',
        fontSize: '0.95rem',
        fontWeight: isActive ? '600' : '400',
        fontFamily: 'var(--font-ui)',
        borderLeft: isActive ? '3px solid var(--color-secondary)' : '3px solid transparent',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
      })}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
        <span style={{ fontSize: '1.1rem' }}>◈</span>
        <span>{label}</span>
      </div>
    </NavLink>
  );
}

export default NavItem;

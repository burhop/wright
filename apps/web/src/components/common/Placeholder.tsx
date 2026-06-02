
interface PlaceholderProps {
  title: string;
  description: string;
  'data-testid'?: string;
}

export function Placeholder({ title, description, 'data-testid': testId }: PlaceholderProps) {
  return (
    <div
      data-testid={testId || "placeholder"}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-xl)',
        height: '100%',
        minHeight: '200px',
        backgroundColor: 'var(--color-surface-subtle)',
        border: '1px dashed var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        color: 'var(--color-secondary)',
        textAlign: 'center',
      }}
    >
      <h3 style={{ fontFamily: 'var(--font-ui)', fontSize: '1.25rem', marginBottom: 'var(--space-sm)', color: 'var(--color-primary)' }}>
        {title}
      </h3>
      <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.95rem', maxWidth: '400px' }}>
        {description}
      </p>
    </div>
  );
}

export default Placeholder;

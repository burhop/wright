export function ProcessDefinitionLoading() {
  return (
    <section
      className="process-definition__state"
      data-testid="process-definition-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <h2>Loading the validated process definition</h2>
      <p>Wright is checking one exact read-only definition and its identity.</p>
    </section>
  );
}

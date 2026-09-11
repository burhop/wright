export type WorkflowComposerEnvironment = Readonly<Record<string, unknown>>;

const ENABLED_VALUES = new Set(["1", "true", "yes", "on"]);

export function workflowComposerEnabled(
  environment: WorkflowComposerEnvironment = import.meta.env,
): boolean {
  const value = environment.VITE_WRIGHT_WORKFLOW_COMPOSER;
  return ENABLED_VALUES.has(
    String(value ?? "")
      .trim()
      .toLowerCase(),
  );
}

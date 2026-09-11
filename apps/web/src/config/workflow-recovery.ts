export type WorkflowRecoveryEnvironment = Readonly<Record<string, unknown>>;

const ENABLED_VALUES = new Set(["1", "true", "yes", "on"]);

export function workflowRecoveryEnabled(
  environment: WorkflowRecoveryEnvironment = import.meta.env,
): boolean {
  const value = environment.VITE_WRIGHT_WORKFLOW_RECOVERY;
  return ENABLED_VALUES.has(
    String(value ?? "")
      .trim()
      .toLowerCase(),
  );
}

export function workspaceSurfacesEnabled(
  environment: Record<string, unknown> = import.meta.env,
): boolean {
  const value = environment.VITE_WORKSPACE_SURFACES_ENABLED;
  if (["1", "true", "yes", "on"].includes(String(value).toLowerCase())) {
    return true;
  }
  if (!import.meta.env.DEV || typeof window === "undefined") return false;
  try {
    return (
      window.localStorage.getItem("wright.workspaceSurfaces.testEnabled") ===
      "1"
    );
  } catch {
    // Opaque/sandboxed documents may expose Storage while denying all access.
    return false;
  }
}

export function rivetWorkflowsTabEnabled(
  environment: Record<string, unknown> = import.meta.env,
): boolean {
  const value = environment.VITE_RIVET_WORKFLOWS_TAB_ENABLED;
  if (value === undefined || value === null || value === "") return true;
  return !["0", "false", "no", "off"].includes(String(value).toLowerCase());
}

export function engineeringWorkflowPrototypeEnabled(
  environment: Record<string, unknown> = import.meta.env,
): boolean {
  const value = environment.VITE_ENGINEERING_WORKFLOW_PROTOTYPE;
  if (value !== undefined && value !== null && value !== "") {
    return ["1", "true", "yes", "on"].includes(String(value).toLowerCase());
  }
  if (!import.meta.env.DEV || typeof window === "undefined") return false;
  try {
    return (
      window.localStorage.getItem(
        "wright.engineeringWorkflowPrototype.testEnabled",
      ) === "1"
    );
  } catch {
    return false;
  }
}

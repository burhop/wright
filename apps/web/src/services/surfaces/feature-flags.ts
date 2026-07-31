export function workspaceSurfacesEnabled(
  environment: Record<string, unknown> = import.meta.env,
): boolean {
  const value = environment.VITE_WORKSPACE_SURFACES_ENABLED;
  return ["1", "true", "yes", "on"].includes(String(value).toLowerCase());
}

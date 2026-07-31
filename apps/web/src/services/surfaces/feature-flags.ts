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
      window.localStorage.getItem("wright.workspaceSurfaces.testEnabled") === "1"
    );
  } catch {
    // Opaque/sandboxed documents may expose Storage while denying all access.
    return false;
  }
}

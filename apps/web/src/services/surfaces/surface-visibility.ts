import type { SurfaceDescriptor } from "./surface-contract";

function isRetainedRivetEditor(descriptor: SurfaceDescriptor): boolean {
  return (
    descriptor.source.kind === "live_app" &&
    descriptor.source.sourceId === "wright.rivet-editor"
  );
}

export function isVisibleWorkspaceSurface(
  descriptor: SurfaceDescriptor,
): boolean {
  // Rivet is rendered inside Wright's retained workflow tab, but its process
  // and preview authority still belong to the managed live-app service.
  return !isRetainedRivetEditor(descriptor);
}

export function visibleWorkspaceSurfaces(
  descriptors: readonly SurfaceDescriptor[],
): SurfaceDescriptor[] {
  return descriptors.filter(isVisibleWorkspaceSurface);
}

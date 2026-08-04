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
  return !(isRetainedRivetEditor(descriptor) && descriptor.lifecycle === "failed");
}

export function visibleWorkspaceSurfaces(
  descriptors: readonly SurfaceDescriptor[],
): SurfaceDescriptor[] {
  return descriptors.filter(isVisibleWorkspaceSurface);
}

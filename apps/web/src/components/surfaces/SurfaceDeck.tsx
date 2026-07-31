import { useEffect, useState, type ReactNode } from "react";

import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";

interface Props {
  readonly descriptors: readonly SurfaceDescriptor[];
  readonly activeSurfaceId: string;
  readonly maximumRetainedHosts?: number;
  readonly renderSurface: (descriptor: SurfaceDescriptor) => ReactNode;
}

function stateful(descriptor: SurfaceDescriptor): boolean {
  return ["live_app", "mcp_app"].includes(descriptor.source.kind);
}

export function SurfaceDeck({
  descriptors,
  activeSurfaceId,
  maximumRetainedHosts = 6,
  renderSurface,
}: Props) {
  const [retained, setRetained] = useState<readonly string[]>([]);

  useEffect(() => {
    setRetained((previous) => {
      const available = new Set(descriptors.map((item) => item.surfaceId));
      const next = previous.filter((surfaceId) => available.has(surfaceId));
      for (const descriptor of descriptors) {
        if (stateful(descriptor) && !next.includes(descriptor.surfaceId)) {
          next.push(descriptor.surfaceId);
        }
      }
      const activeDescriptor = descriptors.find(
        (descriptor) => descriptor.surfaceId === activeSurfaceId,
      );
      if (activeDescriptor && stateful(activeDescriptor)) {
        const activeIndex = next.indexOf(activeSurfaceId);
        if (activeIndex >= 0) {
          next.splice(activeIndex, 1);
          next.push(activeSurfaceId);
        }
      }
      while (next.length > maximumRetainedHosts) {
        const candidate = next.findIndex((item) => item !== activeSurfaceId);
        if (candidate < 0) break;
        next.splice(candidate, 1);
      }
      return next.length === previous.length &&
        next.every((item, index) => item === previous[index])
        ? previous
        : next;
    });
  }, [activeSurfaceId, descriptors, maximumRetainedHosts]);

  const mounted = descriptors.filter(
    (descriptor) =>
      descriptor.surfaceId === activeSurfaceId || retained.includes(descriptor.surfaceId),
  );
  return (
    <div data-testid="surface-retained-deck" style={{ height: "100%" }}>
      {mounted.map((descriptor) => {
        const active = descriptor.surfaceId === activeSurfaceId;
        return (
          <section
            key={descriptor.surfaceId}
            role="tabpanel"
            aria-label={descriptor.title}
            aria-hidden={!active}
            hidden={!active}
            style={{ height: "100%" }}
          >
            {renderSurface(descriptor)}
          </section>
        );
      })}
    </div>
  );
}

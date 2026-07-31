import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";

interface Props {
  readonly descriptors: readonly SurfaceDescriptor[];
  readonly activeSurfaceId: string;
  readonly maximumRetainedHosts?: number;
  readonly renderSurface: (descriptor: SurfaceDescriptor) => ReactNode;
  readonly onOpenInBrowser?: (
    descriptor: SurfaceDescriptor,
  ) => void | Promise<void>;
}

function stateful(descriptor: SurfaceDescriptor): boolean {
  return ["live_app", "mcp_app"].includes(descriptor.source.kind);
}

export function SurfaceDeck({
  descriptors,
  activeSurfaceId,
  maximumRetainedHosts = 6,
  renderSurface,
  onOpenInBrowser,
}: Props) {
  const [retained, setRetained] = useState<readonly string[]>([]);
  const [evicted, setEvicted] = useState<readonly string[]>([]);
  const [pressureCandidate, setPressureCandidate] = useState<string | null>(
    null,
  );
  const activePanelRef = useRef<HTMLElement>(null);

  const descriptorIds = useMemo(
    () => descriptors.map((item) => item.surfaceId),
    [descriptors],
  );

  useEffect(() => {
    if (evicted.includes(activeSurfaceId)) {
      setEvicted((previous) =>
        previous.filter((item) => item !== activeSurfaceId),
      );
    }
  }, [activeSurfaceId, evicted]);

  useEffect(() => {
    setRetained((previous) => {
      const available = new Set(descriptorIds);
      const next = previous.filter(
        (surfaceId) => available.has(surfaceId) && !evicted.includes(surfaceId),
      );
      for (const descriptor of descriptors) {
        if (
          stateful(descriptor) &&
          !evicted.includes(descriptor.surfaceId) &&
          !next.includes(descriptor.surfaceId)
        ) {
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
      return next.length === previous.length &&
        next.every((item, index) => item === previous[index])
        ? previous
        : next;
    });
  }, [activeSurfaceId, descriptorIds, descriptors, evicted]);

  useEffect(() => {
    const candidates = retained.filter((item) => item !== activeSurfaceId);
    setPressureCandidate(
      retained.length > maximumRetainedHosts ? (candidates[0] ?? null) : null,
    );
  }, [activeSurfaceId, maximumRetainedHosts, retained]);

  const mounted = descriptors.filter(
    (descriptor) =>
      descriptor.surfaceId === activeSurfaceId ||
      retained.includes(descriptor.surfaceId),
  );
  const pressureDescriptor = descriptors.find(
    (descriptor) => descriptor.surfaceId === pressureCandidate,
  );
  return (
    <div
      data-testid="surface-retained-deck"
      style={{ height: "100%", position: "relative" }}
    >
      {pressureCandidate && (
        <div
          role="alertdialog"
          aria-labelledby="surface-pressure-title"
          aria-describedby="surface-pressure-description"
          className="surface-pressure-dialog"
        >
          <strong id="surface-pressure-title">
            Surface memory limit reached
          </strong>
          <p id="surface-pressure-description">
            {pressureCandidate} must reload if it is removed from memory.
          </p>
          <button
            type="button"
            onClick={() => {
              setEvicted((previous) =>
                previous.includes(pressureCandidate)
                  ? previous
                  : [...previous, pressureCandidate],
              );
              setPressureCandidate(null);
              queueMicrotask(() => activePanelRef.current?.focus());
            }}
          >
            Reload least recently used surface
          </button>
          <button type="button" onClick={() => setPressureCandidate(null)}>
            Keep current tabs
          </button>
          <button
            type="button"
            disabled={!onOpenInBrowser || !pressureDescriptor}
            onClick={() => {
              if (pressureDescriptor)
                void onOpenInBrowser?.(pressureDescriptor);
            }}
          >
            Open surface in browser
          </button>
        </div>
      )}
      {mounted.map((descriptor) => {
        const active = descriptor.surfaceId === activeSurfaceId;
        return (
          <section
            ref={active ? activePanelRef : undefined}
            key={descriptor.surfaceId}
            id={`surface-panel-${descriptor.surfaceId}`}
            role="tabpanel"
            aria-labelledby={`surface-tab-control-${descriptor.surfaceId}`}
            aria-label={descriptor.title}
            aria-hidden={!active}
            hidden={!active}
            tabIndex={active ? -1 : undefined}
            style={{ height: "100%" }}
          >
            {renderSurface(descriptor)}
          </section>
        );
      })}
    </div>
  );
}

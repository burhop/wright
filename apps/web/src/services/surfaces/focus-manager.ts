export type HostFocusRegion = "chat" | "tabs" | "toolbar" | "frame-return";

const regionOrder: readonly HostFocusRegion[] = [
  "chat",
  "tabs",
  "toolbar",
  "frame-return",
];

export function nextHostFocusRegion(
  current: HostFocusRegion,
  reverse = false,
): HostFocusRegion {
  const index = regionOrder.indexOf(current);
  const offset = reverse ? -1 : 1;
  return regionOrder[
    (index + offset + regionOrder.length) % regionOrder.length
  ];
}

export interface FocusRegionElements {
  readonly chat: HTMLElement | null;
  readonly tabs: HTMLElement | null;
  readonly toolbar: HTMLElement | null;
  readonly frameReturn: HTMLElement | null;
}

export class SurfaceFocusManager {
  private initiator: HTMLElement | null = null;

  rememberInitiator(element: HTMLElement | null): void {
    this.initiator = element;
  }

  restoreInitiator(fallback: HTMLElement | null): void {
    const target = this.initiator?.isConnected ? this.initiator : fallback;
    target?.focus();
    this.initiator = null;
  }

  cycle(
    current: HostFocusRegion,
    regions: FocusRegionElements,
    reverse = false,
  ): HostFocusRegion {
    let target = nextHostFocusRegion(current, reverse);
    for (let attempts = 0; attempts < regionOrder.length; attempts += 1) {
      const element =
        target === "frame-return" ? regions.frameReturn : regions[target];
      if (element && !element.hasAttribute("disabled")) {
        element.focus();
        return target;
      }
      target = nextHostFocusRegion(target, reverse);
    }
    return current;
  }
}

export function installF6HostRegionCycle(
  root: HTMLElement,
  resolveRegions: () => FocusRegionElements,
): () => void {
  const manager = new SurfaceFocusManager();
  const handler = (event: KeyboardEvent) => {
    if (event.key !== "F6" || !root.contains(document.activeElement)) return;
    event.preventDefault();
    const active = document.activeElement as HTMLElement | null;
    const region = (active?.closest<HTMLElement>("[data-focus-region]")?.dataset
      .focusRegion ?? "chat") as HostFocusRegion;
    manager.cycle(region, resolveRegions(), event.shiftKey);
  };
  root.addEventListener("keydown", handler);
  return () => root.removeEventListener("keydown", handler);
}

export function installElectronReturnAccelerator(
  returnToHost: () => void,
): () => void {
  const handler = () => returnToHost();
  window.addEventListener("wright:return-to-host", handler);
  const unsubscribeDesktop = window.wrightDesktop?.onReturnToHost?.(handler);
  return () => {
    window.removeEventListener("wright:return-to-host", handler);
    unsubscribeDesktop?.();
  };
}

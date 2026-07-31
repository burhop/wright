import { hostAdapter, type HostAdapter } from "../../host-adapter";
import type { SurfaceDescriptor } from "../surface-contract";
import type { PresentationLaunch } from "../surface-client";
import type { SurfacePresenter } from "../registry";

export type LiveFrameStatus = "loading" | "ready" | "unknown" | "blocked";

export class LiveAppPresenter implements SurfacePresenter {
  private readonly launch: PresentationLaunch;
  private descriptor: SurfaceDescriptor;
  private readonly onStatus: (status: LiveFrameStatus) => void;
  private readonly host: HostAdapter;
  private frame: HTMLIFrameElement | null = null;
  private disposed = false;
  private statusTimer: ReturnType<typeof setTimeout> | undefined;

  constructor(
    launch: PresentationLaunch,
    descriptor: SurfaceDescriptor,
    onStatus: (status: LiveFrameStatus) => void,
    host: HostAdapter = hostAdapter,
  ) {
    this.launch = launch;
    this.descriptor = descriptor;
    this.onStatus = onStatus;
    this.host = host;
  }

  mount(container: HTMLElement): void {
    if (this.disposed) throw new Error("Live app presenter is disposed");
    if (this.frame) throw new Error("Live app presenter is already mounted");
    const source = this.host.validateIssuedPreviewUrl(
      this.launch.absoluteBootstrapUrl,
    );
    const frame = document.createElement("iframe");
    frame.src = source;
    frame.title = this.descriptor.title;
    frame.dataset.testid = `surface-frame-${this.descriptor.surfaceId}`;
    frame.setAttribute("sandbox", "allow-scripts allow-forms allow-same-origin");
    frame.setAttribute("referrerpolicy", "no-referrer");
    frame.setAttribute("allow", "fullscreen 'none'; camera 'none'; microphone 'none'; geolocation 'none'");
    frame.style.width = "100%";
    frame.style.height = "100%";
    frame.style.border = "0";
    frame.addEventListener("load", () => {
      if (!this.disposed) {
        if (this.statusTimer !== undefined) clearTimeout(this.statusTimer);
        // A cross-origin load event cannot prove that CSP/XFO allowed visible,
        // interactive content. A later exact-origin bridge handshake may
        // promote this state to ready; until then the browser fallback remains.
        this.onStatus("unknown");
      }
    });
    frame.addEventListener("error", () => {
      if (!this.disposed) this.onStatus("blocked");
    });
    this.frame = frame;
    this.onStatus("loading");
    container.replaceChildren(frame);
    this.statusTimer = setTimeout(() => {
      if (!this.disposed) this.onStatus("unknown");
    }, 5000);
  }

  update(descriptor: SurfaceDescriptor): void {
    const instance = descriptor.instance;
    if (
      instance?.instanceId !== this.launch.instanceId ||
      instance?.generation !== this.launch.generation
    ) {
      throw new Error("Live app presentation belongs to a stale instance generation");
    }
    this.descriptor = descriptor;
    if (this.frame) this.frame.title = descriptor.title;
  }

  focus(): void {
    this.frame?.focus();
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    if (this.statusTimer !== undefined) clearTimeout(this.statusTimer);
    if (this.frame) {
      this.frame.src = "about:blank";
      this.frame.remove();
    }
    this.frame = null;
  }
}

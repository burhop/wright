import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";

interface Props {
  readonly lifecycle: SurfaceDescriptor["lifecycle"];
  readonly frameStatus?: "ready" | "unknown" | "blocked";
}

const messages: Record<SurfaceDescriptor["lifecycle"], string> = {
  declared: "Application is declared but not running.",
  starting: "Application is starting and is not ready for presentation.",
  ready: "Application is ready.",
  unhealthy:
    "Application is unhealthy; recovery or browser fallback may be available.",
  stopping: "Application is stopping; the current presentation is inert.",
  stopped: "Application is stopped. Restart it to create a new generation.",
  failed: "Application failed. Open diagnostics or deliberately restart it.",
};

export function SurfaceStatus({ lifecycle, frameStatus }: Props) {
  const message =
    frameStatus === "blocked" || frameStatus === "unknown"
      ? `${messages[lifecycle]} Embedding may have been blocked by browser framing. Open it in the system browser or retry the panel.`
      : messages[lifecycle];
  return (
    <p role="status" data-testid="surface-status" aria-live="polite">
      {message}
    </p>
  );
}

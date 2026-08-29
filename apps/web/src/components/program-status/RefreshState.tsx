import type { ProgramStatusPublisher } from "../../services/program-status";

export function RefreshState({
  state,
  generatedAt,
  publisher,
  message,
}: {
  state: "loading" | "current" | "stale" | "unavailable";
  generatedAt?: string;
  publisher?: ProgramStatusPublisher | null;
  message?: string | null;
}) {
  const color =
    state === "current"
      ? "var(--color-success, #22c55e)"
      : state === "loading"
        ? "var(--color-secondary)"
        : "var(--color-warning, #f59e0b)";
  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="program-status-refresh-state"
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "var(--space-sm)",
        alignItems: "center",
        color,
      }}
    >
      <span aria-hidden="true">●</span>
      <strong>
        {state === "current"
          ? "Committed evidence current"
          : state === "loading"
            ? "Loading committed evidence"
            : state === "stale"
              ? "Showing last valid evidence"
              : "Program status unavailable"}
      </strong>
      {generatedAt ? (
        <span>Published {new Date(generatedAt).toLocaleString()}</span>
      ) : null}
      {publisher ? <span>Publisher: {publisher.state}</span> : null}
      {message ? <span>{message}</span> : null}
    </div>
  );
}

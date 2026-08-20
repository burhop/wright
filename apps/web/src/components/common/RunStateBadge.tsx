interface RunStateBadgeProps {
  state: string;
}

const stateLabel = (state: string) =>
  ({ queued: "Queued", running: "Running", cancelling: "Cancelling", cancelled: "Cancelled", succeeded: "Succeeded", failed: "Failed" })[state] || state;

export function RunStateBadge({ state }: RunStateBadgeProps) {
  const symbol = state === "succeeded" ? "✓" : state === "failed" ? "!" : state === "cancelled" ? "■" : "●";
  return (
    <span
      className={`rivet-run-state rivet-run-state--${state}`}
      data-testid={`rivet-run-state-${state}`}
      aria-label={`Run state: ${stateLabel(state)}`}
    >
      <span aria-hidden="true">{symbol}</span> {stateLabel(state)}
    </span>
  );
}

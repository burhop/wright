import type {
  RivetRunInspection,
  RivetRunStep,
} from "../../services/workspace-service";
import { RunStateBadge } from "../common/RunStateBadge";

export function TraceProcessDetails({
  inspection,
  onSelectStep,
}: {
  inspection: RivetRunInspection;
  onSelectStep: (step: RivetRunStep) => void;
}) {
  if (!inspection.steps.length) {
    return (
      <p className="workflow-trace__empty">No execution steps were recorded.</p>
    );
  }
  return (
    <ol
      className="workflow-trace__process-list"
      aria-label="Recorded process attempts"
    >
      {inspection.steps.map((step) => (
        <li key={step.step_id}>
          <button type="button" onClick={() => onSelectStep(step)}>
            <span>
              {step.sequence}. {step.label}
              {(step.attempt || 1) > 1 && <small>Attempt {step.attempt}</small>}
            </span>
            <RunStateBadge state={step.state} />
            <span>
              {step.duration_ms == null ? "" : `${step.duration_ms} ms`}
            </span>
          </button>
        </li>
      ))}
    </ol>
  );
}

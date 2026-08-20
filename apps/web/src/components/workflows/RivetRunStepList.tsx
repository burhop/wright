import type { RivetRunStep } from "../../services/workspace-service";
import { RunStateBadge } from "../common/RunStateBadge";

interface RivetRunStepListProps {
  steps: RivetRunStep[];
  onFocusStep?: (step: RivetRunStep) => void;
}

export function RivetRunStepList({ steps, onFocusStep }: RivetRunStepListProps) {
  if (!steps.length) return <p className="rivet-run-empty">No execution steps were recorded.</p>;
  return (
    <ol className="rivet-run-steps" aria-label="Workflow execution steps">
      {steps.map((step) => (
        <li key={step.step_id}>
          <button type="button" onClick={() => onFocusStep?.(step)} disabled={!step.node_id}>
            <span>{step.sequence}. {step.label}</span>
            <RunStateBadge state={step.state} />
            {step.duration_ms != null && <span>{step.duration_ms} ms</span>}
          </button>
          {step.reason_code && <small>{step.reason_code}</small>}
        </li>
      ))}
    </ol>
  );
}

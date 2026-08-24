import type { RivetRunStep } from "../../services/workspace-service";
import { RunStateBadge } from "../common/RunStateBadge";
import { displayEvidenceState } from "./rivet-run-evidence";

interface RivetRunStepListProps {
  steps: RivetRunStep[];
  onFocusStep?: (step: RivetRunStep) => void;
}

function StepValues({
  title,
  values,
  state,
}: {
  title: string;
  values?: RivetRunStep["inputs"];
  state?: string;
}) {
  const retainedValues = values ?? [];
  return (
    <section>
      <h4>{title}</h4>
      {retainedValues.length ? (
        <dl>
          {retainedValues.map((value) => (
            <div key={value.result_id}>
              <dt>{value.name}</dt>
              <dd>
                <span>{value.data_type}</span>
                <span>{displayEvidenceState(value.evidence_state)}</span>
                <pre>{value.preview || "No value"}</pre>
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p>{displayEvidenceState(state)}</p>
      )}
    </section>
  );
}

export function RivetRunStepList({
  steps,
  onFocusStep,
}: RivetRunStepListProps) {
  if (!steps.length)
    return <p className="rivet-run-empty">No execution steps were recorded.</p>;
  return (
    <ol className="rivet-run-steps" aria-label="Workflow execution steps">
      {steps.map((step) => (
        <li key={step.step_id}>
          <button
            type="button"
            data-testid={"rivet-run-step-focus-" + step.step_id}
            onClick={() => onFocusStep?.(step)}
            disabled={!step.node_id}
          >
            <span>
              {step.sequence}. {step.label}
            </span>
            <RunStateBadge state={step.state} />
            {step.duration_ms != null && <span>{step.duration_ms} ms</span>}
          </button>
          {step.reason_code && <small>{step.reason_code}</small>}
          <details className="rivet-run-step-evidence">
            <summary data-testid={"rivet-run-step-evidence-" + step.step_id}>
              Inspect box values
            </summary>
            <div>
              <StepValues
                title="Inputs"
                values={step.inputs}
                state={step.input_state}
              />
              <StepValues
                title="Outputs"
                values={step.outputs}
                state={step.output_state}
              />
            </div>
            <dl className="rivet-run-step-technical">
              <dt>Box type</dt>
              <dd>{step.node_type || "Unavailable"}</dd>
              {step.qualified_tool_name && (
                <>
                  <dt>MCP action</dt>
                  <dd>{step.qualified_tool_name}</dd>
                </>
              )}
              <dt>Technical ID</dt>
              <dd>{step.node_id || "Unavailable"}</dd>
            </dl>
          </details>
        </li>
      ))}
    </ol>
  );
}

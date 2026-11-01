import type {
  RivetRunInspection,
  RivetRunStep,
} from "../../services/workspace-service";
import { RivetRunResult } from "../workflows/RivetRunResult";
import type { TraceGraphSelection } from "./TraceGraph";

export function TraceInspector({
  inspection,
  selection,
  selectedStep,
  onClose,
  onSelectStep,
  onOpenArtifact,
}: {
  inspection: RivetRunInspection;
  selection: TraceGraphSelection | null;
  selectedStep: RivetRunStep | null;
  onClose: () => void;
  onSelectStep?: (step: RivetRunStep) => void;
  onOpenArtifact?: (artifact: Record<string, unknown>) => void;
}) {
  const node =
    selection?.kind === "node"
      ? inspection.graph?.nodes.find((item) => item.node_id === selection.id)
      : null;
  const connection =
    selection?.kind === "connection"
      ? inspection.graph?.connections.find(
          (item) => item.connection_id === selection.id,
        )
      : null;
  const steps = selectedStep
    ? [selectedStep]
    : node
      ? inspection.steps.filter((step) => step.node_id === node.node_id)
      : [];
  if (!selection && !selectedStep) return null;
  return (
    <aside
      className="workflow-trace__inspector"
      aria-label="Selected process detail"
    >
      <header>
        <div>
          <strong>
            {node?.label || connection?.label || selectedStep?.label}
          </strong>
          <span>
            {node?.node_type ||
              (connection ? "Connection" : "Recorded attempt")}
          </span>
        </div>
        <button
          type="button"
          aria-label="Close process detail"
          onClick={onClose}
        >
          X
        </button>
      </header>
      {connection && (
        <>
          <p>
            {connection.source_node_id} to {connection.target_node_id}:{" "}
            {connection.source_port} to {connection.target_port}
          </p>
          {(connection.traversals || []).length > 0 && (
            <section aria-label="Recorded connection traversals">
              <h3>Recorded traversals</h3>
              <ol>
                {(connection.traversals || []).map((traversal) => {
                  const source = inspection.steps.find(
                    (step) => step.step_id === traversal.source_step_id,
                  );
                  const target = inspection.steps.find(
                    (step) => step.step_id === traversal.target_step_id,
                  );
                  return (
                    <li key={traversal.traversal_id}>
                      Attempt {traversal.source_attempt} to attempt{" "}
                      {traversal.target_attempt}
                      {target && onSelectStep && (
                        <button
                          type="button"
                          className="workflow-trace__evidence-link"
                          onClick={() => onSelectStep(target)}
                        >
                          Open {target.label}
                        </button>
                      )}
                      {source && <small>From {source.label}</small>}
                    </li>
                  );
                })}
              </ol>
            </section>
          )}
        </>
      )}
      {node?.prompt && (
        <details>
          <summary>Executed prompt</summary>
          <pre>{node.prompt}</pre>
        </details>
      )}
      {node && Object.keys(node.configuration).length > 0 && (
        <details>
          <summary>Recorded configuration</summary>
          <pre>{JSON.stringify(node.configuration, null, 2)}</pre>
        </details>
      )}
      {steps.map((step) => (
        <section key={step.step_id}>
          <h3>
            Attempt {step.attempt || 1}: {step.state}
          </h3>
          {step.reason_code && <p>{step.reason_code}</p>}
          <details>
            <summary>Inputs ({step.inputs.length})</summary>
            {step.inputs.map((result) => (
              <RivetRunResult key={result.result_id} result={result} />
            ))}
            {!step.inputs.length && (
              <p>{step.input_state.replaceAll("-", " ")}</p>
            )}
          </details>
          <details>
            <summary>Outputs ({step.outputs.length})</summary>
            {step.outputs.map((result) => (
              <RivetRunResult
                key={result.result_id}
                result={result}
                onOpenArtifact={onOpenArtifact}
              />
            ))}
            {!step.outputs.length && (
              <p>{step.output_state.replaceAll("-", " ")}</p>
            )}
          </details>
          <details>
            <summary>Technical activity</summary>
            <dl>
              <dt>Node</dt>
              <dd>{step.node_id || "Unavailable"}</dd>
              <dt>Tool</dt>
              <dd>{step.qualified_tool_name || "Unavailable"}</dd>
              <dt>Trace</dt>
              <dd>{step.trace_id || "Unavailable"}</dd>
            </dl>
          </details>
        </section>
      ))}
      {connection && !steps.length && !(connection.traversals || []).length && (
        <p className="workflow-trace__empty">
          No explicit traversal was retained for this connection. Its configured
          relationship is shown without claiming that data crossed it.
        </p>
      )}
    </aside>
  );
}

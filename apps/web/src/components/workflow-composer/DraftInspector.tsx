import type { DraftProjection } from "./draft-projection";
import type { WorkflowDraftValidation } from "../../services/workflow-drafts";

interface DraftInspectorProps {
  readonly projection: Readonly<DraftProjection>;
  readonly selectedSemanticId: string | null;
  readonly validation: WorkflowDraftValidation | null;
}

export function DraftInspector({ projection, selectedSemanticId, validation }: DraftInspectorProps): React.ReactNode {
  const selectedBlock = projection.phases
    .flatMap((phase) => phase.blocks)
    .find((block) => block.semanticId === selectedSemanticId);

  return (
    <aside className="workflow-composer__inspector" data-testid="workflow-composer-inspector" aria-label="Draft inspector">
      <header>
        <p className="workflow-composer__eyebrow">Inspector</p>
        <h2>{selectedSemanticId === null ? "Nothing selected" : selectedBlock?.title ?? "Selected concept"}</h2>
        <code>{selectedSemanticId ?? "Select a concept in the diagram"}</code>
      </header>
      <details open>
        <summary>Definition</summary>
        {selectedBlock ? (
          <dl>
            <dt>Role</dt><dd>{selectedBlock.role}</dd>
            <dt>Purpose</dt><dd>{selectedBlock.purpose}</dd>
            <dt>Phase</dt><dd><code>{selectedBlock.phase_id}</code></dd>
            <dt>Position</dt><dd>{selectedBlock.position.x}, {selectedBlock.position.y}</dd>
          </dl>
        ) : <p>Select a workflow block to inspect its definition.</p>}
      </details>
      <details>
        <summary>Ports &amp; relationships</summary>
        {selectedBlock ? (
          <dl>
            <dt>Inputs</dt><dd>{selectedBlock.inputs.map((port) => port.semanticId).join(", ") || "None declared"}</dd>
            <dt>Outputs</dt><dd>{selectedBlock.outputs.map((port) => port.semanticId).join(", ") || "None declared"}</dd>
            <dt>Gates</dt><dd>{selectedBlock.gates.map((gate) => gate.semanticId).join(", ") || "None declared"}</dd>
            <dt>Artifacts</dt><dd>{selectedBlock.artifacts.map((artifact) => artifact.semanticId).join(", ") || "None declared"}</dd>
          </dl>
        ) : <p>No relationships selected.</p>}
      </details>
      <details>
        <summary>Validation</summary>
        {validation === null ? (
          <p><strong>Not checked</strong> · validate this working copy before saving.</p>
        ) : validation.valid ? (
          <p className="workflow-composer__valid"><strong>Validation passed</strong> · all {projection.phases.flatMap((phase) => phase.blocks).length} block positions and declared relationships resolve.</p>
        ) : (
          <div className="workflow-composer__invalid">
            <strong>Validation found {validation.diagnostics.length} diagnostic{validation.diagnostics.length === 1 ? "" : "s"}</strong>
            <ul>
              {validation.diagnostics.map((diagnostic) => (
                <li key={`${diagnostic.code}:${diagnostic.path}`}>
                  <code>{diagnostic.code}</code> — {diagnostic.explanation} {diagnostic.correction}
                </li>
              ))}
            </ul>
          </div>
        )}
      </details>
    </aside>
  );
}

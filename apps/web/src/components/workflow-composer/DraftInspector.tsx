import { useEffect, useMemo, useState } from "react";

import type { WorkflowDraftValidation } from "../../services/workflow-drafts";
import type { DraftCanvasIntent, DraftDiagnostic } from "./draft-intents";
import type { DraftProjection } from "./draft-projection";

interface DraftInspectorProps {
  readonly projection: Readonly<DraftProjection>;
  readonly selectedSemanticId: string | null;
  readonly validation: WorkflowDraftValidation | null;
  readonly diagnostics: readonly DraftDiagnostic[];
  readonly onIntent: (intent: DraftCanvasIntent) => void;
}

export function DraftInspector({
  projection,
  selectedSemanticId,
  validation,
  diagnostics,
  onIntent,
}: DraftInspectorProps): React.ReactNode {
  const blocks = useMemo(
    () => projection.phases.flatMap((phase) => phase.blocks),
    [projection],
  );
  const ports = useMemo(
    () => blocks.flatMap((block) => [...block.inputs, ...block.outputs]),
    [blocks],
  );
  const selectedBlock = blocks.find(
    (block) => block.semanticId === selectedSemanticId,
  );
  const [title, setTitle] = useState("");
  const [purpose, setPurpose] = useState("");
  const [x, setX] = useState("0");
  const [y, setY] = useState("0");
  const [sourcePortId, setSourcePortId] = useState(
    ports.find((port) => port.direction === "output")?.semanticId ?? "",
  );
  const [targetPortId, setTargetPortId] = useState(
    ports.find((port) => port.direction === "input")?.semanticId ?? "",
  );
  const [newPhaseId, setNewPhaseId] = useState(
    projection.phases[0]?.semanticId ?? "",
  );
  const [newRole, setNewRole] = useState<
    "input" | "work" | "review" | "release"
  >("work");
  const [newBlockX, setNewBlockX] = useState("0");
  const [newBlockY, setNewBlockY] = useState("0");

  useEffect(() => {
    setTitle(selectedBlock?.title ?? "");
    setPurpose(selectedBlock?.purpose ?? "");
    setX(String(selectedBlock?.position.x ?? 0));
    setY(String(selectedBlock?.position.y ?? 0));
  }, [selectedBlock]);

  const gate = selectedBlock?.gates[0];
  const feedback =
    gate === undefined
      ? undefined
      : projection.feedbackPaths.find(
          (item) => item.from_gate_id === gate.semanticId,
        );
  const artifact = selectedBlock?.artifacts[0];
  const [gateCondition, setGateCondition] = useState("");
  const [gateProceed, setGateProceed] = useState("");
  const [gateRevise, setGateRevise] = useState("");
  const [feedbackReason, setFeedbackReason] = useState("");
  const [artifactTitle, setArtifactTitle] = useState("");
  const [artifactType, setArtifactType] = useState("type.intended-output");
  const [artifactDescription, setArtifactDescription] = useState("");

  useEffect(() => {
    setGateCondition(gate?.condition ?? "Describe the acceptance condition.");
    setGateProceed(
      gate?.proceed_target_block_id ?? blocks[0]?.semanticId ?? "",
    );
    setGateRevise(gate?.revise_target_block_id ?? blocks[0]?.semanticId ?? "");
    setFeedbackReason(
      feedback?.label ?? "Revise the named work to satisfy this gate.",
    );
    setArtifactTitle(artifact?.title ?? "Intended output");
    setArtifactType(artifact?.artifact_type_id ?? "type.intended-output");
    setArtifactDescription(
      artifact?.description ??
        "Declared intended output; no artifact is executed.",
    );
  }, [artifact, blocks, feedback, gate]);

  return (
    <aside
      className="workflow-composer__inspector"
      data-testid="workflow-composer-inspector"
      aria-label="Draft inspector"
    >
      <header>
        <p className="workflow-composer__eyebrow">Inspector</p>
        <h2>
          {selectedSemanticId === null
            ? "Nothing selected"
            : (selectedBlock?.title ?? "Selected concept")}
        </h2>
        <code>{selectedSemanticId ?? "Select a concept in the diagram"}</code>
      </header>

      <details open>
        <summary>Definition &amp; position</summary>
        {selectedBlock ? (
          <div className="workflow-inspector__form">
            <label>
              Title
              <input
                data-testid="workflow-inspector-title"
                maxLength={500}
                value={title}
                onChange={(event) => setTitle(event.currentTarget.value)}
              />
            </label>
            <label>
              Purpose
              <textarea
                data-testid="workflow-inspector-purpose"
                maxLength={500}
                rows={3}
                value={purpose}
                onChange={(event) => setPurpose(event.currentTarget.value)}
              />
            </label>
            <button
              data-testid="workflow-inspector-apply-definition"
              type="button"
              onClick={() =>
                onIntent({
                  type: "edit-block",
                  semanticId: selectedBlock.semanticId,
                  title,
                  purpose,
                })
              }
            >
              Apply definition
            </button>
            <div className="workflow-inspector__row">
              <label>
                X
                <input
                  data-testid="workflow-inspector-position-x"
                  type="number"
                  min={-10000}
                  max={10000}
                  value={x}
                  onChange={(event) => setX(event.currentTarget.value)}
                />
              </label>
              <label>
                Y
                <input
                  data-testid="workflow-inspector-position-y"
                  type="number"
                  min={-10000}
                  max={10000}
                  value={y}
                  onChange={(event) => setY(event.currentTarget.value)}
                />
              </label>
            </div>
            <button
              data-testid="workflow-inspector-apply-position"
              type="button"
              onClick={() =>
                onIntent({
                  type: "move-block",
                  semanticId: selectedBlock.semanticId,
                  x: Number(x),
                  y: Number(y),
                })
              }
            >
              Apply position
            </button>
            <button
              className="workflow-inspector__danger"
              data-testid="workflow-inspector-delete-block"
              type="button"
              onClick={() =>
                onIntent({
                  type: "delete-concept",
                  semanticId: selectedBlock.semanticId,
                })
              }
            >
              Delete selected block
            </button>
          </div>
        ) : (
          <p>Select a workflow block to inspect and edit its definition.</p>
        )}
      </details>

      <details open>
        <summary>Connections</summary>
        <div className="workflow-inspector__form">
          <label>
            Source port
            <select
              data-testid="workflow-connection-source"
              value={sourcePortId}
              onChange={(event) => setSourcePortId(event.currentTarget.value)}
            >
              {ports.map((port) => (
                <option
                  key={`source-${port.semanticId}`}
                  value={port.semanticId}
                >
                  {port.name} · {port.direction} · {port.value_type_id}
                </option>
              ))}
            </select>
          </label>
          <label>
            Target port
            <select
              data-testid="workflow-connection-target"
              value={targetPortId}
              onChange={(event) => setTargetPortId(event.currentTarget.value)}
            >
              {ports.map((port) => (
                <option
                  key={`target-${port.semanticId}`}
                  value={port.semanticId}
                >
                  {port.name} · {port.direction} · {port.value_type_id}
                </option>
              ))}
            </select>
          </label>
          <button
            data-testid="workflow-connection-create"
            type="button"
            disabled={!sourcePortId || !targetPortId}
            onClick={() =>
              onIntent({
                type: "create-connection",
                sourcePortId,
                targetPortId,
              })
            }
          >
            Create connection
          </button>
        </div>
      </details>

      <details>
        <summary>Gate, feedback &amp; artifact</summary>
        {selectedBlock ? (
          <div className="workflow-inspector__form">
            <label>
              Gate condition
              <input
                data-testid="workflow-gate-condition"
                maxLength={500}
                value={gateCondition}
                onChange={(event) =>
                  setGateCondition(event.currentTarget.value)
                }
              />
            </label>
            <label>
              Proceed target
              <select
                data-testid="workflow-gate-proceed"
                value={gateProceed}
                onChange={(event) => setGateProceed(event.currentTarget.value)}
              >
                {blocks.map((block) => (
                  <option
                    key={`proceed-${block.semanticId}`}
                    value={block.semanticId}
                  >
                    {block.title}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Revise target
              <select
                data-testid="workflow-gate-revise"
                value={gateRevise}
                onChange={(event) => setGateRevise(event.currentTarget.value)}
              >
                {blocks.map((block) => (
                  <option
                    key={`revise-${block.semanticId}`}
                    value={block.semanticId}
                  >
                    {block.title}
                  </option>
                ))}
              </select>
            </label>
            <button
              data-testid="workflow-gate-apply"
              type="button"
              onClick={() =>
                onIntent(
                  gate
                    ? {
                        type: "edit-gate",
                        semanticId: gate.semanticId,
                        condition: gateCondition,
                        proceedTargetBlockId: gateProceed,
                        reviseTargetBlockId: gateRevise,
                      }
                    : {
                        type: "create-gate",
                        ownerBlockId: selectedBlock.semanticId,
                        condition: gateCondition,
                        proceedTargetBlockId: gateProceed,
                        reviseTargetBlockId: gateRevise,
                      },
                )
              }
            >
              {gate ? "Apply gate" : "Create gate and feedback"}
            </button>
            {feedback && (
              <>
                <label>
                  Feedback reason
                  <textarea
                    data-testid="workflow-feedback-reason"
                    maxLength={500}
                    rows={2}
                    value={feedbackReason}
                    onChange={(event) =>
                      setFeedbackReason(event.currentTarget.value)
                    }
                  />
                </label>
                <button
                  data-testid="workflow-feedback-apply"
                  type="button"
                  onClick={() =>
                    onIntent({
                      type: "edit-feedback",
                      semanticId: feedback.semanticId,
                      toBlockId: gateRevise,
                      reason: feedbackReason,
                    })
                  }
                >
                  Apply feedback
                </button>
              </>
            )}
            <label>
              Artifact title
              <input
                data-testid="workflow-artifact-title"
                maxLength={500}
                value={artifactTitle}
                onChange={(event) =>
                  setArtifactTitle(event.currentTarget.value)
                }
              />
            </label>
            <label>
              Artifact type
              <input
                data-testid="workflow-artifact-type"
                maxLength={96}
                value={artifactType}
                onChange={(event) => setArtifactType(event.currentTarget.value)}
              />
            </label>
            <label>
              Artifact description
              <textarea
                data-testid="workflow-artifact-description"
                maxLength={500}
                rows={2}
                value={artifactDescription}
                onChange={(event) =>
                  setArtifactDescription(event.currentTarget.value)
                }
              />
            </label>
            <button
              data-testid="workflow-artifact-apply"
              type="button"
              onClick={() =>
                onIntent(
                  artifact
                    ? {
                        type: "edit-intended-artifact",
                        semanticId: artifact.semanticId,
                        title: artifactTitle,
                        artifactTypeId: artifactType,
                        description: artifactDescription,
                      }
                    : {
                        type: "create-intended-artifact",
                        ownerBlockId: selectedBlock.semanticId,
                        title: artifactTitle,
                        artifactTypeId: artifactType,
                        description: artifactDescription,
                      },
                )
              }
            >
              {artifact ? "Apply artifact" : "Create intended artifact"}
            </button>
          </div>
        ) : (
          <p>
            Select a block to author its gate, feedback, and intended artifact
            declarations.
          </p>
        )}
      </details>

      <details>
        <summary>Add block</summary>
        <div className="workflow-inspector__form">
          <label>
            Phase
            <select
              data-testid="workflow-block-create-phase"
              value={newPhaseId}
              onChange={(event) => setNewPhaseId(event.currentTarget.value)}
            >
              {projection.phases.map((phase) => (
                <option key={phase.semanticId} value={phase.semanticId}>
                  {phase.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Role
            <select
              data-testid="workflow-block-create-role"
              value={newRole}
              onChange={(event) =>
                setNewRole(event.currentTarget.value as typeof newRole)
              }
            >
              {["input", "work", "review", "release"].map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </label>
          <div className="workflow-inspector__row">
            <label>
              X
              <input
                data-testid="workflow-block-create-x"
                type="number"
                value={newBlockX}
                onChange={(event) => setNewBlockX(event.currentTarget.value)}
              />
            </label>
            <label>
              Y
              <input
                data-testid="workflow-block-create-y"
                type="number"
                value={newBlockY}
                onChange={(event) => setNewBlockY(event.currentTarget.value)}
              />
            </label>
          </div>
          <button
            data-testid="workflow-block-create"
            type="button"
            onClick={() =>
              onIntent({
                type: "create-block",
                phaseId: newPhaseId,
                role: newRole,
                x: Number(newBlockX),
                y: Number(newBlockY),
              })
            }
          >
            Create provisional block
          </button>
        </div>
      </details>

      <details>
        <summary>Validation</summary>
        {diagnostics.length > 0 ? (
          <div className="workflow-composer__invalid">
            <p>
              <strong>
                {validation !== null && !validation.valid
                  ? "Validation failed"
                  : "Edit rejected"}
              </strong>{" "}
              · resolve the named diagnostic; the last valid draft remains
              active.
            </p>
            <ul>
              {diagnostics.map((item) => (
                <li key={`${item.code}:${item.path}`}>
                  <code>{item.code}</code> — {item.explanation}{" "}
                  {item.correction}
                </li>
              ))}
            </ul>
          </div>
        ) : validation === null ? (
          <p>
            <strong>Not checked</strong> · validate this working copy before
            saving.
          </p>
        ) : validation.valid ? (
          <p className="workflow-composer__valid">
            <strong>Validation passed</strong> · all {blocks.length} block
            positions and declared relationships resolve.
          </p>
        ) : (
          <p className="workflow-composer__invalid">
            <strong>
              Validation found {validation.diagnostics.length} diagnostic
              {validation.diagnostics.length === 1 ? "" : "s"}
            </strong>
          </p>
        )}
      </details>
    </aside>
  );
}

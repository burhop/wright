import { useState } from "react";
import type { RecoveryBlock, RecoveryWorkflow } from "./model";
import { RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY } from "./model";
import type { RecoveryCommand } from "./command-system";
import {
  normalizeWorkflowInstructionOverride,
  type WorkflowInstructionOverride,
} from "./workflow-instructions";
import { workflowInstructionPreview } from "./WorkflowInstructionsEditor";
import { isMcpBlock } from "./mcp-settings";
import { imageOutput } from "./image-output";

export function stepInstructionOverride(
  block: RecoveryBlock,
): WorkflowInstructionOverride | null {
  const retained = block.configuration[RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY];
  if (retained === undefined) return null;
  const value = JSON.parse(String(retained)).instruction_override;
  return value === undefined
    ? null
    : normalizeWorkflowInstructionOverride(value);
}

export function StepInstructionsEditor({
  block,
  workflow,
  readOnly,
  onApply,
  onOpenWorkflowInstructions,
}: {
  block: RecoveryBlock;
  workflow: RecoveryWorkflow;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
  onOpenWorkflowInstructions: () => void;
}) {
  let original: WorkflowInstructionOverride | null = null;
  let initialError = "";
  try {
    original = stepInstructionOverride(block);
  } catch (error) {
    initialError =
      error instanceof Error
        ? error.message
        : "Inspect the stored instruction override.";
  }
  const [policy, setPolicy] = useState(
    original?.assumption_policy ?? "inherit",
  );
  const [text, setText] = useState(original?.text ?? "");
  const [mode, setMode] = useState(original?.mode ?? "append");
  const [error, setError] = useState(initialError);
  const role = isMcpBlock(block)
    ? "mcp-task"
    : imageOutput(block)
      ? "image-generation"
      : "workflow-task";
  const profile = workflow.metadata.instructions;
  const value = {
    origin: "step-author",
    roles: original?.roles ?? [role],
    mode,
    text,
    assumption_policy: policy === "inherit" ? null : policy,
  };
  const preview = profile
    ? workflowInstructionPreview(
        {
          ...profile,
          layers: [...profile.layers, value as WorkflowInstructionOverride],
        },
        role,
      )
    : null;
  const apply = () => {
    if (readOnly || !profile) return;
    try {
      const instructionOverride =
        !text.trim() && policy === "inherit" && mode === "append"
          ? null
          : normalizeWorkflowInstructionOverride(value);
      if (
        !onApply([
          {
            kind: "set_block_object_configuration",
            blockId: block.id,
            key: "instruction_override",
            value: instructionOverride,
          },
        ])
      )
        throw new Error(
          "Instructions were not applied. Inspect workflow diagnostics.",
        );
      setError("");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Check this step's instructions.",
      );
    }
  };
  return (
    <details
      className="recovery-technical-details wright-instruction-editor"
      data-testid="workflow-step-instructions"
    >
      <summary data-testid="workflow-step-instructions-toggle">
        Step instruction settings
      </summary>
      {!profile ? (
        <>
          <p>
            This legacy workflow has no saved instruction profile. Make workflow
            instructions explicit before adding a step override.
          </p>
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            data-testid="workflow-step-instructions-workflow"
            onClick={onOpenWorkflowInstructions}
          >
            Inspect workflow instructions
          </button>
        </>
      ) : (
        <>
          <p>
            This step inherits the saved workflow profile. Changes below travel
            with this workflow revision and apply to {value.roles.join(", ")}.
          </p>
          <label>
            Step assumption policy
            <select
              data-testid="workflow-step-instructions-policy"
              value={policy}
              disabled={readOnly}
              onChange={(event) =>
                setPolicy(event.target.value as typeof policy)
              }
            >
              <option value="inherit">Inherit workflow policy</option>
              <option value="document_reasonable">
                Document reasonable assumptions
              </option>
              <option value="require_specified">
                Require specified values
              </option>
            </select>
          </label>
          <label>
            Additional step guidance
            <textarea
              data-testid="workflow-step-instructions-guidance"
              rows={4}
              value={text}
              disabled={readOnly}
              onChange={(event) => setText(event.target.value)}
            />
          </label>
          <label>
            Step guidance mode
            <select
              data-testid="workflow-step-instructions-mode"
              value={mode}
              disabled={readOnly}
              onChange={(event) => setMode(event.target.value as typeof mode)}
            >
              <option value="append">Append to workflow instructions</option>
              <option value="replace">
                Replace instructions for this role
              </option>
            </select>
          </label>
          {preview && (
            <details>
              <summary data-testid="workflow-step-instructions-preview-toggle">
                Effective instructions for this step
              </summary>
              <p>Origins: {preview.origins.join(" → ")}</p>
              <p>Assumption policy: {preview.policy}</p>
              <textarea
                aria-label="Effective step instruction template"
                data-testid="workflow-step-instructions-preview"
                rows={8}
                value={preview.text}
                readOnly
              />
            </details>
          )}
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            data-testid="workflow-step-instructions-apply"
            disabled={readOnly}
            onClick={apply}
          >
            Apply step instructions
          </button>
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </details>
  );
}

import { useState } from "react";
import type { RecoveryCommand } from "./command-system";
import { type RecoveryBlock, type RecoveryWorkflow } from "./model";
import { sourceKey } from "./prompt-settings";
import {
  declarationJson,
  humanInputDeclarationCommands,
  inputDeclarationCommands,
  interactionObject,
} from "./interaction-settings";

const pretty = (value: unknown) => JSON.stringify(value, null, 2);
function initialObject(
  block: RecoveryBlock,
  key: "interaction_input" | "human_interaction",
) {
  try {
    return { object: interactionObject(block, key), error: "" };
  } catch (error) {
    return {
      object: null,
      error:
        error instanceof Error
          ? error.message
          : "Inspect the stored declaration.",
    };
  }
}

/** Edit declarations in the accepted process, never values for an existing run. */
export function InputDeclarationEditor({
  block,
  readOnly,
  onApply,
}: {
  block: RecoveryBlock;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
}) {
  const initial = initialObject(block, "interaction_input");
  const [text, setText] = useState(
    pretty(
      initial.object ?? {
        version: 1,
        value_schema: {
          type:
            block.configuration.input_mode === "workspace-file"
              ? "object"
              : "string",
        },
        required: true,
      },
    ),
  );
  const [error, setError] = useState(initial.error);
  const apply = () => {
    if (readOnly) return;
    try {
      if (onApply(inputDeclarationCommands(block, text))) setError("");
      else
        setError(
          "The declaration was not applied. Inspect the workflow diagnostics.",
        );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Check the input declaration.");
    }
  };
  return (
    <details
      className="recovery-technical-details"
      data-testid="workflow-input-declaration-editor"
      open={!!initial.object}
    >
      <summary data-testid="workflow-input-declaration-toggle">
        Input schema and defaults
      </summary>
      <p>
        Define what this process needs before it starts. Values entered in the
        working view belong to a run.
      </p>
      <label>
        Input declaration (JSON)
        <textarea
          data-testid="workflow-input-declaration-json"
          rows={12}
          value={text}
          disabled={readOnly}
          onChange={(event) => {
            setText(event.target.value);
            setError("");
          }}
        />
      </label>
      <p>
        Use value_schema for the value shape, required for readiness, and
        optional unit, frame and default fields. Preserve configured
        option_source bindings when editing.
      </p>
      <p>
        A declared default takes precedence over legacy input text. Wright
        checks supported schema, provider options and actual values before
        starting.
      </p>
      <button
        data-testid="workflow-input-declaration-apply"
        type="button"
        className="recovery-button recovery-button--secondary"
        disabled={readOnly}
        onClick={apply}
      >
        Apply input declaration
      </button>
      {initial.object && (
        <button
          data-testid="workflow-input-declaration-infer"
          type="button"
          className="recovery-button recovery-button--quiet"
          disabled={readOnly}
          onClick={() => {
            if (readOnly) return;
            if (
              onApply([
                {
                  kind: "set_block_object_configuration",
                  blockId: block.id,
                  key: "interaction_input",
                  value: null,
                },
              ])
            )
              setError("");
            else
              setError(
                "The declaration was not removed. Inspect the workflow diagnostics.",
              );
          }}
        >
          Use inferred input schema
        </button>
      )}
      {error && <p role="alert">{error}</p>}
    </details>
  );
}

export function HumanInputDeclarationEditor({
  block,
  workflow,
  readOnly,
  onApply,
}: {
  block: RecoveryBlock;
  workflow: RecoveryWorkflow;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
}) {
  const initial = initialObject(block, "human_interaction");
  const output = workflow.ports.find((port) =>
    block.outputPortIds.includes(port.id),
  );
  const [text, setText] = useState(
    pretty(
      initial.object ?? {
        version: 1,
        kind: "input",
        instructions: block.instructions,
        response_schema: {
          type: "object",
          properties: {},
          required: [],
          additionalProperties: false,
        },
        output_port: output ? sourceKey(output.id) : "",
      },
    ),
  );
  const [error, setError] = useState(initial.error);
  let current: Record<string, unknown> | null = null;
  try {
    current = declarationJson(text);
  } catch {
    /* Keep incomplete JSON editable. */
  }
  const changeInstructions = (instructions: string) => {
    if (current) {
      setText(pretty({ ...current, instructions }));
      setError("");
    }
  };
  const apply = () => {
    if (readOnly) return;
    try {
      if (onApply(humanInputDeclarationCommands(block, workflow, text)))
        setError("");
      else
        setError(
          "The declaration was not applied. Inspect the workflow diagnostics.",
        );
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Check the declared user input.",
      );
    }
  };
  return (
    <section
      className="recovery-prompt-editor"
      data-testid="workflow-human-input-editor"
    >
      <h3>Planned user input</h3>
      <p>
        This step pauses the same run for a structured response. Connect
        upstream evidence and the response output to the steps that use it.
      </p>
      {!initial.object && (
        <p role="status">
          This step is a draft. Define its instructions and response schema
          before running.
        </p>
      )}
      <label>
        Instructions for the user
        <textarea
          data-testid="workflow-human-input-instructions"
          rows={4}
          value={
            typeof current?.instructions === "string"
              ? current.instructions
              : ""
          }
          disabled={readOnly || !current}
          maxLength={8000}
          onChange={(event) => changeInstructions(event.target.value)}
        />
      </label>
      <label>
        Response declaration (JSON)
        <textarea
          data-testid="workflow-human-input-json"
          rows={15}
          value={text}
          disabled={readOnly}
          onChange={(event) => {
            setText(event.target.value);
            setError("");
          }}
        />
      </label>
      <p>
        Define the object response_schema with named properties and required
        fields. This is a planned input, separate from an approval or action.
      </p>
      <p>
        Wright validates supported schema and evidence connections before
        executing. Unattended steps cannot invent additional questions.
      </p>
      <button
        data-testid="workflow-human-input-apply"
        type="button"
        className="recovery-button recovery-button--secondary"
        disabled={readOnly}
        onClick={apply}
      >
        Apply response declaration
      </button>
      {error && <p role="alert">{error}</p>}
    </section>
  );
}

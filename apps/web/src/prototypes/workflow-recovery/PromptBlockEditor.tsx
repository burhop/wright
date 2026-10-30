import { configuredOutputs, outputConsumers } from "./output-contracts";
import { useState } from "react";
import { McpTaskOptions } from "./McpTaskOptions";
import { imageOutput, imageOutputCommands } from "./image-output";
import type { RecoveryCommand } from "./command-system";
import {
  findBlock,
  findPort,
  type RecoveryBlock,
  type RecoveryWorkflow,
} from "./model";
import {
  connectPromptCommands,
  connectReferenceCommands,
  isFinalPrompt,
  isImageSource,
  promptFilename,
  promptFormat,
  promptSourceCandidates,
  RESPONSE_FORMATS,
  savedResponsePublication,
  sourceKey,
  type ResponseFormat,
} from "./prompt-settings";

export function PromptBlockEditor({
  block,
  workflow,
  readOnly,
  onApply,
  sessionId,
}: {
  block: RecoveryBlock;
  workflow: RecoveryWorkflow;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
  sessionId?: string;
}) {
  const [message, setMessage] = useState("");
  const mode =
    block.configuration.prompt_source === "connection"
      ? "connection"
      : "inline";
  const format = promptFormat(block);
  const image = imageOutput(block);
  const cad = Boolean(
    block.configuration.cad || block.configuration.application_resource,
  );
  const declared = configuredOutputs(block, workflow);
  const ResponseOptions = cad ? "details" : "div";
  const final = isFinalPrompt(block, workflow) && !cad && !image;
  const saving = final || block.configuration.save_output === true;
  const publication = savedResponsePublication(block);
  const promptPort = workflow.ports.find(
    (port) =>
      port.ownerBlockId === block.id &&
      sourceKey(port.id) === block.configuration.prompt_input,
  );
  const edge = workflow.relationships.find(
    (edge) => edge.kind === "data" && edge.targetId === promptPort?.id,
  );
  const candidates = promptSourceCandidates(block, workflow);
  const imageCandidates = promptSourceCandidates(block, workflow, true).filter(
    (port) => isImageSource(port.id, workflow),
  );
  const imageEdge = workflow.relationships.find(
    (edge) =>
      block.inputPortIds.includes(edge.targetId) &&
      isImageSource(edge.sourceId, workflow),
  );
  const config = (key: string, value: string | boolean) =>
    onApply([
      { kind: "set_block_configuration", blockId: block.id, key, value },
    ]);
  const connections = workflow.relationships.filter(
    (edge) =>
      edge.kind === "data" &&
      (block.inputPortIds.includes(edge.targetId) ||
        block.outputPortIds.includes(edge.sourceId)),
  );
  const choosePrompt = (id: string) => {
    try {
      onApply(connectPromptCommands(block, workflow, id));
      setMessage("");
    } catch (error) {
      setMessage(String(error));
    }
  };
  return (
    <section
      className="recovery-prompt-editor"
      data-testid="workflow-recovery-prompt-editor"
    >
      <label>
        Prompt source
        <select
          data-testid="workflow-recovery-prompt-source"
          value={mode}
          disabled={readOnly}
          onChange={(event) => {
            const commands: RecoveryCommand[] =
              event.target.value === "inline"
                ? connectPromptCommands(block, workflow, "")
                : [];
            onApply([
              ...commands,
              {
                kind: "set_block_configuration",
                blockId: block.id,
                key: "prompt_source",
                value: event.target.value,
              },
            ]);
          }}
        >
          <option value="inline">Write here</option>
          <option value="connection">From another block</option>
        </select>
      </label>
      {mode === "inline" ? (
        <label className="recovery-prompt-editor__prompt">
          Prompt
          <textarea
            rows={7}
            data-testid={`workflow-recovery-block-instructions-${block.id}`}
            value={block.instructions}
            readOnly={readOnly}
            onChange={(event) =>
              onApply([
                {
                  kind: "set_block_definition",
                  blockId: block.id,
                  patch: { instructions: event.target.value },
                },
              ])
            }
            placeholder="What should this step do?"
          />
        </label>
      ) : (
        <label>
          Prompt from
          <select
            data-testid="workflow-recovery-prompt-from"
            value={edge?.sourceId ?? ""}
            disabled={readOnly}
            onChange={(event) => choosePrompt(event.target.value)}
          >
            <option value="">Choose an upstream output</option>
            {candidates.map((port) => (
              <option key={port.id} value={port.id}>
                {findBlock(workflow, port.ownerBlockId)?.title} · {port.name}
              </option>
            ))}
          </select>
          <small>The complete response becomes this step’s prompt.</small>
          {!edge && (
            <span className="recovery-prompt-editor__error">
              Choose a source before running.
            </span>
          )}
        </label>
      )}
      <label>
        Reference image · optional
        <select
          data-testid="workflow-recovery-reference-image"
          value={imageEdge?.sourceId ?? ""}
          disabled={readOnly}
          onChange={(event) =>
            onApply(
              event.target.value
                ? connectReferenceCommands(
                    block,
                    workflow,
                    event.target.value,
                    workflow.ports.find(
                      (port) =>
                        port.ownerBlockId === block.id &&
                        port.name === "Reference image",
                    )?.id,
                  )
                : imageEdge
                  ? [{ kind: "disconnect", relationshipId: imageEdge.id }]
                  : [],
            )
          }
        >
          <option value="">Choose an upstream image</option>
          {imageCandidates.map((port) => (
            <option key={port.id} value={port.id}>
              {findBlock(workflow, port.ownerBlockId)?.title} · {port.name}
            </option>
          ))}
        </select>
        <small>
          Connect an image export or uploaded image to the Reference image
          socket. Keep the task instructions in Prompt.
        </small>
      </label>
      {cad && declared.size > 0 && (
        <section
          className="recovery-output-promises"
          aria-label="Configured outputs"
        >
          <b>Outputs from this task</b>
          <ul>
            {block.outputPortIds
              .filter((id) => declared.has(sourceKey(id)))
              .map((id) => (
                <li key={id}>
                  {declared.get(sourceKey(id))!.name}
                  {outputConsumers(workflow, id).length > 0
                    ? ` → ${outputConsumers(workflow, id).join(", ")}`
                    : ""}
                </li>
              ))}
          </ul>
          <small>
            Set file formats in Exports below. Wright produces those files after
            the task, even when you edit the prompt.
          </small>
        </section>
      )}
      {block.configuration.authoring_template === "mcp-task" && (
        <McpTaskOptions
          block={block}
          workflow={workflow}
          sessionId={sessionId}
          readOnly={readOnly}
          onApply={onApply}
        />
      )}
      <ResponseOptions className="recovery-response-options">
        {cad && <summary>Activity summary · optional</summary>}
        <label>
          Response format
          <select
            data-testid="workflow-recovery-response-format"
            value={image ? `image-${image.format}` : format}
            disabled={readOnly}
            onChange={(event) => {
              const imageFormat =
                event.target.value === "image-png"
                  ? "png"
                  : event.target.value === "image-jpeg"
                    ? "jpeg"
                    : null;
              if (imageFormat || image) {
                try {
                  const filename =
                    (image?.path ?? "render.png").replace(/\.[^/.]+$/, "") +
                    (imageFormat === "jpeg" ? ".jpg" : ".png");
                  const commands = imageOutputCommands(
                    block,
                    workflow,
                    imageFormat
                      ? { format: imageFormat, path: filename, port: "" }
                      : null,
                  );
                  if (imageFormat) {
                    onApply(commands);
                    setMessage("");
                    return;
                  }
                  onApply([
                    ...commands,
                    {
                      kind: "set_block_configuration",
                      blockId: block.id,
                      key: "output_format",
                      value: event.target.value,
                    },
                    {
                      kind: "set_block_configuration",
                      blockId: block.id,
                      key: "output_filename",
                      value: `response${RESPONSE_FORMATS[event.target.value as ResponseFormat]}`,
                    },
                  ]);
                  setMessage("");
                } catch (error) {
                  setMessage(
                    error instanceof Error ? error.message : String(error),
                  );
                }
                return;
              }
              const next = event.target.value as ResponseFormat;
              const filename =
                promptFilename(block).replace(/\.[^/.]+$/, "") +
                RESPONSE_FORMATS[next];
              onApply([
                {
                  kind: "set_block_configuration",
                  blockId: block.id,
                  key: "output_format",
                  value: next,
                },
                {
                  kind: "set_block_configuration",
                  blockId: block.id,
                  key: "output_filename",
                  value: filename,
                },
              ]);
            }}
          >
            <option value="text">Text</option>
            <option value="markdown">Markdown</option>
            <option value="html">HTML</option>
            <option value="json">JSON</option>
            {!cad && (
              <>
                <option value="image-png">Image (PNG)</option>
                <option value="image-jpeg">Image (JPEG)</option>
              </>
            )}
          </select>
          <small>
            {image
              ? block.configuration.mcp_server
                ? "The AI uses the selected MCP server to create the image. Wright verifies the resulting file."
                : "Wright sends the prompt and reference images to your configured AI connection, then saves and displays the returned image."
              : "Wright includes format instructions in the model request."}
          </small>
        </label>
        {image ? (
          <section>
            <label>
              Image filename
              <input
                data-testid="workflow-recovery-image-output-path"
                value={image.path}
                readOnly={readOnly}
                onChange={(event) => {
                  try {
                    onApply(
                      imageOutputCommands(block, workflow, {
                        ...image,
                        path: event.target.value,
                      }),
                    );
                    setMessage("");
                  } catch (error) {
                    setMessage(
                      error instanceof Error ? error.message : String(error),
                    );
                  }
                }}
              />
            </label>
            <small>
              The image is the saved result. Each run creates a new file; the
              activity summary remains in run details.
            </small>
            {block.configuration.authoring_template === "mcp-task" &&
              !block.configuration.mcp_server && (
                <button
                  type="button"
                  className="recovery-button recovery-button--secondary"
                  onClick={() =>
                    onApply(imageOutputCommands(block, workflow, image))
                  }
                  disabled={readOnly}
                >
                  Use configured AI for this image
                </button>
              )}
          </section>
        ) : (
          <section className="recovery-prompt-editor__save">
            <label className="recovery-prompt-editor__checkbox">
              <input
                type="checkbox"
                data-testid="workflow-recovery-save-response"
                checked={saving}
                disabled={readOnly || final || !!publication}
                onChange={(event) =>
                  config("save_output", event.target.checked)
                }
              />
              Save response to workspace
            </label>
            {final && (
              <small data-testid="workflow-recovery-terminal-save">
                Saved automatically because this is a final step.
              </small>
            )}
            {publication && (
              <small data-testid="workflow-recovery-response-publication">
                Saved response file output:{" "}
                <code>{publication.port ?? "not configured"}</code>. Edit the
                file output and save policy together in Source.
              </small>
            )}
            {saving && (
              <>
                <label>
                  File name or path
                  <input
                    data-testid="workflow-recovery-output-filename"
                    value={promptFilename(block)}
                    readOnly={readOnly}
                    onChange={(event) =>
                      config("output_filename", event.target.value)
                    }
                    placeholder={`report${RESPONSE_FORMATS[format]}`}
                  />
                </label>
                <label>
                  If the file exists
                  <select
                    data-testid="workflow-recovery-file-policy"
                    value={String(block.configuration.file_policy ?? "indexed")}
                    disabled={readOnly || !!publication}
                    onChange={(event) =>
                      config("file_policy", event.target.value)
                    }
                  >
                    <option value="indexed">Create an indexed file</option>
                    <option value="overwrite">Overwrite existing file</option>
                    {publication?.publishing && (
                      <option value={publication.policy}>
                        {publication.label}
                      </option>
                    )}
                  </select>
                </label>
                <small>
                  {publication
                    ? "The saved response becomes a file input for downstream work. Wright checks the output binding and run path before execution."
                    : block.configuration.file_policy === "overwrite"
                      ? "Replace the file after the response passes validation."
                      : `${promptFilename(block)} → ${promptFilename(block).replace(/(\.[^/.]+)$/, "-001$1")}`}
                </small>
              </>
            )}
          </section>
        )}
      </ResponseOptions>
      <details className="recovery-prompt-editor__connections">
        <summary data-testid="workflow-recovery-prompt-connections">
          Connections
          {connections.length ? ` · ${connections.length}` : " · optional"}
        </summary>
        {connections.length === 0 && <p>No connected blocks.</p>}
        {connections.map((connection) => {
          const incoming = block.inputPortIds.includes(connection.targetId);
          const other = findPort(
            workflow,
            incoming ? connection.sourceId : connection.targetId,
          );
          return (
            <div
              className="recovery-prompt-editor__connection"
              key={connection.id}
            >
              <span>
                {incoming
                  ? connection.targetId === promptPort?.id &&
                    mode === "connection"
                    ? "Prompt from"
                    : "Reference from"
                  : "Response to"}
                :{" "}
                {findBlock(workflow, other?.ownerBlockId ?? null)?.title ??
                  other?.name}
              </span>
              <button
                type="button"
                disabled={readOnly}
                aria-label={`Disconnect ${connection.label}`}
                data-testid={`workflow-recovery-prompt-disconnect-${connection.id}`}
                onClick={() =>
                  onApply([
                    { kind: "disconnect", relationshipId: connection.id },
                  ])
                }
              >
                ×
              </button>
            </div>
          );
        })}
        <label>
          Add reference material
          <select
            disabled={readOnly}
            value=""
            data-testid="workflow-recovery-add-reference"
            onChange={(event) =>
              onApply(
                connectReferenceCommands(block, workflow, event.target.value),
              )
            }
          >
            <option value="">Choose an upstream output</option>
            {promptSourceCandidates(block, workflow, true).map((port) => (
              <option key={port.id} value={port.id}>
                {findBlock(workflow, port.ownerBlockId)?.title} · {port.name}
              </option>
            ))}
          </select>
        </label>
      </details>
      {message && <p role="alert">{message}</p>}
    </section>
  );
}

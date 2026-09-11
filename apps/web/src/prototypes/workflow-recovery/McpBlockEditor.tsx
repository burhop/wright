import { useCallback, useEffect, useState } from "react";
import type { RecoveryCommand } from "./command-system";
import { findBlock, type RecoveryBlock, type RecoveryWorkflow } from "./model";
import {
  configureMcpTool,
  connectMcpInput,
  fieldSchema,
  listWorkflowMcpTools,
  workflowMcpServerName,
  mcpCandidates,
  readJson,
  type ToolSchema,
  type WorkflowMcpTool,
} from "./mcp-settings";
import { isFinalPrompt, promptFilename, sourceKey } from "./prompt-settings";

export function McpBlockEditor({
  block,
  workflow,
  sessionId,
  readOnly,
  onApply,
}: {
  block: RecoveryBlock;
  workflow: RecoveryWorkflow;
  sessionId?: string;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
}) {
  const [tools, setTools] = useState<WorkflowMcpTool[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [invalid, setInvalid] = useState<Record<string, string>>({});
  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      setTools(await listWorkflowMcpTools(sessionId));
      setMessage("");
    } catch (e) {
      setMessage(String(e));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);
  useEffect(() => {
    void load();
  }, [load]);
  const schema = readJson<ToolSchema>(block.configuration.mcp_input_schema, {});
  const args = readJson<Record<string, unknown>>(
    block.configuration.mcp_arguments,
    {},
  );
  const mapping = readJson<Record<string, string>>(
    block.configuration.mcp_argument_ports,
    {},
  );
  const mode = String(block.configuration.mcp_arguments_source ?? "fields");
  const selected = String(block.configuration.mcp_tool ?? "");
  const final = isFinalPrompt(block, workflow);
  const save = final || block.configuration.save_output === true;
  const config = (key: string, value: string | boolean) =>
    onApply([
      { kind: "set_block_configuration", blockId: block.id, key, value },
    ]);
  const setArgument = (name: string, value: unknown) => {
    const next = { ...args };
    if (value === undefined) delete next[name];
    else next[name] = value;
    config("mcp_arguments", JSON.stringify(next));
  };
  const connection = (key: string) => {
    const target = workflow.ports.find(
      (p) => p.ownerBlockId === block.id && sourceKey(p.id) === key,
    );
    if (!target) return null;
    const edge = workflow.relationships.find(
      (e) => e.kind === "data" && e.targetId === target.id,
    );
    return (
      <select
        aria-label={`Source for ${target.name}`}
        data-testid={`workflow-recovery-mcp-source-${key}`}
        value={edge?.sourceId ?? ""}
        disabled={readOnly}
        onChange={(e) =>
          onApply(connectMcpInput(block, workflow, target.id, e.target.value))
        }
      >
        <option value="">
          {key === block.configuration.mcp_arguments_input
            ? "Choose a JSON response"
            : "Enter below"}
        </option>
        {mcpCandidates(block, workflow, target).map((p) => (
          <option key={p.id} value={p.id}>
            {findBlock(workflow, p.ownerBlockId)?.title} · {p.name}
          </option>
        ))}
      </select>
    );
  };
  const field = (name: string, raw: ToolSchema) => {
    const s = fieldSchema(raw),
      key = Object.keys(mapping).find((k) => mapping[k] === name) ?? "";
    const target = workflow.ports.find(
      (p) => p.ownerBlockId === block.id && sourceKey(p.id) === key,
    );
    const linked = workflow.relationships.some(
      (e) => e.kind === "data" && e.targetId === target?.id,
    );
    const value = args[name];
    const id = `workflow-recovery-mcp-value-${name}`;
    return (
      <section className="recovery-mcp-field" key={name}>
        <label htmlFor={id}>
          {s.title ?? name.replaceAll("_", " ")}
          {schema.required?.includes(name) ? " *" : ""}
        </label>
        {connection(key)}
        {!linked &&
          (s.enum ? (
            <select
              id={id}
              data-testid={id}
              disabled={readOnly}
              value={value === undefined ? "" : JSON.stringify(value)}
              onChange={(e) =>
                setArgument(
                  name,
                  e.target.value === ""
                    ? undefined
                    : JSON.parse(e.target.value),
                )
              }
            >
              <option value="">Choose {name.replaceAll("_", " ")}</option>
              {s.enum.map((v) => (
                <option key={JSON.stringify(v)} value={JSON.stringify(v)}>
                  {String(v)}
                </option>
              ))}
            </select>
          ) : s.type === "boolean" ? (
            <select
              id={id}
              data-testid={id}
              disabled={readOnly}
              value={value === undefined ? "" : String(value)}
              onChange={(e) =>
                setArgument(
                  name,
                  e.target.value === "" ? undefined : e.target.value === "true",
                )
              }
            >
              <option value="">Not set</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          ) : s.type === "string" ? (
            <textarea
              id={id}
              rows={3}
              data-testid={id}
              value={String(value ?? "")}
              readOnly={readOnly}
              onChange={(e) => setArgument(name, e.target.value || undefined)}
            />
          ) : s.type === "number" || s.type === "integer" ? (
            <input
              id={id}
              type="number"
              step={s.type === "integer" ? 1 : "any"}
              data-testid={id}
              value={String(value ?? "")}
              readOnly={readOnly}
              onChange={(e) =>
                setArgument(
                  name,
                  e.target.value === "" ? undefined : Number(e.target.value),
                )
              }
            />
          ) : (
            <textarea
              id={id}
              rows={3}
              data-testid={id}
              value={
                invalid[name] ??
                (value === undefined ? "" : JSON.stringify(value, null, 2))
              }
              readOnly={readOnly}
              placeholder="JSON value"
              onChange={(e) => {
                try {
                  const v = e.target.value
                    ? JSON.parse(e.target.value)
                    : undefined;
                  setArgument(name, v);
                  setInvalid((current) => {
                    const next = { ...current };
                    delete next[name];
                    return next;
                  });
                } catch {
                  setArgument(name, e.target.value);
                  setInvalid((current) => ({
                    ...current,
                    [name]: e.target.value,
                  }));
                }
              }}
            />
          ))}
        {invalid[name] !== undefined && (
          <small role="alert">
            Enter valid JSON before leaving this field.
          </small>
        )}
        {raw.description && (
          <small className="recovery-mcp-description">{raw.description}</small>
        )}
      </section>
    );
  };
  const fields = Object.entries(schema.properties ?? {});
  return (
    <section
      className="recovery-prompt-editor recovery-mcp-editor"
      data-testid="workflow-recovery-mcp-editor"
    >
      <label>
        MCP tool
        <select
          data-testid="workflow-recovery-mcp-tool"
          value={selected}
          disabled={readOnly || loading}
          onChange={(e) => {
            const tool = tools.find((t) => t.name === e.target.value);
            if (tool) {
              onApply(configureMcpTool(block, workflow, tool));
              setInvalid({});
            }
          }}
        >
          <option value="">
            {loading ? "Loading available tools…" : "Choose a tool"}
          </option>
          {selected && !tools.some((t) => t.name === selected) && (
            <option value={selected}>
              {String(block.configuration.mcp_tool_title || "Selected tool")} ·
              unavailable
            </option>
          )}
          {tools.map((t) => (
            <option key={t.name} value={t.name}>
              {t.title} · {workflowMcpServerName(t)}
            </option>
          ))}
        </select>
      </label>
      <button
        type="button"
        data-testid="workflow-recovery-mcp-refresh"
        className="recovery-button recovery-button--secondary"
        disabled={loading}
        onClick={() => void load()}
      >
        Refresh tools
      </button>
      {tools.some(
        (t) =>
          t.name === selected &&
          t.schema_digest !== block.configuration.mcp_schema_digest,
      ) && (
        <button
          type="button"
          data-testid="workflow-recovery-mcp-update-definition"
          disabled={readOnly}
          onClick={() => {
            onApply(
              configureMcpTool(
                block,
                workflow,
                tools.find((t) => t.name === selected)!,
              ),
            );
            setMessage(
              "Tool definition updated. Review and configure its inputs before running.",
            );
          }}
        >
          Update changed tool inputs
        </button>
      )}
      {message && <p role="alert">{message}</p>}
      {!loading && !tools.length && !message && (
        <p>Enable an MCP server in Tool Registry to use its tools here.</p>
      )}
      {selected && (
        <>
          <label>
            Provide tool inputs
            <select
              data-testid="workflow-recovery-mcp-mode"
              value={mode}
              disabled={readOnly}
              onChange={(e) => {
                const commands: RecoveryCommand[] = workflow.relationships
                  .filter((edge) => block.inputPortIds.includes(edge.targetId))
                  .map((edge) => ({
                    kind: "disconnect",
                    relationshipId: edge.id,
                  }));
                commands.push({
                  kind: "set_block_configuration",
                  blockId: block.id,
                  key: "mcp_arguments_source",
                  value: e.target.value,
                });
                onApply(commands);
              }}
            >
              <option value="fields">Named inputs</option>
              <option value="connection">JSON from another block</option>
            </select>
          </label>
          {mode === "connection" ? (
            <>
              <label>
                Arguments
                {connection(String(block.configuration.mcp_arguments_input))}
              </label>
              <small>
                The connected JSON object supplies all tool arguments.
              </small>
              <details>
                <summary data-testid="workflow-recovery-mcp-expected-json">
                  Expected arguments
                </summary>
                <pre>{JSON.stringify(schema, null, 2)}</pre>
              </details>
            </>
          ) : (
            <>
              {fields
                .filter(([name]) => schema.required?.includes(name))
                .map(([n, s]) => field(n, s))}
              {fields.some(([n]) => !schema.required?.includes(n)) && (
                <details>
                  <summary data-testid="workflow-recovery-mcp-optional">
                    Optional inputs
                  </summary>
                  {fields
                    .filter(([n]) => !schema.required?.includes(n))
                    .map(([n, s]) => field(n, s))}
                </details>
              )}
              {!fields.length && <p>This tool has no input parameters.</p>}
            </>
          )}
          <section className="recovery-prompt-editor__save">
            <label className="recovery-prompt-editor__checkbox">
              <input
                type="checkbox"
                data-testid="workflow-recovery-mcp-save"
                checked={save}
                disabled={readOnly || final}
                onChange={(e) => config("save_output", e.target.checked)}
              />
              Save result to workspace
            </label>
            {final && (
              <small>Saved automatically because this is a final step.</small>
            )}
            {save && (
              <>
                <label>
                  Result file format
                  <select
                    data-testid="workflow-recovery-mcp-format"
                    value={String(block.configuration.output_format ?? "json")}
                    disabled={readOnly}
                    onChange={(e) =>
                      onApply([
                        {
                          kind: "set_block_configuration",
                          blockId: block.id,
                          key: "output_format",
                          value: e.target.value,
                        },
                        {
                          kind: "set_block_configuration",
                          blockId: block.id,
                          key: "output_filename",
                          value:
                            promptFilename(block).replace(/\.[^/.]+$/, "") +
                            (e.target.value === "text" ? ".txt" : ".json"),
                        },
                      ])
                    }
                  >
                    <option value="json">JSON result</option>
                    <option value="text">Text content</option>
                  </select>
                </label>
                <label>
                  File name or path
                  <input
                    data-testid="workflow-recovery-mcp-filename"
                    value={promptFilename(block)}
                    readOnly={readOnly}
                    onChange={(e) => config("output_filename", e.target.value)}
                  />
                </label>
                <label>
                  If the file exists
                  <select
                    data-testid="workflow-recovery-mcp-file-policy"
                    value={String(block.configuration.file_policy ?? "indexed")}
                    disabled={readOnly}
                    onChange={(e) => config("file_policy", e.target.value)}
                  >
                    <option value="indexed">Create an indexed file</option>
                    <option value="overwrite">Overwrite existing file</option>
                  </select>
                </label>
              </>
            )}
          </section>
          <small>
            Outputs: Result contains structured data; Text contains the tool’s
            readable response.
          </small>
          <details>
            <summary data-testid="workflow-recovery-mcp-tool-help">
              Tool help
            </summary>
            <p>{String(block.configuration.mcp_description ?? "")}</p>
          </details>
        </>
      )}
    </section>
  );
}

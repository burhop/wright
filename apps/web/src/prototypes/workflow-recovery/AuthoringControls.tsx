import { useEffect, useRef, useState } from "react";

import {
  AUTHORING_GROUPS,
  AUTHORING_TEMPLATES,
  authoringConfigurationCommands,
  authoringInputState,
  authoringReadiness,
} from "./authoring-objects";
import { listWorkflowMcpTools, type WorkflowMcpTool } from "./mcp-settings";
import { mcpServerChoices, type McpServerChoice } from "./mcp-server-blocks";
import type { RecoveryCommand } from "./command-system";
import {
  findBlock,
  findPort,
  recoveryAuthoringSectionKind,
  type RecoveryBlock,
  type RecoveryWorkflow,
} from "./model";
import { WorkflowObjectIcon } from "./WorkflowObjectIcon";
import { disconnectedProcessDiagnostic } from "./run-readiness";
import type { WorkspaceWorkflowSourceReadiness } from "../../services/workspace-service";

export interface AuthoringWorkspaceFile {
  path: string;
  name: string;
}

export function isServerScopedMcpTask(block: RecoveryBlock): boolean {
  return block.configuration.authoring_template === "mcp-task";
}

export function isExactMcpTool(block: RecoveryBlock): boolean {
  return block.configuration.authoring_template === "mcp-tool";
}

export function mcpTaskHasRequiredBinding(block: RecoveryBlock): boolean {
  if (isServerScopedMcpTask(block))
    return Boolean(block.configuration.mcp_server);
  if (isExactMcpTool(block))
    return (
      Boolean(block.configuration.mcp_server) &&
      Boolean(block.configuration.mcp_tool)
    );
  return false;
}

export function mcpTaskIsAvailable(
  block: RecoveryBlock,
  tools: readonly WorkflowMcpTool[],
): boolean {
  const server = String(block.configuration.mcp_server ?? "");
  const tool = String(block.configuration.mcp_tool ?? "");
  return tools.some(
    (item) =>
      item.server_id === server &&
      (isServerScopedMcpTask(block) || item.name === tool),
  );
}

export function AuthoringRunReadiness({
  workflow,
  saved,
  executionConnected,
  templateReadiness,
  sessionId,
  onRefreshTemplateReadiness,
  onSelect,
}: {
  readonly workflow: RecoveryWorkflow;
  readonly saved: boolean;
  readonly executionConnected: boolean;
  readonly templateReadiness?: WorkspaceWorkflowSourceReadiness | null;
  readonly sessionId?: string;
  readonly onRefreshTemplateReadiness?: () => void;
  readonly onSelect: (id: string) => void;
}) {
  const inputs = authoringReadiness(workflow);
  const processIssue = disconnectedProcessDiagnostic(workflow);
  const tasks = workflow.blocks.filter(
    (block) => recoveryAuthoringSectionKind(block) !== "input",
  );
  const isMcpTask = (block: RecoveryBlock) =>
    isServerScopedMcpTask(block) || isExactMcpTool(block);
  const unbound = tasks.filter((block) => {
    const hasMcpBinding = mcpTaskHasRequiredBinding(block);
    const requiresExecutionBinding =
      block.executionKind === "deterministic" || isMcpTask(block);
    return requiresExecutionBinding && !block.bindingId && !hasMcpBinding;
  });
  const mcpTasks = tasks.filter(isMcpTask);
  const mcpCheckKey = mcpTasks
    .map(
      (block) =>
        `${block.id}:${block.configuration.mcp_server ?? ""}:${block.configuration.mcp_tool ?? ""}`,
    )
    .join("|");
  const [mcpTools, setMcpTools] = useState<WorkflowMcpTool[] | null>(null);
  const [mcpCheckError, setMcpCheckError] = useState("");
  const [mcpCheckVersion, setMcpCheckVersion] = useState(0);
  useEffect(() => {
    let current = true;
    setMcpTools(null);
    setMcpCheckError("");
    if (!sessionId || mcpTasks.length === 0) return;
    void listWorkflowMcpTools(sessionId)
      .then((tools) => {
        if (current) setMcpTools(tools);
      })
      .catch(() => {
        if (current) setMcpCheckError("MCP availability could not be checked.");
      });
    return () => {
      current = false;
    };
  }, [mcpCheckKey, mcpCheckVersion, mcpTasks.length, sessionId]);
  const mcpStatus = (block: RecoveryBlock) => {
    if (!mcpTools) return mcpCheckError ? "check unavailable" : "checking";
    return mcpTaskIsAvailable(block, mcpTools) ? "available" : "unavailable";
  };
  const unavailableMcpCount = mcpTasks.filter((block) =>
    ["unavailable", "check unavailable"].includes(mcpStatus(block)),
  ).length;
  const attentionCount =
    inputs.inputs.filter((item) => item.status !== "configured").length +
    unbound.length +
    (processIssue ? 1 : 0) +
    (!saved ? 1 : 0) +
    (!executionConnected ? 1 : 0) +
    unavailableMcpCount +
    (templateReadiness &&
    !["not_template", "ready", "verified"].includes(templateReadiness.state)
      ? 1
      : 0);
  const templateStatus = templateReadiness
    ? templateReadiness.state === "not_template"
      ? "Hand-authored workflow"
      : templateReadiness.state === "setup_required"
        ? "Setup required"
        : templateReadiness.state === "reference"
          ? "Reference only"
          : templateReadiness.state === "unavailable"
            ? "Check unavailable"
            : templateReadiness.state === "verified"
              ? "Verified"
              : "Ready"
    : "Checking…";
  const templateStatusTone =
    !templateReadiness ||
    templateReadiness.state === "not_template" ||
    templateReadiness.state === "ready" ||
    templateReadiness.state === "verified"
      ? templateReadiness?.state === "not_template"
        ? "unknown"
        : "good"
      : "attention";
  return (
    <details
      className={`recovery-run-readiness ${attentionCount ? "has-attention" : "is-ready"}`}
      data-testid="workflow-recovery-run-readiness"
    >
      <summary data-testid="workflow-recovery-run-readiness-toggle">
        <b>Run readiness</b>
        <span>
          {attentionCount
            ? `${attentionCount} item${attentionCount === 1 ? "" : "s"} need attention`
            : "Authoring checks pass"}
        </span>
      </summary>
      <div className="recovery-run-readiness__grid">
        <ReadinessItem
          label="Inputs"
          value={`${inputs.configuredCount}/${inputs.totalCount} configured`}
          status={
            inputs.configuredCount === inputs.totalCount ? "good" : "attention"
          }
        />
        <ReadinessItem
          label="Process"
          value={processIssue ? "Disconnected groups" : "Connected"}
          status={processIssue ? "attention" : "good"}
          action={processIssue ? "Check graph" : undefined}
          onAction={
            processIssue
              ? () => onSelect(workflow.blocks[0]?.id ?? "")
              : undefined
          }
          actionTestId="workflow-recovery-readiness-process-action"
        />
        <ReadinessItem
          label="Saved definition"
          value={saved ? "Saved" : "Unsaved changes"}
          status={saved ? "good" : "attention"}
        />
        <ReadinessItem
          label="Run path"
          value={
            executionConnected ? "Connected · preflight required" : "Not wired"
          }
          status={executionConnected ? "unknown" : "attention"}
        />
        <ReadinessItem
          label="Template qualification"
          value={templateStatus}
          status={templateStatusTone}
        />
      </div>
      {unbound.length > 0 && (
        <div className="recovery-run-readiness__issue">
          <b>Unbound tasks</b>
          {unbound.map((block) => (
            <button
              type="button"
              key={block.id}
              data-testid={`workflow-recovery-readiness-task-${block.id}`}
              onClick={() => onSelect(block.id)}
            >
              {block.title} · choose a tool or execution binding
            </button>
          ))}
        </div>
      )}
      {mcpTasks.length > 0 && (
        <div className="recovery-run-readiness__issue">
          <b>Tool bindings</b>
          {mcpTasks.map((block) => (
            <button
              type="button"
              key={block.id}
              data-testid={`workflow-recovery-readiness-mcp-${block.id}`}
              onClick={() => onSelect(block.id)}
            >
              {block.title} ·{" "}
              {String(block.configuration.mcp_server ?? "server not selected")}
              {isExactMcpTool(block)
                ? ` / ${String(block.configuration.mcp_tool ?? "tool not selected")}`
                : " · AI selects the operation"}
              {` · ${mcpStatus(block)}`}
            </button>
          ))}
          {mcpCheckError && (
            <span>
              {mcpCheckError} Owner: Wright environment · Next: check the{" "}
              <a href="/tool-registry">Tool Registry</a>.
            </span>
          )}
          <button
            type="button"
            data-testid="workflow-recovery-mcp-refresh"
            onClick={() => setMcpCheckVersion((version) => version + 1)}
          >
            Recheck MCP availability
          </button>
        </div>
      )}
      {templateReadiness &&
        templateReadiness.state !== "not_template" &&
        (templateReadiness.blocking_reasons.length > 0 ||
          templateReadiness.message) && (
          <div
            className="recovery-run-readiness__issue"
            data-testid="workflow-recovery-template-readiness-issue"
          >
            <b>
              {templateReadiness.template_id ?? "Workflow template"} ·{" "}
              {templateStatus}
            </b>
            {(templateReadiness.blocking_reasons.length
              ? templateReadiness.blocking_reasons
              : [
                  templateReadiness.message ??
                    "Wright could not assess this template.",
                ]
            ).map((reason) => (
              <span key={reason}>
                Owner: template maintainer / Wright environment · Next: {reason}
              </span>
            ))}
            {onRefreshTemplateReadiness && (
              <button
                type="button"
                data-testid="workflow-recovery-template-readiness-refresh"
                onClick={onRefreshTemplateReadiness}
              >
                Recheck qualification
              </button>
            )}
          </div>
        )}
      {inputs.inputs
        .filter((item) => item.status !== "configured")
        .map((item) => (
          <div className="recovery-run-readiness__issue" key={item.blockId}>
            <button
              type="button"
              data-testid={`workflow-recovery-readiness-input-${item.blockId}`}
              onClick={() => onSelect(item.blockId)}
            >
              {item.title} · {item.reason}
            </button>
          </div>
        ))}
      {executionConnected ? (
        <p className="recovery-run-readiness__note">
          Host software, MCP availability, and model access are not assessed by
          the editor. Wright must complete that preflight before any prompt or
          tool call is dispatched. Owner: Wright environment / tool maintainer.
        </p>
      ) : (
        <p className="recovery-run-readiness__note">
          Execution availability has not been assessed. Wright will not send a
          prompt until the run service confirms the saved workflow.
        </p>
      )}
    </details>
  );
}

function ReadinessItem({
  label,
  value,
  status,
  action,
  onAction,
  actionTestId,
}: {
  readonly label: string;
  readonly value: string;
  readonly status: "good" | "attention" | "unknown";
  readonly action?: string;
  readonly onAction?: () => void;
  readonly actionTestId?: string;
}) {
  return (
    <div className={`recovery-run-readiness__item is-${status}`}>
      <span>{label}</span>
      <b>{value}</b>
      {action && onAction && (
        <button type="button" data-testid={actionTestId} onClick={onAction}>
          {action}
        </button>
      )}
    </div>
  );
}

export function AuthoringCreateRail({
  onCreate,
  disabled,
  sessionId,
  onCreateServer,
}: {
  readonly onCreate: (templateId: string) => void;
  readonly disabled: boolean;
  sessionId?: string;
  onCreateServer?: (server: McpServerChoice) => void;
}) {
  const [group, setGroup] = useState<string | null>(null);
  const [tools, setTools] = useState<WorkflowMcpTool[]>([]);
  const [toolMessage, setToolMessage] = useState("");
  useEffect(() => {
    if (group !== "tool" || !sessionId) return;
    let current = true;
    setToolMessage("Loading available servers…");
    void listWorkflowMcpTools(sessionId)
      .then((value) => {
        if (current) {
          setTools(value);
          setToolMessage(
            value.length
              ? ""
              : "Enable a server in Tool Registry to add it here.",
          );
        }
      })
      .catch(() => {
        if (current)
          setToolMessage(
            "Could not load servers. Open Tool Registry to check the connection.",
          );
      });
    return () => {
      current = false;
    };
  }, [group, sessionId]);
  const rootRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!group) return;
    rootRef.current
      ?.querySelector<HTMLButtonElement>(".recovery-create-template")
      ?.focus();
    const dismiss = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setGroup(null);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [group]);
  return (
    <aside
      ref={rootRef}
      className="recovery-create-rail"
      aria-label="Create workflow objects"
      data-testid="workflow-recovery-palette"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          const id = group;
          setGroup(null);
          rootRef.current
            ?.querySelector<HTMLButtonElement>(`[data-group="${id}"]`)
            ?.focus();
        }
      }}
    >
      <div className="recovery-create-buttons">
        <h2>
          <span aria-hidden="true">＋</span> Create
        </h2>
        {AUTHORING_GROUPS.map((item) => (
          <button
            type="button"
            key={item.id}
            data-group={item.id}
            className={`recovery-create-group ${group === item.id ? "is-selected" : ""}`}
            aria-label={item.label}
            aria-expanded={group === item.id}
            aria-controls="recovery-create-options"
            data-testid={`workflow-recovery-create-group-${item.id}`}
            disabled={disabled}
            title={item.description}
            onClick={() =>
              setGroup((current) => (current === item.id ? null : item.id))
            }
          >
            <WorkflowObjectIcon kind={item.id} />
            <b aria-hidden="true">{item.label}</b>
          </button>
        ))}
      </div>
      {group && (
        <section
          id="recovery-create-options"
          className="recovery-create-popover"
          aria-label={`${AUTHORING_GROUPS.find((item) => item.id === group)?.label} templates`}
        >
          <header>
            <h3>{AUTHORING_GROUPS.find((item) => item.id === group)?.label}</h3>
            <button
              type="button"
              data-testid="workflow-recovery-create-close"
              aria-label="Close create menu"
              onClick={() => setGroup(null)}
            >
              ×
            </button>
          </header>
          <p>
            {group === "tool"
              ? "Choose a server, then describe what you want it to do."
              : "Add an object to this workflow. Nothing runs when you add it."}
          </p>
          {AUTHORING_TEMPLATES.filter(
            (item) =>
              item.group === group &&
              !["mcp-tool", "mcp-task", "engineering-step"].includes(item.id),
          ).map((item) => (
            <button
              type="button"
              key={item.id}
              className="recovery-create-template"
              data-testid={`workflow-recovery-create-template-${item.id}`}
              onClick={() => {
                onCreate(item.id);
                setGroup(null);
              }}
            >
              <b>{item.label}</b>
              <span>{item.description}</span>
            </button>
          ))}
          {group === "tool" && (
            <>
              {toolMessage && <p role="status">{toolMessage}</p>}
              {mcpServerChoices(tools).map((server) => (
                <button
                  type="button"
                  key={server.id}
                  className="recovery-create-template"
                  data-testid={`workflow-recovery-create-server-${server.id}`}
                  onClick={() => {
                    onCreateServer?.(server);
                    setGroup(null);
                  }}
                >
                  <b>{server.name}</b>
                  <span>AI task</span>
                </button>
              ))}
              <a href="/tool-registry" target="_blank" rel="noreferrer">
                Add or enable a server
              </a>
            </>
          )}
        </section>
      )}
    </aside>
  );
}

export function AuthoringInputsNavigator({
  workflow,
  onSelect,
}: {
  readonly workflow: RecoveryWorkflow;
  readonly onSelect: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const readiness = authoringReadiness(workflow);
  useEffect(() => {
    if (!open) return;
    const dismiss = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [open]);
  return (
    <div
      className="recovery-inputs-summary"
      ref={rootRef}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setOpen(false);
          rootRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
        }
      }}
    >
      <button
        type="button"
        className="recovery-button recovery-button--secondary"
        data-testid="workflow-recovery-inputs-toggle"
        aria-expanded={open}
        aria-controls="recovery-input-navigator"
        onClick={() => setOpen(!open)}
      >
        Inputs · {readiness.configuredCount}/{readiness.totalCount} configured{" "}
        <span aria-hidden="true">⌄</span>
      </button>
      {open && (
        <section
          id="recovery-input-navigator"
          className="recovery-input-navigator"
          aria-label="Workflow inputs"
          data-testid="workflow-recovery-inputs-navigator"
        >
          <header>
            <b>Workflow inputs</b>
            <button
              type="button"
              aria-label="Close inputs navigator"
              data-testid="workflow-recovery-inputs-close"
              onClick={() => setOpen(false)}
            >
              ×
            </button>
          </header>
          <p>
            Select an input to view or edit it in the Inspector. Configured does
            not mean executed.
          </p>
          {readiness.inputs.length === 0 ? (
            <p>No input objects yet. Add one from Create.</p>
          ) : (
            readiness.inputs.map((item) => (
              <button
                type="button"
                key={item.blockId}
                data-testid={`workflow-recovery-input-navigate-${item.blockId}`}
                onClick={() => {
                  onSelect(item.blockId);
                  setOpen(false);
                }}
              >
                <b>{item.title}</b>
                <span>
                  {item.status === "configured"
                    ? "Configured"
                    : item.status === "unavailable"
                      ? "File unavailable"
                      : "Needs input"}
                </span>
                <small>{item.summary}</small>
              </button>
            ))
          )}
        </section>
      )}
    </div>
  );
}

export function AuthoringOverview({
  block,
  workflow,
  onSelect,
}: {
  readonly block: RecoveryBlock;
  readonly workflow: RecoveryWorkflow;
  readonly onSelect: (id: string) => void;
}) {
  const isInput = recoveryAuthoringSectionKind(block) === "input";
  const state = authoringInputState(block);
  const binding = workflow.bindings.find((item) => item.id === block.bindingId);
  return (
    <section
      className="recovery-overview"
      data-testid={`workflow-recovery-overview-${block.id}`}
    >
      <p>{block.purpose}</p>
      <div className="recovery-fact">
        <span>Source</span>
        <b>
          {isInput
            ? "Engineer input"
            : block.executionKind === "ai_capable"
              ? "AI document / review"
              : block.executionKind === "human"
                ? "Engineer review"
                : "Tool or check"}
        </b>
      </div>
      <div className="recovery-fact">
        <span>Configuration</span>
        <b>
          {isInput
            ? state.status === "configured"
              ? "Configured"
              : "Needs input"
            : binding
              ? "Example binding"
              : "Unbound draft"}
        </b>
      </div>
      <div className="recovery-fact">
        <span>Execution</span>
        <b>Not executed</b>
      </div>
      {isInput && (
        <div className="recovery-input-preview">
          {typeof block.configuration.input_text === "string" &&
          block.configuration.input_text.trim() &&
          block.configuration.input_mode !== "workspace-file"
            ? block.configuration.input_text
            : state.summary}
          {state.reason && <small>{state.reason}</small>}
        </div>
      )}
      {!isInput && (
        <p className="recovery-field-help">
          {binding
            ? "The saved example names an automation. This editor does not verify that it is installed or execute it."
            : "Configure this draft now. An execution binding is required before a real run."}
        </p>
      )}
      <details className="recovery-technical-details">
        <summary
          data-testid={`workflow-recovery-overview-contracts-${block.id}`}
        >
          Inputs and outputs
        </summary>
        {[...block.inputPortIds, ...block.outputPortIds].map((id) => {
          const port = findPort(workflow, id);
          return port ? (
            <button
              type="button"
              key={id}
              data-testid={`workflow-recovery-overview-port-${id}`}
              onClick={() => onSelect(id)}
            >
              {port.direction === "input" ? "Input" : "Output"}: {port.name}
            </button>
          ) : null;
        })}
      </details>
    </section>
  );
}

export function AuthoringSettings({
  block,
  workflow,
  readOnly,
  onApply,
  direct = false,
}: {
  direct?: boolean;
  readonly block: RecoveryBlock;
  readonly workflow: RecoveryWorkflow;
  readonly readOnly: boolean;
  readonly onApply: (commands: RecoveryCommand[]) => boolean;
  readonly onListWorkspaceFiles?: () => Promise<AuthoringWorkspaceFile[]>;
}) {
  const [title, setTitle] = useState(block.title);
  const [instructions, setInstructions] = useState(block.instructions);
  const [configuration, setConfiguration] = useState(block.configuration);
  const [message, setMessage] = useState("");
  const [newKey, setNewKey] = useState("");
  const titleRef = useRef<HTMLInputElement>(null);
  const configurationIdentity = JSON.stringify(block.configuration);
  useEffect(() => {
    setTitle(block.title);
    setInstructions(block.instructions);
    setConfiguration(
      JSON.parse(configurationIdentity) as RecoveryBlock["configuration"],
    );
    setMessage("");
    setNewKey("");
  }, [block.id, block.title, block.instructions, configurationIdentity]);
  const isInput = recoveryAuthoringSectionKind(block) === "input";
  const isReview = block.configuration.authoring_template === "manual-review";
  const isPromptFirst =
    !isInput && (block.executionKind === "ai_capable" || isReview);
  const promptRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    (isPromptFirst ? promptRef.current : titleRef.current)?.focus();
  }, [block.id, isPromptFirst]);
  const inputMode =
    configuration.input_mode === "workspace-file" ? "workspace-file" : "text";
  const isWorkspaceFileInput = isInput && inputMode === "workspace-file";
  const setConfig = (key: string, value: string | number | boolean) => {
    if (direct) {
      try {
        if (!readOnly)
          onApply(authoringConfigurationCommands(block, { [key]: value }));
      } catch (error) {
        setMessage(
          error instanceof Error
            ? error.message
            : "This parameter could not be updated.",
        );
      }
    } else setConfiguration((current) => ({ ...current, [key]: value }));
  };
  const reviewCriteria =
    block.kind === "approval"
      ? workflow.relationships
          .filter(
            (item) =>
              item.sourceId === block.id &&
              (item.kind === "decision" || item.kind === "feedback"),
          )
          .map(
            (item) =>
              `${item.kind === "decision" ? "Accept" : "Revise"} when: ${item.condition ?? item.label}`,
          )
          .join("\n")
      : "";
  const genericEntries = Object.entries(configuration).filter(
    ([key]) =>
      !key.startsWith("__wright_") &&
      ![
        "input_mode",
        "input_text",
        "workspace_file",
        "authoring_template",
        "binding_state",
      ].includes(key),
  );
  const save = () => {
    try {
      const commands: RecoveryCommand[] = [];
      if (title !== block.title)
        commands.push({ kind: "set_block_title", blockId: block.id, title });
      if (instructions !== block.instructions)
        commands.push({
          kind: "set_block_definition",
          blockId: block.id,
          patch: { instructions },
        });
      commands.push(
        ...authoringConfigurationCommands(
          block,
          Object.fromEntries(
            Object.entries(configuration).filter(
              ([key]) => !key.startsWith("__wright_"),
            ),
          ),
        ),
      );
      if (commands.length > 0 && onApply(commands))
        setMessage(
          "Applied to workflow. Save the workflow file to keep these changes.",
        );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "These settings could not be applied.",
      );
    }
  };
  const stepNameField = (
    <label>
      Step name
      <input
        ref={titleRef}
        data-testid={`workflow-recovery-block-title-${block.id}`}
        value={title}
        readOnly={readOnly}
        onChange={(event) => setTitle(event.target.value)}
      />
    </label>
  );
  const instructionsField = !isInput ? (
    <label
      className={
        isPromptFirst ? "recovery-authoring-settings__prompt" : undefined
      }
    >
      {block.executionKind === "ai_capable"
        ? "AI prompt"
        : block.executionKind === "human"
          ? "Engineer checklist"
          : "Tool instructions"}
      <textarea
        ref={isPromptFirst ? promptRef : undefined}
        rows={isPromptFirst ? 8 : 5}
        data-testid={`workflow-recovery-block-instructions-${block.id}`}
        value={instructions}
        readOnly={readOnly}
        onChange={(event) => {
          if (direct) {
            if (!readOnly)
              onApply([
                {
                  kind: "set_block_definition",
                  blockId: block.id,
                  patch: { instructions: event.target.value },
                },
              ]);
          } else setInstructions(event.target.value);
        }}
      />
      <small className="recovery-field-help">
        {isReview
          ? "Connect one document as the final step. These instructions appear with the saved files for your approval or change request."
          : "This prompt is saved in the workflow and is the instruction sent when this step runs."}
      </small>
    </label>
  ) : null;
  return (
    <section className="recovery-authoring-settings">
      {direct
        ? instructionsField
        : isPromptFirst
          ? instructionsField
          : !isWorkspaceFileInput && stepNameField}
      {isInput && (
        <fieldset className="recovery-input-editor">
          <legend>Input content</legend>
          {isWorkspaceFileInput ? (
            <>
              <label>
                Workspace file path
                <input
                  data-testid={`workflow-recovery-input-file-${block.id}`}
                  value={String(configuration.workspace_file ?? "")}
                  readOnly={readOnly}
                  placeholder="requirements.pdf"
                  onChange={(event) =>
                    setConfiguration((current) => ({
                      ...current,
                      input_mode: "workspace-file",
                      workspace_file: event.target.value.trimStart(),
                    }))
                  }
                />
              </label>
              <small>
                Use a path relative to this workspace. A filename with no
                folder, such as <code>requirements.pdf</code>, is in the
                workspace root.
              </small>
            </>
          ) : (
            <>
              <label>
                Provided as
                <select
                  data-testid={`workflow-recovery-input-mode-${block.id}`}
                  disabled={readOnly}
                  value={inputMode}
                  onChange={(event) =>
                    setConfig("input_mode", event.target.value)
                  }
                >
                  <option value="text">Typed text</option>
                  <option value="workspace-file">Workspace file</option>
                </select>
              </label>
              {inputMode === "text" ? (
                <label>
                  Text or design instructions
                  <textarea
                    rows={5}
                    data-testid={`workflow-recovery-input-text-${block.id}`}
                    value={String(configuration.input_text ?? "")}
                    readOnly={readOnly}
                    placeholder="Describe the design intent, requirements, or context…"
                    onChange={(event) =>
                      setConfiguration((current) => ({
                        ...current,
                        input_mode: "text",
                        input_text: event.target.value,
                      }))
                    }
                  />
                </label>
              ) : null}
            </>
          )}
        </fieldset>
      )}
      {!direct && !isPromptFirst && instructionsField}
      {!direct && isPromptFirst && stepNameField}
      {reviewCriteria && (
        <details
          open={direct || undefined}
          className="recovery-inspector__field"
        >
          <summary
            data-testid={`workflow-recovery-block-review-toggle-${block.id}`}
          >
            Review criteria
          </summary>
          <textarea
            aria-label="Engineer approval checklist"
            data-testid={`workflow-recovery-block-review-${block.id}`}
            readOnly
            value={reviewCriteria}
          />
          <small>
            These criteria come from this step&apos;s accept and revise paths;
            edit the corresponding connection to change them.
          </small>
        </details>
      )}
      {!isReview && (
        <details className="recovery-technical-details">
          <summary
            data-testid={`workflow-recovery-settings-advanced-${block.id}`}
          >
            Parameters and advanced settings
          </summary>
          {genericEntries.map(([key, value]) => (
            <label key={key}>
              {key.replace(/_/g, " ")}
              {typeof value === "boolean" ? (
                <input
                  type="checkbox"
                  data-testid={`workflow-recovery-block-parameter-${block.id}-${key}`}
                  checked={value}
                  disabled={readOnly}
                  onChange={(event) => setConfig(key, event.target.checked)}
                />
              ) : (
                <input
                  type={typeof value === "number" ? "number" : "text"}
                  data-testid={
                    key === "thickness_mm"
                      ? `workflow-recovery-block-thickness-${block.id}`
                      : `workflow-recovery-block-parameter-${block.id}-${key}`
                  }
                  value={value}
                  readOnly={readOnly}
                  onChange={(event) =>
                    setConfig(
                      key,
                      typeof value === "number"
                        ? Number(event.target.value)
                        : event.target.value,
                    )
                  }
                />
              )}
            </label>
          ))}
          {!readOnly && (
            <div className="recovery-parameter-add">
              <label>
                New parameter
                <input
                  data-testid={`workflow-recovery-parameter-name-${block.id}`}
                  value={newKey}
                  onChange={(event) => setNewKey(event.target.value)}
                  placeholder="parameter_name"
                />
              </label>
              <button
                type="button"
                data-testid={`workflow-recovery-parameter-add-${block.id}`}
                disabled={
                  !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(newKey) ||
                  newKey in configuration
                }
                onClick={() => {
                  setConfig(newKey, "");
                  setNewKey("");
                }}
              >
                Add parameter
              </button>
            </div>
          )}
          <code>{block.id}</code>
          <span>
            {block.inputPortIds.length} inputs · {block.outputPortIds.length}{" "}
            outputs
          </span>
        </details>
      )}
      {message && (
        <p
          role="status"
          className="recovery-field-help"
          data-testid="workflow-recovery-settings-feedback"
        >
          {message}
        </p>
      )}
      {readOnly ? (
        <p data-testid="workflow-recovery-candidate-readonly">
          Editing is unavailable while a run, save, or suggestion review is in
          progress.
        </p>
      ) : (
        <div className="recovery-inspector__actions">
          {!direct && (
            <button
              type="button"
              className="recovery-button recovery-button--primary"
              data-testid="workflow-recovery-config-apply"
              onClick={save}
            >
              Apply settings
            </button>
          )}
        </div>
      )}
    </section>
  );
}

export function AuthoringPortConnections({
  workflow,
  portId,
  onSelect,
}: {
  readonly workflow: RecoveryWorkflow;
  readonly portId: string;
  readonly onSelect: (id: string) => void;
}) {
  const port = findPort(workflow, portId);
  if (!port) return null;
  const relationships = workflow.relationships.filter(
    (item) =>
      item.kind === "data" &&
      (item.sourceId === portId || item.targetId === portId),
  );
  return (
    <div className="recovery-port-connections">
      <b>{port.direction === "input" ? "Comes from" : "Used by"}</b>
      {relationships.length === 0 ? (
        <span>Not connected</span>
      ) : (
        relationships.map((item) => {
          const otherId =
            item.sourceId === portId ? item.targetId : item.sourceId;
          const other = findPort(workflow, otherId);
          const owner = other ? findBlock(workflow, other.ownerBlockId) : null;
          return (
            <button
              type="button"
              key={item.id}
              data-testid={`workflow-recovery-port-navigate-${portId}-${item.id}`}
              onClick={() => onSelect(otherId)}
            >
              {owner?.title ?? "Workflow step"} · {other?.name ?? otherId}
            </button>
          );
        })
      )}
      <small>
        {port.cardinality === "many"
          ? "Accepts a collection / multiple connected items"
          : port.cardinality === "optional"
            ? "Optional single item"
            : "Single item"}
        {port.direction === "output" ? " · May feed multiple steps" : ""}
      </small>
    </div>
  );
}

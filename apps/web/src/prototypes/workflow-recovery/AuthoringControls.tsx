import { useEffect, useRef, useState } from "react";

import { AUTHORING_GROUPS, AUTHORING_TEMPLATES, authoringConfigurationCommands, authoringInputState, authoringReadiness } from "./authoring-objects";
import type { RecoveryCommand } from "./command-system";
import { findBlock, findPort, recoveryAuthoringSectionKind, type RecoveryBlock, type RecoveryWorkflow } from "./model";
import { WorkflowObjectIcon } from "./WorkflowObjectIcon";

export interface AuthoringWorkspaceFile { path: string; name: string }

export function AuthoringCreateRail({ onCreate, disabled }: { readonly onCreate: (templateId: string) => void; readonly disabled: boolean }) {
  const [group, setGroup] = useState<string | null>(null);
  const rootRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!group) return;
    rootRef.current?.querySelector<HTMLButtonElement>(".recovery-create-template")?.focus();
    const dismiss = (event: PointerEvent) => { if (!rootRef.current?.contains(event.target as Node)) setGroup(null); };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [group]);
  return <aside ref={rootRef} className="recovery-create-rail" aria-label="Create workflow objects" data-testid="workflow-recovery-palette" onKeyDown={(event) => { if (event.key === "Escape") { const id = group; setGroup(null); rootRef.current?.querySelector<HTMLButtonElement>(`[data-group="${id}"]`)?.focus(); } }}>
    <div className="recovery-create-buttons"><h2><span aria-hidden="true">＋</span> Create</h2>
    {AUTHORING_GROUPS.map((item) => <button type="button" key={item.id} data-group={item.id} className={`recovery-create-group ${group === item.id ? "is-selected" : ""}`} aria-expanded={group === item.id} aria-controls="recovery-create-options" data-testid={`workflow-recovery-create-group-${item.id}`} disabled={disabled} title={item.description} onClick={() => setGroup((current) => current === item.id ? null : item.id)}><WorkflowObjectIcon kind={item.id} /><b>{item.label}</b></button>)}</div>
    {group && <section id="recovery-create-options" className="recovery-create-popover" aria-label={`${AUTHORING_GROUPS.find((item) => item.id === group)?.label} templates`}>
      <header><h3>{AUTHORING_GROUPS.find((item) => item.id === group)?.label}</h3><button type="button" data-testid="workflow-recovery-create-close" aria-label="Close create menu" onClick={() => setGroup(null)}>×</button></header>
      <p>Add an object to this workflow. Nothing runs when you add it.</p>
      {AUTHORING_TEMPLATES.filter((item) => item.group === group).map((item) => <button type="button" key={item.id} className="recovery-create-template" data-testid={`workflow-recovery-create-template-${item.id}`} onClick={() => { onCreate(item.id); setGroup(null); }}><b>{item.label}</b><span>{item.description}</span></button>)}
    </section>}
  </aside>;
}

export function AuthoringInputsNavigator({ workflow, onSelect }: { readonly workflow: RecoveryWorkflow; readonly onSelect: (id: string) => void }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const readiness = authoringReadiness(workflow);
  useEffect(() => {
    if (!open) return;
    const dismiss = (event: PointerEvent) => { if (!rootRef.current?.contains(event.target as Node)) setOpen(false); };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [open]);
  return <div className="recovery-inputs-summary" ref={rootRef} onKeyDown={(event) => { if (event.key === "Escape") { setOpen(false); rootRef.current?.querySelector<HTMLButtonElement>("button")?.focus(); } }}>
    <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-inputs-toggle" aria-expanded={open} aria-controls="recovery-input-navigator" onClick={() => setOpen(!open)}>Inputs · {readiness.configuredCount}/{readiness.totalCount} configured <span aria-hidden="true">⌄</span></button>
    {open && <section id="recovery-input-navigator" className="recovery-input-navigator" aria-label="Workflow inputs" data-testid="workflow-recovery-inputs-navigator">
      <header><b>Workflow inputs</b><button type="button" aria-label="Close inputs navigator" data-testid="workflow-recovery-inputs-close" onClick={() => setOpen(false)}>×</button></header>
      <p>Select an input to view or edit it in the Inspector. Configured does not mean executed.</p>
      {readiness.inputs.length === 0 ? <p>No input objects yet. Add one from Create.</p> : readiness.inputs.map((item) => <button type="button" key={item.blockId} data-testid={`workflow-recovery-input-navigate-${item.blockId}`} onClick={() => { onSelect(item.blockId); setOpen(false); }}><b>{item.title}</b><span>{item.status === "configured" ? "Configured" : item.status === "unavailable" ? "File unavailable" : "Needs input"}</span><small>{item.summary}</small></button>)}
    </section>}
  </div>;
}

export function AuthoringOverview({ block, workflow, onSettings, onSelect }: { readonly block: RecoveryBlock; readonly workflow: RecoveryWorkflow; readonly onSettings: () => void; readonly onSelect: (id: string) => void }) {
  const isInput = recoveryAuthoringSectionKind(block) === "input";
  const state = authoringInputState(block);
  const binding = workflow.bindings.find((item) => item.id === block.bindingId);
  return <section className="recovery-overview" data-testid={`workflow-recovery-overview-${block.id}`}>
    <p>{block.purpose}</p>
    <div className="recovery-fact"><span>Source</span><b>{isInput ? "Engineer input" : block.executionKind === "ai_capable" ? "AI document / review" : block.executionKind === "human" ? "Engineer review" : "Tool or check"}</b></div>
    <div className="recovery-fact"><span>Configuration</span><b>{isInput ? state.status === "configured" ? "Configured" : "Needs input" : binding ? "Example binding" : "Unbound draft"}</b></div>
    <div className="recovery-fact"><span>Execution</span><b>Not executed</b></div>
    {isInput && <div className="recovery-input-preview">{typeof block.configuration.input_text === "string" && block.configuration.input_text.trim() && block.configuration.input_mode !== "workspace-file" ? block.configuration.input_text : state.summary}{state.reason && <small>{state.reason}</small>}</div>}
    {!isInput && <p className="recovery-field-help">{binding ? "The saved example names an automation. This editor does not verify that it is installed or execute it." : "Configure this draft now. An execution binding is required before a real run."}</p>}
    <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-open-settings" onClick={onSettings}>Edit settings</button>
    <details className="recovery-technical-details"><summary data-testid={`workflow-recovery-overview-contracts-${block.id}`}>Inputs and outputs</summary>
      {[...block.inputPortIds, ...block.outputPortIds].map((id) => { const port = findPort(workflow, id); return port ? <button type="button" key={id} data-testid={`workflow-recovery-overview-port-${id}`} onClick={() => onSelect(id)}>{port.direction === "input" ? "Uses" : "Creates"}: {port.name}</button> : null; })}
    </details>
  </section>;
}

export function AuthoringSettings({ block, workflow, readOnly, onApply, onDelete, onListWorkspaceFiles }: { readonly block: RecoveryBlock; readonly workflow: RecoveryWorkflow; readonly readOnly: boolean; readonly onApply: (commands: RecoveryCommand[]) => boolean; readonly onDelete: () => void; readonly onListWorkspaceFiles?: () => Promise<AuthoringWorkspaceFile[]> }) {
  const [title, setTitle] = useState(block.title);
  const [instructions, setInstructions] = useState(block.instructions);
  const [configuration, setConfiguration] = useState(block.configuration);
  const [files, setFiles] = useState<AuthoringWorkspaceFile[]>([]);
  const [fileState, setFileState] = useState<"idle" | "loading" | "loaded" | "error">("idle");
  const [message, setMessage] = useState("");
  const [newKey, setNewKey] = useState("");
  const titleRef = useRef<HTMLInputElement>(null);
  useEffect(() => { titleRef.current?.focus(); }, [block.id]);
  const configurationIdentity = JSON.stringify(block.configuration);
  useEffect(() => { setTitle(block.title); setInstructions(block.instructions); setConfiguration(JSON.parse(configurationIdentity) as RecoveryBlock["configuration"]); setMessage(""); setNewKey(""); }, [block.id, block.title, block.instructions, configurationIdentity]);
  const isInput = recoveryAuthoringSectionKind(block) === "input";
  const inputMode = configuration.input_mode === "workspace-file" ? "workspace-file" : "text";
  const setConfig = (key: string, value: string | number | boolean) => setConfiguration((current) => ({ ...current, [key]: value }));
  const listFiles = async () => {
    if (!onListWorkspaceFiles) return;
    setFileState("loading");
    try { setFiles(await onListWorkspaceFiles()); setFileState("loaded"); setMessage(""); } catch { setFileState("error"); setMessage("Workspace files could not be read. Existing input configuration was kept; retry the file list."); }
  };
  const reviewCriteria = block.kind === "approval" ? workflow.relationships.filter((item) => item.sourceId === block.id && (item.kind === "decision" || item.kind === "feedback")).map((item) => `${item.kind === "decision" ? "Accept" : "Revise"} when: ${item.condition ?? item.label}`).join("\n") : "";
  const genericEntries = Object.entries(configuration).filter(([key]) => !key.startsWith("__wright_") && !["input_mode", "input_text", "workspace_file", "authoring_template", "binding_state"].includes(key));
  const save = () => {
    try {
      const commands: RecoveryCommand[] = [];
      if (title !== block.title) commands.push({ kind: "set_block_title", blockId: block.id, title });
      if (instructions !== block.instructions) commands.push({ kind: "set_block_definition", blockId: block.id, patch: { instructions } });
      commands.push(...authoringConfigurationCommands(block, Object.fromEntries(Object.entries(configuration).filter(([key]) => !key.startsWith("__wright_")))));
      if (commands.length > 0 && onApply(commands)) setMessage("Applied to workflow. Save the workflow file to keep these changes.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "These settings could not be applied."); }
  };
  return <section className="recovery-authoring-settings">
    <label>Step name<input ref={titleRef} data-testid={`workflow-recovery-block-title-${block.id}`} value={title} readOnly={readOnly} onChange={(event) => setTitle(event.target.value)} /></label>
    {isInput && <fieldset className="recovery-input-editor"><legend>Input content</legend>
      <label>Provided as<select data-testid={`workflow-recovery-input-mode-${block.id}`} disabled={readOnly} value={inputMode} onChange={(event) => { setConfig("input_mode", event.target.value); if (event.target.value === "workspace-file") void listFiles(); }}><option value="text">Typed text</option><option value="workspace-file">Workspace file</option></select></label>
      {inputMode === "text" ? <label>Text or design instructions<textarea rows={5} data-testid={`workflow-recovery-input-text-${block.id}`} value={String(configuration.input_text ?? "")} readOnly={readOnly} placeholder="Describe the design intent, requirements, or context…" onChange={(event) => setConfiguration((current) => ({ ...current, input_mode: "text", input_text: event.target.value }))} /></label> : <>
        <label>Workspace file<select data-testid={`workflow-recovery-input-file-${block.id}`} disabled={readOnly || fileState !== "loaded"} value={String(configuration.workspace_file ?? "")} onChange={(event) => setConfiguration((current) => ({ ...current, input_mode: "workspace-file", workspace_file: event.target.value }))}><option value="">Choose a workspace file</option>{configuration.workspace_file && !files.some((file) => file.path === configuration.workspace_file) && <option value={String(configuration.workspace_file)}>{String(configuration.workspace_file)} (not in current list)</option>}{files.map((file) => <option key={file.path} value={file.path}>{file.path}</option>)}</select></label>
        <button type="button" className="recovery-button recovery-button--secondary" data-testid={`workflow-recovery-input-files-refresh-${block.id}`} disabled={!onListWorkspaceFiles || fileState === "loading"} onClick={() => void listFiles()}>{fileState === "loading" ? "Reading files…" : "Refresh workspace files"}</button>
        {!onListWorkspaceFiles && <small>File selection requires an open workspace. Typed input remains available.</small>}{fileState === "loaded" && files.length === 0 && <small>No permitted files were found in this workspace. Add a document using the workspace file browser.</small>}
      </>}
      <small>The text or relative file reference is stored in the workflow. Selecting a file does not run or upload it.</small>
    </fieldset>}
    {!isInput && <label>{block.executionKind === "ai_capable" ? "AI prompt" : block.executionKind === "human" ? "Engineer checklist" : "Tool instructions"}<textarea rows={5} data-testid={`workflow-recovery-block-instructions-${block.id}`} value={instructions} readOnly={readOnly} onChange={(event) => setInstructions(event.target.value)} /><small className="recovery-field-help">Written in this workflow, not copied from an input document. {block.bindingId ? "Example binding only; no real execution is available here." : "Unbound draft; adding or editing this object does not execute it."}</small></label>}
    {reviewCriteria && <details className="recovery-inspector__field"><summary data-testid={`workflow-recovery-block-review-toggle-${block.id}`}>Engineer approval checklist</summary><textarea aria-label="Engineer approval checklist" data-testid={`workflow-recovery-block-review-${block.id}`} readOnly value={reviewCriteria} /><small>These criteria come from this step&apos;s accept and revise paths; edit the corresponding connection to change them.</small></details>}
    <details className="recovery-technical-details"><summary data-testid={`workflow-recovery-settings-advanced-${block.id}`}>Parameters and advanced settings</summary>
      {genericEntries.map(([key, value]) => <label key={key}>{key.replace(/_/g, " ")}{typeof value === "boolean" ? <input type="checkbox" data-testid={`workflow-recovery-block-parameter-${block.id}-${key}`} checked={value} disabled={readOnly} onChange={(event) => setConfig(key, event.target.checked)} /> : <input type={typeof value === "number" ? "number" : "text"} data-testid={key === "thickness_mm" ? `workflow-recovery-block-thickness-${block.id}` : `workflow-recovery-block-parameter-${block.id}-${key}`} value={value} readOnly={readOnly} onChange={(event) => setConfig(key, typeof value === "number" ? Number(event.target.value) : event.target.value)} />}</label>)}
      {!readOnly && <div className="recovery-parameter-add"><label>New parameter<input data-testid={`workflow-recovery-parameter-name-${block.id}`} value={newKey} onChange={(event) => setNewKey(event.target.value)} placeholder="parameter_name" /></label><button type="button" data-testid={`workflow-recovery-parameter-add-${block.id}`} disabled={!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(newKey) || newKey in configuration} onClick={() => { setConfig(newKey, ""); setNewKey(""); }}>Add parameter</button></div>}
      <code>{block.id}</code><span>{block.inputPortIds.length} inputs · {block.outputPortIds.length} outputs</span>
    </details>
    {message && <p role="status" className="recovery-field-help" data-testid="workflow-recovery-settings-feedback">{message}</p>}
    {readOnly ? <p data-testid="workflow-recovery-candidate-readonly">This example suggestion is read-only until you add or discard it.</p> : <div className="recovery-inspector__actions"><button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-config-apply" onClick={save}>Apply settings</button><button type="button" className="recovery-button recovery-button--danger" data-testid="workflow-recovery-delete" onClick={onDelete}>Delete step…</button></div>}
  </section>;
}

export function AuthoringPortConnections({ workflow, portId, onSelect }: { readonly workflow: RecoveryWorkflow; readonly portId: string; readonly onSelect: (id: string) => void }) {
  const port = findPort(workflow, portId);
  if (!port) return null;
  const relationships = workflow.relationships.filter((item) => item.kind === "data" && (item.sourceId === portId || item.targetId === portId));
  return <div className="recovery-port-connections"><b>{port.direction === "input" ? "Comes from" : "Used by"}</b>{relationships.length === 0 ? <span>Not connected</span> : relationships.map((item) => { const otherId = item.sourceId === portId ? item.targetId : item.sourceId; const other = findPort(workflow, otherId); const owner = other ? findBlock(workflow, other.ownerBlockId) : null; return <button type="button" key={item.id} data-testid={`workflow-recovery-port-navigate-${portId}-${item.id}`} onClick={() => onSelect(otherId)}>{owner?.title ?? "Workflow step"} · {other?.name ?? otherId}</button>; })}<small>{port.cardinality === "many" ? "Accepts a collection / multiple connected items" : port.cardinality === "optional" ? "Optional single item" : "Single item"}{port.direction === "output" ? " · May feed multiple steps" : ""}</small></div>;
}

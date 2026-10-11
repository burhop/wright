import type {
  WorkspaceWorkflowOutput,
  WorkspaceWorkflowRunSummary,
} from "../../services/workspace-service";
import {
  findBlock,
  findPort,
  recoveryAuthoringSectionKind,
  type RecoveryBlock,
  type RecoveryWorkflow,
} from "./model";
import {
  fileKind,
  fileName,
  taskBlockId,
} from "./engineering-run-presentation";

// Unknown action settings remain visible; never summarize away an authorization limit.
export function EngineeringActionScope({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span>Not specified</span>;
  if (Array.isArray(value))
    return (
      <ul>
        {value.map((item, i) => (
          <li key={i}>
            <EngineeringActionScope value={item} />
          </li>
        ))}
      </ul>
    );
  if (typeof value === "object")
    return (
      <dl className="recovery-action-scope">
        {Object.entries(value).map(([key, item]) => (
          <div key={key}>
            <dt>{key.replaceAll("_", " ")}</dt>
            <dd>
              <EngineeringActionScope value={item} />
            </dd>
          </div>
        ))}
      </dl>
    );
  if (typeof value === "boolean") return <span>{value ? "Yes" : "No"}</span>;
  if (typeof value === "string" && /^[a-f0-9]{64}$/i.test(value))
    return <span>File version recorded in the technical record</span>;
  return <span>{String(value)}</span>;
}

export function EngineeringFiles({
  paths,
  onOpenFile,
}: {
  paths: readonly string[];
  onOpenFile?: (path: string) => void;
}) {
  return (
    <ul className="recovery-engineering-files">
      {paths.map((path) => (
        <li key={path}>
          <span>
            <b title={path}>{fileName(path)}</b>
            <small>{fileKind(path)}</small>
            {paths.some(
              (other) => other !== path && fileName(other) === fileName(path),
            ) && <small>{path}</small>}
          </span>
          {onOpenFile ? (
            <button
              type="button"
              className="recovery-button recovery-button--secondary"
              title={path}
              aria-label={`Open ${fileName(path)}`}
              onClick={() => onOpenFile(path)}
            >
              Open file
            </button>
          ) : (
            <code>{path}</code>
          )}
        </li>
      ))}
    </ul>
  );
}

export function EngineeringStepContext({
  block,
  workflow,
  outputs,
  sourceMismatch,
  onOpenFile,
}: {
  block: RecoveryBlock;
  workflow: RecoveryWorkflow;
  outputs: readonly WorkspaceWorkflowOutput[];
  sourceMismatch: boolean;
  onOpenFile?: (path: string) => void;
}) {
  const input = recoveryAuthoringSectionKind(block) === "input";
  const sourceNames = [
    ...new Set(
      workflow.relationships
        .filter(
          (r) =>
            r.kind === "data" &&
            findPort(workflow, r.targetId)?.ownerBlockId === block.id,
        )
        .map(
          (r) =>
            findBlock(
              workflow,
              findPort(workflow, r.sourceId)?.ownerBlockId ?? "",
            )?.title,
        )
        .filter((name): name is string => !!name),
    ),
  ];
  const files = sourceMismatch
    ? []
    : outputs.filter((o) => taskBlockId(o.task_id) === block.id);
  return (
    <section
      className="recovery-step-context"
      data-testid="workflow-engineering-step-context"
    >
      <h3>{input ? "What this input supplies" : "What this step does"}</h3>
      <p>
        {block.purpose ||
          (input
            ? "Supplies the saved text or file to connected steps."
            : "No purpose has been written for this step yet.")}
      </p>
      {!!sourceNames.length && (
        <>
          <h4>Uses information from</h4>
          <ul>
            {sourceNames.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        </>
      )}
      {!input && !!block.outputPortIds.length && (
        <>
          <h4>Expected outputs</h4>
          <ul>
            {block.outputPortIds.map((id) => {
              const port = findPort(workflow, id);
              return port ? (
                <li key={id}>{port.description || port.name}</li>
              ) : null;
            })}
          </ul>
          <small>
            Declared by the workflow; this does not mean a result has been
            produced or passed its checks.
          </small>
        </>
      )}
      {!!files.length && (
        <>
          <h4>Files produced in this run</h4>
          <EngineeringFiles
            paths={files.map((f) => f.output_path)}
            onOpenFile={onOpenFile}
          />
        </>
      )}
      {sourceMismatch && !input && (
        <p>
          Run results belong to a different saved workflow or an edited draft.
          Open Run details to inspect that run.
        </p>
      )}
    </section>
  );
}

export function EngineeringRunProgress({
  run,
  workflow,
  onSelectBlock,
}: {
  run: WorkspaceWorkflowRunSummary;
  workflow: RecoveryWorkflow;
  onSelectBlock: (id: string) => void;
}) {
  if (!run.execution) return null;
  const completed = new Set(run.execution.completed_task_ids.map(taskBlockId));
  const active = run.execution.active_task_id
    ? taskBlockId(run.execution.active_task_id)
    : null;
  const review =
    run.approval?.state === "pending"
      ? taskBlockId(run.approval.step_id)
      : null;
  const last = run.execution.last_progress?.task_id
    ? taskBlockId(run.execution.last_progress.task_id)
    : null;
  const blocks = workflow.blocks.filter(
    (b) => recoveryAuthoringSectionKind(b) !== "input",
  );
  return (
    <details
      className="recovery-run-progress"
      data-testid="workflow-engineering-run-progress"
    >
      <summary>
        Step progress · {blocks.filter((b) => completed.has(b.id)).length} of{" "}
        {blocks.length} finished
      </summary>
      <p>
        Finished means the step ran, not that its result passed engineering
        review. Select a step to inspect its purpose and connections.
      </p>
      <ul>
        {blocks.map((block) => {
          const state =
            review === block.id
              ? "Awaiting your review"
              : run.status === "failed" && last === block.id
                ? "Stopped with an error"
                : run.status === "running" && active === block.id
                  ? "Running"
                  : completed.has(block.id)
                    ? "Finished"
                    : "No completion recorded";
          return (
            <li key={block.id}>
              <button
                type="button"
                className="recovery-button recovery-button--secondary"
                onClick={() => onSelectBlock(block.id)}
              >
                {block.title}
              </button>
              <span>{state}</span>
            </li>
          );
        })}
      </ul>
    </details>
  );
}

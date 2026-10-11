import type {
  WorkspaceEngineeringResult,
  WorkspaceWorkflowOutput,
  WorkspaceWorkflowRunSummary,
  WorkflowApprovalCheckpoint,
} from "../../services/workspace-service";
import type { RecoveryWorkflow } from "./model";
import { RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY } from "./model";
import {
  fileKind,
  fileName,
  reviewFiles,
  taskBlockId,
} from "./engineering-run-presentation";

export interface ResultFile {
  path: string;
  available: boolean;
  sha256?: string;
}

/** A read-only run projection, never a task, port, or persisted layout object. */
export interface WorkflowResultBlock {
  id: string;
  producerId: string | null;
  producerTitle: string;
  title: string;
  files: ResultFile[];
  sourceMismatch: boolean;
  reviewLabel: string;
  unavailableRun?: {
    status: WorkspaceWorkflowRunSummary["status"];
    failedStepId?: string;
    failedStepTitle?: string;
    error?: string;
    diagnostic?: string;
  };
}

export function safeResultPath(value: unknown): value is string {
  return (
    typeof value === "string" &&
    !!value.trim() &&
    // Intentionally reject control characters in untrusted artifact paths.
    // eslint-disable-next-line no-control-regex
    !/^[\\/]|[:\\?#\x00-\x1f]/.test(value) &&
    !value.split("/").some((part) => part === ".." || part === "." || !part)
  );
}

function expectedFiles(
  configuration: RecoveryWorkflow["blocks"][number]["configuration"],
): string[] {
  let retained: Record<string, unknown> = {};
  try {
    retained = JSON.parse(
      String(configuration[RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY] ?? "{}"),
    );
  } catch {
    /* Incomplete authoring draft. */
  }
  const mapping = retained?.expected_file_ports;
  return [
    ...(configuration.save_output === true
      ? [configuration.output_filename]
      : []),
    ...String(configuration.expected_files ?? "").split(/\r?\n/),
    ...(mapping && typeof mapping === "object" ? Object.values(mapping) : []),
  ].filter(safeResultPath);
}

function resultTitle(files: ResultFile[]): string {
  if (files.length === 1 && /\.(png|jpe?g|gif|webp)$/i.test(files[0]!.path))
    return "Image";
  if (files.some((file) => fileKind(file.path) === "Plot or image"))
    return "Plots and supporting data";
  const document = files.find((file) => fileKind(file.path) === "Document");
  if (document) {
    const name = fileName(document.path)
      .replace(/\.[^.]+$/, "")
      .replace(/[-_]+/g, " ");
    return name.charAt(0).toUpperCase() + name.slice(1);
  }
  if (files.some((file) => fileKind(file.path) === "Model"))
    return "Models and drawings";
  if (files.some((file) => fileKind(file.path) === "Data table"))
    return "Data tables";
  return "Supporting files";
}

/** Attribute a failure only when the saved run identifies the failed step. */
export function recordedFailedStep(
  workflow: RecoveryWorkflow | null,
  run?: WorkspaceWorkflowRunSummary | null,
): { id?: string; title?: string; diagnostic?: string } | null {
  const progress = run?.execution?.last_progress;
  if (
    run?.status !== "failed" ||
    !progress ||
    !(
      progress.status === "failed" ||
      (progress.kind === "step_diagnostic" &&
        !!progress.message &&
        progress.message === run.error)
    )
  )
    return null;
  const id = progress.task_id ? taskBlockId(progress.task_id) : undefined;
  return {
    id: workflow?.blocks.some((block) => block.id === id) ? id : undefined,
    title: progress.task_title,
    diagnostic:
      progress.kind === "step_diagnostic" ? progress.diagnostic : undefined,
  };
}

export function workflowResultBlocks({
  workflow,
  results = [],
  outputs = [],
  checkpoint,
  sourceMismatch = false,
  run,
}: {
  workflow: RecoveryWorkflow | null;
  results?: readonly WorkspaceEngineeringResult[];
  outputs?: readonly WorkspaceWorkflowOutput[];
  checkpoint?: WorkflowApprovalCheckpoint | null;
  sourceMismatch?: boolean;
  run?: WorkspaceWorkflowRunSummary | null;
}): WorkflowResultBlock[] {
  const groups = new Map<string, WorkflowResultBlock>();
  function group(producerId: string, producerTitle?: string, recorded = false) {
    // Never attach old run evidence to a newly edited step with the same ID.
    const detached = recorded && sourceMismatch;
    const id = `result.${detached ? "saved." : ""}${producerId}`;
    let value = groups.get(id);
    if (!value) {
      const producer = workflow?.blocks.find(
        (block) => block.id === producerId,
      );
      value = {
        id,
        producerId: detached ? null : (producer?.id ?? null),
        producerTitle:
          producerTitle ||
          (!detached ? producer?.title : undefined) ||
          "Saved workflow step",
        title: "",
        files: [],
        sourceMismatch: detached,
        reviewLabel: "",
      };
      groups.set(id, value);
    }
    if ((detached || !workflow) && producerTitle)
      value.producerTitle = producerTitle;
    return value;
  }
  function add(
    target: WorkflowResultBlock,
    path: string,
    available: boolean,
    sha256?: string | null,
  ) {
    if (!safeResultPath(path)) return;
    const prior = target.files.find((file) => file.path === path);
    const digest =
      typeof sha256 === "string" && /^[a-f0-9]{64}$/i.test(sha256)
        ? sha256
        : undefined;
    if (prior) {
      prior.available ||= available;
      prior.sha256 = digest ?? prior.sha256;
    } else target.files.push({ path, available, sha256: digest });
  }
  for (const block of workflow?.blocks ?? []) {
    const files = expectedFiles(block.configuration);
    for (const path of files) add(group(block.id), path, false);
  }
  function visit(result: WorkspaceEngineeringResult) {
    for (const representation of result.representations) {
      if (
        representation.kind !== "workspace_file" ||
        !safeResultPath(representation.location)
      )
        continue;
      add(
        group(taskBlockId(result.provenance.task_id), undefined, true),
        representation.location,
        true,
        representation.sha256,
      );
    }
    result.exports.forEach(visit);
  }
  results.forEach(visit);
  for (const output of outputs) {
    if (safeResultPath(output.output_path))
      add(
        group(taskBlockId(output.task_id), output.task_title, true),
        output.output_path,
        true,
      );
  }
  const reviewed = new Set(checkpoint ? reviewFiles(checkpoint) : []);
  const reviewRecords = (checkpoint?.continuation.artifact_files ?? []) as {
    path: string;
    sha256: string;
  }[];
  const priority = (file: ResultFile) =>
    [
      "Plot or image",
      "Document",
      "Model",
      "Data table",
      "Supporting file",
    ].indexOf(fileKind(file.path));
  return [...groups.values()]
    .map((value) => {
      value.files.sort((a, b) => priority(a) - priority(b));
      value.title = resultTitle(value.files);
      if (
        run &&
        !sourceMismatch &&
        !value.files.some((file) => file.available)
      ) {
        const failedStep = recordedFailedStep(workflow, run);
        value.unavailableRun = {
          status: run.status,
          failedStepId: failedStep?.id,
          failedStepTitle: failedStep?.title,
          error: run.error,
          diagnostic: failedStep?.diagnostic,
        };
      }
      for (const file of value.files) {
        if (file.available && reviewed.has(file.path))
          file.sha256 ??= reviewRecords.find(
            (record) => record?.path === file.path,
          )?.sha256;
      }
      const hasReviewEvidence = value.files.some(
        (file) =>
          file.available &&
          reviewed.has(file.path) &&
          reviewRecords.some(
            (record) =>
              record?.path === file.path && record.sha256 === file.sha256,
          ),
      );
      if (hasReviewEvidence && checkpoint?.action_kind === "local_review") {
        value.reviewLabel =
          checkpoint.state === "pending"
            ? "Includes files awaiting review"
            : checkpoint.state === "changes_requested"
              ? "Changes requested"
              : ["approved", "consumed"].includes(checkpoint.state)
                ? "Includes reviewed files"
                : "Review needs updating";
      }
      return value;
    })
    .sort(
      (a, b) =>
        Number(a.sourceMismatch) - Number(b.sourceMismatch) ||
        priority(a.files[0]) - priority(b.files[0]),
    );
}

export function resultAvailability(result: WorkflowResultBlock): string {
  const available = result.files.filter((file) => file.available).length;
  if (result.sourceMismatch) return "From saved run · workflow changed";
  if (!available && result.unavailableRun?.status === "failed")
    return "Not produced · run failed";
  if (!available && result.unavailableRun?.status === "cancelled")
    return "Not produced · run cancelled";
  if (!available) return "Not produced yet";
  return `${available} of ${result.files.length} files available`;
}

import type { WorkflowApprovalCheckpoint } from "../../services/workspace-service";

export const fileName = (path: string) => path.split(/[\\/]/).at(-1) || path;

export function fileKind(path: string): string {
  const extension = fileName(path).split(".").at(-1)?.toLowerCase();
  if (["md", "html", "pdf", "docx", "txt"].includes(extension ?? ""))
    return "Document";
  if (["svg", "png", "jpg", "jpeg", "webp"].includes(extension ?? ""))
    return "Plot or image";
  if (["csv", "tsv", "xlsx"].includes(extension ?? "")) return "Data table";
  if (["step", "stp", "stl", "3mf", "fcstd"].includes(extension ?? ""))
    return "Model";
  return "Supporting file";
}

export function approvalPresentation(
  checkpoint?: WorkflowApprovalCheckpoint | null,
) {
  if (!checkpoint || checkpoint.action_kind !== "local_review") return null;
  const presentations = {
    pending: {
      label: "Awaiting your review",
      detail:
        "Inspect the results and check the requirements below. The workflow is paused for your decision.",
    },
    approved: {
      label: "Review approved · waiting to continue",
      detail:
        "Your decision is recorded for these results. The remaining workflow steps have not yet completed.",
    },
    changes_requested: {
      label: "Changes requested",
      detail:
        "Your feedback is recorded. These results have not been approved.",
    },
    stale: {
      label: "Review out of date",
      detail:
        "The workflow or its evidence has changed. A new review is needed before these results can be approved.",
    },
    expired: {
      label: "Review expired",
      detail: "This review can no longer be approved. A new review is needed.",
    },
    consumed: {
      label: "Review recorded",
      detail:
        "This review has already been used to continue the workflow. Check the current run status for subsequent results.",
    },
  };
  return presentations[checkpoint.state];
}

export function externallyManagedReview(
  checkpoint: WorkflowApprovalCheckpoint,
): boolean {
  const context = checkpoint.continuation.execution_context;
  return (
    checkpoint.action_kind === "local_review" &&
    !!context &&
    typeof context === "object" &&
    "campaign_id" in context &&
    typeof context.campaign_id === "string" &&
    !!context.campaign_id
  );
}

// Use the recorded review package, not filenames guessed from block settings.
// An unbound continuation path must never masquerade as reviewed evidence.
export function reviewFiles(checkpoint: WorkflowApprovalCheckpoint): string[] {
  const files = checkpoint.continuation.artifact_files;
  const digests = checkpoint.subject.artifact_digests;
  if (!Array.isArray(files) || !Array.isArray(digests)) return [];
  return [
    ...new Set(
      files.flatMap((file: unknown) => {
        if (
          !file ||
          typeof file !== "object" ||
          !("path" in file) ||
          !("sha256" in file)
        )
          return [];
        return typeof file.path === "string" &&
          file.path &&
          !/^(?:[\\/]|[a-z][a-z0-9+.-]*:)/i.test(file.path) &&
          !file.path
            .split(/[\\/]/)
            .some((part) => !part || part === "." || part === "..") &&
          typeof file.sha256 === "string" &&
          /^[a-f0-9]{64}$/i.test(file.sha256) &&
          digests.includes(file.sha256)
          ? [file.path]
          : [];
      }),
    ),
  ].sort((a, b) => {
    const order = [
      "Document",
      "Plot or image",
      "Data table",
      "Model",
      "Supporting file",
    ];
    return (
      order.indexOf(fileKind(a)) - order.indexOf(fileKind(b)) ||
      a.localeCompare(b)
    );
  });
}

// Same canonical task-to-block mapping used by the run activity projection.
export const taskBlockId = (taskId: string) =>
  `block.${taskId.replaceAll("_", "-")}`;

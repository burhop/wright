export interface ValidationProgress {
  readonly kind: string;
  readonly status?: string;
  readonly revision?: number;
  readonly remaining_revisions?: number;
  readonly assessment_id?: string;
  readonly assessment_path?: string;
  readonly complete_result_ref?: string;
  readonly report?: {
    readonly assessment_id?: string;
    readonly assessment_path?: string;
  };
}

export interface ValidationEvidenceReference {
  readonly assessmentId?: string;
  readonly path: string;
  readonly completeResultRef?: string;
}

export function validationEvidenceReference(
  progress: ValidationProgress | null | undefined,
): ValidationEvidenceReference | null {
  const raw = progress?.assessment_path ?? progress?.report?.assessment_path;
  if (typeof raw !== "string" || !raw.trim()) return null;
  const path = raw.trim().replaceAll("\\", "/");
  const parts = path.split("/");
  if (
    path.startsWith("/") ||
    /^[a-z]:\//i.test(path) ||
    parts.some((part) => part === "" || part === "." || part === "..")
  )
    return null;
  return {
    assessmentId: progress?.assessment_id ?? progress?.report?.assessment_id,
    path,
    completeResultRef: progress?.complete_result_ref,
  };
}

export function validationRunPresentation(
  progress: ValidationProgress | null | undefined,
): { label: string; detail: string } | null {
  if (!progress) return null;
  if (progress.kind === "validation_exhausted")
    return {
      label: "Correction budget exhausted",
      detail:
        "The current output still has findings. Downstream work remains held; open the saved assessment before starting a new run.",
    };
  if (
    progress.kind === "validation_feedback_delivered" ||
    progress.kind === "design_revision"
  )
    return {
      label: "Repairing output",
      detail: `${
        progress.revision ? `Correction revision ${progress.revision}. ` : ""
      }${
        progress.remaining_revisions === undefined
          ? "The producer is creating a new revision from measured findings."
          : `${progress.remaining_revisions} configured correction revision(s) remain at feedback delivery.`
      }`,
    };
  if (progress.kind === "design_check" && progress.status !== "pass")
    return {
      label:
        progress.status === "revise"
          ? "Output held for correction"
          : "Validation held",
      detail:
        progress.status === "revise"
          ? "Measured defects prevent release while the runner prepares bounded correction feedback."
          : "Downstream work remains held until missing evidence or validator capability is restored.",
    };
  return null;
}

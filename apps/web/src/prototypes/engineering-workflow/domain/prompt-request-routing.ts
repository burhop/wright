export type PromptRequestOutputKind =
  "request" | "text" | "images" | "documents";

export interface PromptRequestRouteSnapshot {
  promptPresent: boolean;
  imageCount: number;
  documentCount: number;
  readableDocumentCount: number;
}

export interface PromptRequestRouteIssue {
  code:
    | "OUTPUT_NOT_ACCEPTED"
    | "IMAGES_EMPTY"
    | "DOCUMENTS_EMPTY"
    | "DOCUMENT_TEXT_UNAVAILABLE"
    | "ATTACHMENTS_NOT_ROUTED";
  severity: "error" | "warning";
  message: string;
}

export const promptRequestOutputLabels: Record<
  PromptRequestOutputKind,
  string
> = {
  request: "Complete request",
  text: "Instructions",
  images: "Images",
  documents: "Documents",
};

export function promptRequestRouteIssues(
  snapshot: PromptRequestRouteSnapshot,
  output: PromptRequestOutputKind,
  acceptedOutputs: readonly PromptRequestOutputKind[],
): PromptRequestRouteIssue[] {
  const issues: PromptRequestRouteIssue[] = [];

  if (!acceptedOutputs.includes(output)) {
    issues.push({
      code: "OUTPUT_NOT_ACCEPTED",
      severity: "error",
      message: `${promptRequestOutputLabels[output]} is not accepted by the connected block.`,
    });
  }

  if (output === "images" && snapshot.imageCount === 0) {
    issues.push({
      code: "IMAGES_EMPTY",
      severity: "error",
      message: "The Images output is selected, but no images are attached.",
    });
  }

  if (output === "documents" && snapshot.documentCount === 0) {
    issues.push({
      code: "DOCUMENTS_EMPTY",
      severity: "error",
      message:
        "The Documents output is selected, but no documents are attached.",
    });
  }

  if (
    output === "request" &&
    snapshot.documentCount > snapshot.readableDocumentCount
  ) {
    const unavailable = snapshot.documentCount - snapshot.readableDocumentCount;
    issues.push({
      code: "DOCUMENT_TEXT_UNAVAILABLE",
      severity: "error",
      message: `${unavailable} document${unavailable === 1 ? "" : "s"} need an explicit parser before this AI block can consume them.`,
    });
  }

  if (output === "text" && snapshot.imageCount + snapshot.documentCount > 0) {
    issues.push({
      code: "ATTACHMENTS_NOT_ROUTED",
      severity: "warning",
      message: `${snapshot.imageCount} image${snapshot.imageCount === 1 ? "" : "s"} and ${snapshot.documentCount} document${snapshot.documentCount === 1 ? "" : "s"} are intentionally not routed on this connection.`,
    });
  }

  return issues;
}

export function promptRequestRouteCanRun(
  issues: readonly PromptRequestRouteIssue[],
): boolean {
  return issues.every(({ severity }) => severity !== "error");
}

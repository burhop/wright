import { useEffect, useState } from "react";
import {
  workspaceService,
  type WorkflowApprovalCheckpoint,
} from "../../services/workspace-service";
import { EngineeringFiles } from "./EngineeringRunContext";
import {
  fileKind,
  fileName,
  reviewFiles,
} from "./engineering-run-presentation";

const imageTypes: Record<string, string> = {
  svg: "image/svg+xml",
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  webp: "image/webp",
};

export function ReviewImage({
  path,
  sha256,
  sessionId,
  onOpenFile,
}: {
  path: string;
  sha256: string;
  sessionId: string;
  onOpenFile?: (path: string) => void;
}) {
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let current = true;
    let objectUrl = "";
    setPreview("");
    setError("");
    async function load() {
      try {
        const bytes = await workspaceService.getFileContentArrayBuffer(
          sessionId,
          path,
        );
        if (!current) return;
        if (bytes.byteLength > 20 * 1024 * 1024) {
          setError(
            "This image is too large for an inline preview. Open the file to inspect it.",
          );
          return;
        }
        const digest = Array.from(
          new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
        )
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");
        if (!current) return;
        if (digest !== sha256.toLowerCase()) {
          setError(
            "This file has changed since the review was prepared. A new review is needed.",
          );
          return;
        }
        // Render SVG as an image, never as executable inline markup.
        objectUrl = URL.createObjectURL(
          new Blob([bytes], {
            type: imageTypes[path.split(".").at(-1)!.toLowerCase()],
          }),
        );
        setPreview(objectUrl);
      } catch {
        if (current)
          setError("Preview unavailable. Open the file to inspect it.");
      }
    }
    void load();
    return () => {
      current = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [path, sha256, sessionId]);
  return (
    <figure
      className="recovery-review-image"
      data-testid="workflow-review-image"
    >
      <figcaption>
        <b title={path}>{fileName(path)}</b>
      </figcaption>
      {preview && !error && (
        <img
          src={preview}
          alt={`Preview of ${fileName(path)}`}
          onError={() =>
            setError(
              "This image could not be displayed. Open the file to inspect it.",
            )
          }
        />
      )}
      {!preview && !error && <p role="status">Loading the recorded image…</p>}
      {error && <p role="alert">{error}</p>}
      {onOpenFile && (
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          title={path}
          aria-label={`Open ${fileName(path)}`}
          onClick={() => onOpenFile(path)}
        >
          Open full-size image
        </button>
      )}
    </figure>
  );
}

export function EngineeringReviewFiles({
  checkpoint,
  sessionId,
  onOpenFile,
}: {
  checkpoint: WorkflowApprovalCheckpoint;
  sessionId: string;
  onOpenFile?: (path: string) => void;
}) {
  const files = reviewFiles(checkpoint);
  const records = (checkpoint.continuation.artifact_files ?? []) as {
    path: string;
    sha256: string;
  }[];
  // Keep the producer's recorded order for figures, rather than alphabetically
  // promoting a secondary comparison ahead of its main result.
  const images = files
    .filter((path) => fileKind(path) === "Plot or image")
    .sort(
      (a, b) =>
        records.findIndex((r) => r?.path === a) -
        records.findIndex((r) => r?.path === b),
    );
  const documents = files.filter((path) => fileKind(path) === "Document");
  const supporting = files.filter(
    (path) => !images.includes(path) && !documents.includes(path),
  );
  const boundRecord = (path: string) =>
    records.find(
      (r) =>
        r?.path === path &&
        typeof r.sha256 === "string" &&
        Array.isArray(checkpoint.subject.artifact_digests) &&
        checkpoint.subject.artifact_digests.includes(r.sha256),
    )!;
  return (
    <section data-testid="workflow-review-files">
      <h4>Results to inspect</h4>
      {!files.length ? (
        <p role="status">
          No file links are recorded in this review package. Locate the evidence
          before approving; do not assume a listed requirement has passed.
        </p>
      ) : (
        <>
          <p>
            Inspect the plots, read the findings, then check the requirements
            below. These are the files recorded for this review; changed
            evidence needs a new review.
          </p>
          {!!images.length && (
            <section
              aria-label="Plots and images"
              className="recovery-review-images"
            >
              {images.map((path) => (
                <ReviewImage
                  key={`${sessionId}:${path}:${boundRecord(path).sha256}`}
                  path={path}
                  sha256={boundRecord(path).sha256}
                  sessionId={sessionId}
                  onOpenFile={onOpenFile}
                />
              ))}
            </section>
          )}
          {!!documents.length && (
            <section aria-label="Findings and explanations">
              <h4>Findings and explanations</h4>
              <EngineeringFiles paths={documents} onOpenFile={onOpenFile} />
            </section>
          )}
          {!!supporting.length && (
            <details>
              <summary>
                Supporting data and calculation records ({supporting.length})
              </summary>
              <EngineeringFiles paths={supporting} onOpenFile={onOpenFile} />
            </details>
          )}
        </>
      )}
    </section>
  );
}

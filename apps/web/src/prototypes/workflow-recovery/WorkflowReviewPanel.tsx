import { useEffect, useState } from "react";
import {
  workspaceService,
  type WorkspaceWorkflowReview,
} from "../../services/workspace-service";
import { workspaceContentUrl } from "../../services/viewer-panel/providers/workspace-content-url";

export function useWorkflowReviews(
  sessionId: string | undefined,
  path: string,
  refreshKey: string,
  latest?: WorkspaceWorkflowReview,
) {
  const [reviews, setReviews] = useState<WorkspaceWorkflowReview[]>([]);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let current = true;
    setReviews(latest?.workflow_path === path ? [latest] : []);
    setError("");
    if (sessionId)
      void workspaceService
        .getWorkspaceWorkflowReviews(sessionId, path)
        .then((value) => {
          if (current) setReviews(value);
        })
        .catch((cause) => {
          if (current)
            setError(
              cause instanceof Error
                ? cause.message
                : "Document reviews could not be loaded.",
            );
        });
    return () => {
      current = false;
    };
  }, [sessionId, path, refreshKey, latest, retry]);
  return {
    reviews,
    error,
    refresh: () => setRetry((value) => value + 1),
    update: (review: WorkspaceWorkflowReview) =>
      setReviews((current) =>
        current.map((item) =>
          item.review_id === review.review_id ? review : item,
        ),
      ),
  };
}

export function WorkflowReviewPanel({
  review,
  sessionId,
  onOpenFile,
  onUpdate,
  onRefresh,
}: {
  review: WorkspaceWorkflowReview;
  sessionId: string;
  onOpenFile?: (path: string) => void;
  onUpdate: (review: WorkspaceWorkflowReview) => void;
  onRefresh: () => void;
}) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    setError("");
  }, [review]);
  const pending = review.state === "pending";
  const stale = review.evidence_status === "stale";
  const decide = async (decision: "approved" | "changes_requested") => {
    if (
      busy ||
      error ||
      stale ||
      !pending ||
      (decision === "changes_requested" && !reason.trim())
    )
      return;
    setBusy(true);
    try {
      onUpdate(
        await workspaceService.decideWorkspaceWorkflowReview(
          sessionId,
          review,
          decision,
          reason.trim(),
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Your decision could not be recorded. Refresh reviews before trying again.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <section
      className="recovery-native-run__input recovery-document-review"
      data-testid="workflow-document-review"
    >
      <h3>
        {pending
          ? "Awaiting your review"
          : review.state === "approved"
            ? "Review approved"
            : "Changes requested"}{" "}
        · {review.task_title}
      </h3>
      <p style={{ whiteSpace: "pre-wrap" }}>{review.instructions}</p>
      {stale && (
        <p role="alert">
          {review.evidence_message ||
            "The workflow or reviewed files have changed."}{" "}
          Run the workflow again to create a current review package. Any
          recorded decision applies only to the original package.
        </p>
      )}
      {review.artifacts.map((artifact) => (
        <p key={artifact.output_path}>
          {onOpenFile ? (
            <button
              type="button"
              className="recovery-button recovery-button--secondary"
              data-testid={`review-open-${review.review_id}-${artifact.output_path}`}
              onClick={() => onOpenFile(artifact.output_path)}
            >
              Open {artifact.output_path}
            </button>
          ) : (
            <a
              href={workspaceContentUrl(artifact.output_path, sessionId)}
              target="_blank"
              rel="noreferrer"
            >
              Open {artifact.output_path}
            </a>
          )}
          <small> · {artifact.output_bytes.toLocaleString()} bytes</small>
        </p>
      ))}
      <details>
        <summary data-testid={`review-identity-${review.review_id}`}>
          Reviewed package identity
        </summary>
        <p>
          Run: <code>{review.run_id}</code>
        </p>
        <p>
          Saved workflow: <code>{review.source_digest}</code>
        </p>
        <p>
          Review package: <code>{review.package_digest}</code>
        </p>
        {review.artifacts.map((artifact) => (
          <p key={artifact.output_path}>
            {artifact.output_path}
            <br />
            <code>{artifact.sha256}</code>
          </p>
        ))}
      </details>
      {pending ? (
        <>
          <label>
            Review notes (required for changes)
            <textarea
              data-testid={`review-notes-${review.review_id}`}
              rows={3}
              value={reason}
              disabled={busy}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
          <div className="recovery-authoring-settings__actions">
            <button
              type="button"
              className="recovery-button recovery-button--primary"
              disabled={busy || stale || Boolean(error)}
              data-testid={`review-approve-${review.review_id}`}
              onClick={() => void decide("approved")}
            >
              Approve
            </button>
            <button
              type="button"
              className="recovery-button recovery-button--secondary"
              disabled={busy || stale || Boolean(error) || !reason.trim()}
              data-testid={`review-changes-${review.review_id}`}
              onClick={() => void decide("changes_requested")}
            >
              Request changes
            </button>
          </div>
          <small>
            This records your decision on these files. It does not run more
            steps or submit an order.
          </small>
        </>
      ) : (
        <p>
          {review.reason && (
            <>
              {review.reason}
              <br />
            </>
          )}
          {review.decided_at && (
            <>Recorded {new Date(review.decided_at).toLocaleString()}.</>
          )}
        </p>
      )}
      <p>
        <small>
          Your decision is recorded for this local workspace; reviewer identity
          is not authenticated.
        </small>
      </p>
      {busy && <p role="status">Recording your decision…</p>}
      {error && (
        <div role="alert">
          <p>{error}</p>
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            data-testid={`review-refresh-${review.review_id}`}
            onClick={onRefresh}
          >
            Refresh reviews
          </button>
        </div>
      )}
    </section>
  );
}

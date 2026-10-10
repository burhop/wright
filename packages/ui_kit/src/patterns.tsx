import { useEffect, useId, useState, type ReactNode } from "react";
import type {
  Action,
  ArtifactRef,
  NavigationTarget,
  Observation,
  OutputRef,
  PendingInteraction,
  Readiness,
  Reason,
  InteractionSnapshot,
  JsonValue,
} from "@wright/process-client";
import { SchemaField, schemaFieldError } from "./inputs";

export const UI_KIT_VERSION = "1.0.0";
export type Navigate = (target: NavigationTarget) => void;
export function NavigationButton({
  target,
  title,
  onNavigate,
}: {
  target: NavigationTarget;
  title: string;
  onNavigate?: Navigate;
}) {
  return (
    <button
      type="button"
      className="wp-link"
      disabled={!onNavigate}
      onClick={() => onNavigate?.(target)}
    >
      {title}
    </button>
  );
}
/** Readable projection supplied by the owning assessment service, never a verdict generator. */
export function FindingsPanel({
  findings,
  onNavigate,
  status = "available",
}: {
  findings: readonly Reason[];
  onNavigate?: Navigate;
  status?: "available" | "not_loaded" | "unavailable";
}) {
  return (
    <div className="wp-findings">
      {status !== "available" ? (
        <p className="wp-muted">
          {status === "not_loaded"
            ? "Open the linked assessment to load its findings."
            : "Findings are unavailable in this view. Inspect the linked assessment and evidence."}
        </p>
      ) : findings.length ? (
        findings.map((finding, index) => (
          <ReasonNotice
            key={`${finding.code}-${index}`}
            reason={finding}
            tone="info"
            onNavigate={onNavigate}
          />
        ))
      ) : (
        <p className="wp-muted">
          No findings were reported in this view. Check the linked assessment
          for its scope; this is not an approval.
        </p>
      )}
    </div>
  );
}
export function ProcessUI({
  children,
  theme,
  className = "",
}: {
  children: ReactNode;
  theme?: "dark" | "light";
  className?: string;
}) {
  return (
    <div className={`wright-process-ui ${className}`} data-theme={theme}>
      {children}
    </div>
  );
}
export function Section({
  title,
  description,
  children,
  focusId,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  focusId?: string;
}) {
  const id = useId();
  return (
    <section
      className="wp-section"
      aria-labelledby={id}
      data-process-section={focusId}
      tabIndex={focusId ? -1 : undefined}
    >
      <h2 id={id}>{title}</h2>
      {description && <p className="wp-muted">{description}</p>}
      {children}
    </section>
  );
}
export function ReasonNotice({
  reason,
  onNavigate,
  tone = "error",
}: {
  reason: Reason;
  onNavigate?: Navigate;
  tone?: "error" | "warning" | "info";
}) {
  return (
    <div
      className={`wp-notice wp-notice--${tone}`}
      role={tone === "error" ? "alert" : "status"}
    >
      <p>{reason.message}</p>
      <p className="wp-correction">{reason.correction}</p>
      {reason.navigation && onNavigate && (
        <button
          type="button"
          className="wp-link"
          onClick={() => onNavigate(reason.navigation!)}
        >
          Open related item
        </button>
      )}
      <details>
        <summary>Technical details</summary>
        <code>{reason.code}</code>
        {reason.technical_details_ref && <p>{reason.technical_details_ref}</p>}
      </details>
    </div>
  );
}
export function ActionButton({
  action,
  onAction,
  busy = false,
  readOnly = false,
  onNavigate,
  compactReasons = false,
}: {
  action: Action;
  onAction?: (action: Action) => void;
  busy?: boolean;
  readOnly?: boolean;
  onNavigate?: Navigate;
  compactReasons?: boolean;
}) {
  const id = useId();
  const enabled = action.enabled && !!onAction && !busy && !readOnly;
  return (
    <div className="wp-action">
      <button
        type="button"
        className="wp-button"
        disabled={!enabled}
        aria-busy={busy || undefined}
        aria-describedby={!enabled ? id : undefined}
        onClick={() => {
          if (enabled) onAction?.(action);
        }}
      >
        {busy ? "Working…" : action.title}
      </button>
      {!enabled && compactReasons ? (
        <details id={id} className="wp-action-reasons">
          <summary>Why unavailable</summary>
          {(action.reasons ?? []).map((reason, index) => (
            <ReasonNotice key={`${reason.code}-${index}`} reason={reason} tone="info" onNavigate={onNavigate} />
          ))}
          {!action.reasons?.length && <p className="wp-muted">
            {readOnly ? "This view is read-only." : busy ? "Waiting for Wright to confirm the request." : !onAction ? "This action is unavailable in this view." : "The process has not permitted this action."}
          </p>}
        </details>
      ) : !enabled && (
        <div id={id}>
          {(action.reasons ?? []).map((reason, index) => (
            <ReasonNotice
              key={`${reason.code}-${index}`}
              reason={reason}
              tone="info"
              onNavigate={onNavigate}
            />
          ))}
          {!action.reasons?.length && (
            <p className="wp-muted">
              {readOnly
                ? "This view is read-only."
                : busy
                  ? "Waiting for Wright to confirm the request."
                  : !onAction
                    ? "This action is unavailable in this view."
                    : "The process has not permitted this action."}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
const dependencyLabels = {
  supplied: "Provided",
  explicit_default: "Declared default",
  upstream_produced: "Produced by an earlier step",
  declared_human_response: "Provided at a declared interaction",
  unresolved: "Needs input",
};
export function ReadinessPanel({
  readiness,
  onNavigate,
  now,
}: {
  readiness?: Readiness | null;
  onNavigate?: Navigate;
  now?: number;
}) {
  const [clock, setClock] = useState(Date.now);
  useEffect(() => {
    if (now !== undefined) return;
    const timer = setInterval(() => setClock(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [now]);
  const expired =
    readiness?.state === "ready" &&
    !!readiness.expires_at &&
    (!Number.isFinite(Date.parse(readiness.expires_at)) ||
      Date.parse(readiness.expires_at) <= (now ?? clock));
  return (
    <div className="wp-readiness" role="status">
      <strong>
        {!readiness
          ? "Readiness has not been checked"
          : expired
            ? "Readiness needs refreshing"
            : readiness.state === "ready"
              ? "Ready to start"
              : readiness.state === "blocked"
                  ? "Not ready to start"
                : "This process needs a supported configuration"}
      </strong>
      {(readiness?.reasons ?? []).map((reason, index) => (
        <ReasonNotice
          key={`${reason.code}-${index}`}
          reason={reason}
          tone="info"
          onNavigate={onNavigate}
        />
      ))}
      {!!readiness?.dependencies?.length && (
        <details>
          <summary>How later inputs are supplied</summary>
          <ul>
            {readiness.dependencies.map((dependency) => (
              <li key={dependency.binding_id}>
                {dependency.binding_id}:{" "}
                {dependencyLabels[dependency.classification]}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
const stateLabels: Record<InteractionSnapshot["state"], string> = {
  preparing: "Preparing",
  ready: "Ready",
  running: "Running",
  waiting_human: "Waiting for your review or response",
  waiting_external: "Waiting for an external operation",
  reconciliation_required: "Status needs reconciliation",
  completed: "Process completed",
  failed: "Process needs attention",
  cancelled: "Process cancelled",
  cancellation_requested: "Cancellation requested",
};
const observationStateLabels: Record<Observation["state"], string> = {
  preparing: "Preparing",
  ready: "Ready",
  running: "Running",
  waiting_human: "Waiting for a review or response",
  waiting_external: "Waiting for an external operation",
  reconciliation_required: "Needs reconciliation",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
  cancellation_requested: "Cancellation requested",
};
export function ProgressPanel({
  state,
  observations,
  now,
  activity,
  connection,
}: {
  state: InteractionSnapshot["state"];
  observations: readonly Observation[];
  now?: number;
  activity?: string;
  connection?: "connected" | "reconnecting";
}) {
  const [clock, setClock] = useState(Date.now);
  useEffect(() => {
    if (now !== undefined) return;
    const timer = setInterval(() => setClock(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [now]);
  const currentTime = now ?? clock;
  return (
    <div className="wp-progress" aria-live="polite">
      <strong>{stateLabels[state]}</strong>
      {activity && <p>{activity}</p>}
      {connection === "reconnecting" && (
        <p className="wp-muted">Reconnecting to the saved run…</p>
      )}
      {state === "cancellation_requested" && (
        <p>
          Waiting for the actual outcome. The request does not confirm that the
          operation has stopped.
        </p>
      )}
      {state === "reconciliation_required" && (
        <p>Check the recorded outcome before repeating an action.</p>
      )}
      {observations.map((observation) => {
        const observed = Date.parse(observation.observed_at),
          deadline = observation.stale_after
            ? Date.parse(observation.stale_after)
            : null;
        const terminal = ["completed", "failed", "cancelled"].includes(
          observation.state,
        );
        const stale =
          !Number.isFinite(observed) ||
          observed > currentTime ||
          (!terminal &&
            (deadline === null ||
              !Number.isFinite(deadline) ||
              deadline <= currentTime));
        const percent =
          !stale &&
          typeof observation.progress_percent === "number" &&
          Number.isFinite(observation.progress_percent)
            ? observation.progress_percent
            : null;
        const remaining =
          !terminal &&
          !stale &&
          typeof observation.estimated_remaining_seconds === "number" &&
          Number.isFinite(observation.estimated_remaining_seconds)
            ? observation.estimated_remaining_seconds
            : null;
        return (
          <div className="wp-observation" key={observation.observation_id}>
            <p className="wp-muted">Reported by {observation.provider_binding}</p>
            <p>Observed state: {observationStateLabels[observation.state]}</p>
            {observation.activity && <p>{observation.activity}</p>}
            {stale ? (
              <p className="wp-muted">
                This status needs a fresh observation; progress and time are
                unavailable.
              </p>
            ) : (
              <>
                {percent !== null && (
                  <>
                    <progress
                      max={100}
                      value={percent}
                      aria-label="Observed completion"
                    />
                    <span>
                      {percent.toLocaleString()}%{" "}
                      {terminal ? "last reported" : "complete"}
                    </span>
                  </>
                )}
                {remaining !== null && (
                  <p>
                    {remaining < 60
                      ? `${Math.ceil(remaining)} sec`
                      : `${Math.ceil(remaining / 60)} min`}{" "}
                    remaining (observed estimate)
                  </p>
                )}
                {percent === null &&
                  remaining === null &&
                  ["running", "waiting_external", "cancellation_requested"].includes(
                    observation.state,
                  ) && (
                  <p className="wp-muted">
                    The provider has not supplied a percentage or remaining
                    time.
                  </p>
                )}
              </>
            )}
            <p className="wp-muted">
              Last observed{" "}
              <time dateTime={observation.observed_at}>
                {observation.observed_at}
              </time>
            </p>
            {(observation.limitations ?? []).map((limitation, index) => (
              <p className="wp-muted" key={index}>
                {limitation}
              </p>
            ))}
            <details>
              <summary>Observation details</summary>
              <p>Provider: {observation.provider_binding}</p>
              {observation.operation_id && (
                <p>Operation: {observation.operation_id}</p>
              )}
              {observation.metrics && (
                <pre>{JSON.stringify(observation.metrics, null, 2)}</pre>
              )}
            </details>
          </div>
        );
      })}
    </div>
  );
}
export function EvidenceReference({
  reference,
  onOpen,
}: {
  reference: ArtifactRef;
  onOpen?: (reference: ArtifactRef) => void;
}) {
  const filename = reference.artifact_ref.split(/[\\/]/).filter(Boolean).at(-1)
    || reference.artifact_ref;
  return (
    <div className="wp-evidence">
      <span>{filename}</span>
      <button
        type="button"
        className="wp-link"
        disabled={!onOpen}
        onClick={() => onOpen?.(reference)}
      >
        Open file
      </button>
      <details>
        <summary>File details</summary>
        <p><code>{reference.artifact_ref}</code></p>
        <code>{reference.sha256}</code>
        {reference.result_id && <p>{reference.result_id}</p>}
      </details>
    </div>
  );
}
const assessmentLabels = {
  pass: "Passed",
  fail: "Failed",
  blocked: "Blocked",
  inconclusive: "Inconclusive",
  error: "Assessment error",
  not_applicable: "Not applicable",
};
export function ResultCard({
  output,
  onNavigate,
  onOpen,
  children,
}: {
  output: OutputRef;
  onNavigate?: Navigate;
  onOpen?: (reference: ArtifactRef) => void;
  children?: ReactNode;
}) {
  return (
    <article
      className="wp-result"
      data-result-id={output.result_id}
      tabIndex={-1}
    >
      <h3>{output.title}</h3>
      <p className="wp-muted">{output.role === "previous_attempt" ? "Historical evidence · superseded output" : output.role}</p>
      {children}
      {(output.representations ?? []).map((reference) => (
        <EvidenceReference
          key={`${reference.artifact_ref}:${reference.sha256}`}
          reference={reference}
          onOpen={onOpen}
        />
      ))}
      {!output.representations?.length && (
        <p className="wp-muted">
          No representation is available for this result.
        </p>
      )}
      <div className="wp-findings">
        {(output.assessments ?? []).map((assessment) => (
          <div
            key={assessment.assessment_id}
            data-assessment-id={assessment.assessment_id}
            tabIndex={-1}
          >
            <strong className={`wp-check wp-check--${assessment.outcome}`}>
              {assessmentLabels[assessment.outcome]}
            </strong>
            <span>
              {assessment.currentness !== "current"
                ? ` · ${assessment.currentness}`
                : ""}
            </span>
            <button
              type="button"
              className="wp-link"
              disabled={!onNavigate}
              onClick={() =>
                onNavigate?.({
                  kind: "assessment",
                  assessment_id: assessment.assessment_id,
                  result_id: output.result_id,
                })
              }
            >
              Open assessment
            </button>
          </div>
        ))}
      </div>
      {!output.assessments?.length && (
        <p className="wp-muted">
          No assessment is linked here. Rendering is not verification.
        </p>
      )}
      <button
        type="button"
        className="wp-link"
        disabled={!onNavigate}
        onClick={() =>
          onNavigate?.({
            kind: "block",
            block_id: output.step_id,
            result_id: output.result_id,
          })
        }
      >
        Open producing step
      </button>
      <details>
        <summary>Result identity</summary>
        <code>{output.result_id}</code>
        {output.revision_id && <p>Revision: {output.revision_id}</p>}
        {output.producer_attempt && <p>Attempt: {output.producer_attempt}</p>}
      </details>
    </article>
  );
}
export function CheckpointCard({
  interaction,
  actions,
  onAction,
  onOpen,
  onNavigate,
  children,
  response,
  review,
  execution,
}: {
  interaction: PendingInteraction;
  actions: readonly Action[];
  onAction?: (action: Action) => void;
  onOpen?: (reference: ArtifactRef) => void;
  onNavigate?: Navigate;
  children?: ReactNode;
  response?: {
    value?: JsonValue;
    onChange: (value?: JsonValue) => void;
    onSubmit: (action: Action, value: JsonValue) => void;
    busy?: boolean;
    readOnly?: boolean;
    blockedReason?: Reason;
  };
  review?: {
    reason: string;
    onReasonChange: (reason: string) => void;
    onSubmit: (
      action: Action,
      decision: "approved" | "changes_requested",
      reason: string,
    ) => void;
    busy?: boolean;
    readOnly?: boolean;
    blockedReason?: Reason;
  };
  execution?: {
    onSubmit: (action: Action) => void;
    busy?: boolean;
    readOnly?: boolean;
    blockedReason?: Reason;
  };
}) {
  const reasonId = useId();
  const [confirmedSubject, setConfirmedSubject] = useState<string>();
  const responseError = interaction.kind === "input" && response?.value !== undefined && interaction.response_schema
    ? schemaFieldError(interaction.response_schema, response.value, true)
    : undefined;
  const responseBlockedReason = response?.blockedReason ?? (responseError ? {
    code: "INPUT_REQUIRED",
    message: responseError,
    correction: "Correct the response fields above before submitting.",
  } : undefined);
  const matching = actions.filter(
    (action) =>
      action.checkpoint_id === interaction.checkpoint_id &&
      action.subject_digest === interaction.subject_digest &&
      ["respond", "review", "action"].includes(action.operation),
  );
  return (
    <article className="wp-checkpoint">
      <h3>
        {interaction.kind === "input"
          ? "Provide the declared response"
          : interaction.kind === "review"
            ? "Review the result"
            : "Review the next action"}
      </h3>
      <p>{interaction.instructions}</p>
      {interaction.decision && (
        <div className="wp-muted">
          <p>
            {interaction.decision.integration_test
              ? "Test review recorded: "
              : "Review recorded: "}
            {interaction.decision.decision === "approved"
              ? "Approved"
              : "Changes requested"}
          </p>
          {interaction.decision.reason && <p>{interaction.decision.reason}</p>}
        </div>
      )}
      {interaction.action_receipt && (
        <div className="wp-muted" aria-live="polite">
          <p>
            {interaction.action_receipt.submission === "authorized"
              ? "Action authorized; provider acceptance is not confirmed yet."
              : interaction.action_receipt.submission === "accepted"
                ? "Provider accepted the action."
                : interaction.action_receipt.submission === "rejected"
                  ? "Provider rejected the action."
                  : "Submission outcome is unknown; reconcile before another action."}
          </p>
          {interaction.action_receipt.observed_outcome && (
            <p>
              Observed outcome: {interaction.action_receipt.observed_outcome}
            </p>
          )}
          {interaction.action_receipt.cancellation_requested && (
            <p>
              Cancellation requested.
              {interaction.action_receipt.cancellation_outcome
                ? ` Observed cancellation outcome: ${interaction.action_receipt.cancellation_outcome}.`
                : " Waiting for an observed outcome."}
            </p>
          )}
        </div>
      )}
      <div className={`wp-checkpoint-content${interaction.evidence?.length ? " wp-checkpoint-content--with-evidence" : ""}`}>
      {!!interaction.evidence?.length && <div className="wp-checkpoint-evidence">
      <h4>Files for this review</h4>
      {interaction.evidence.map((reference) => (
        <EvidenceReference
          key={`${reference.artifact_ref}:${reference.sha256}`}
          reference={reference}
          onOpen={onOpen}
        />
      ))}
      </div>}
      <div className="wp-checkpoint-controls">
      {children}
      {review &&
        interaction.decisions?.some(
          (choice) => choice !== "approved" && choice !== "changes_requested",
        ) && (
          <p className="wp-muted">
            Some declared review choices are unsupported in this view. Open the
            interaction step to inspect them.
          </p>
        )}
      {review &&
        (!interaction.decision ||
          matching.some(
            (item) => item.operation === "review" && item.enabled,
          )) &&
        matching.some((item) => item.operation === "review") &&
        !!interaction.decisions?.length && (
          <div className="wp-field wp-review-controls">
            <label htmlFor={reasonId}>Review reason</label>
            <textarea
              id={reasonId}
              value={review.reason}
              maxLength={2000}
              disabled={
                review.busy ||
                review.readOnly ||
                !matching.some(
                  (item) => item.operation === "review" && item.enabled,
                )
              }
              onChange={(event) => review.onReasonChange(event.target.value)}
            />
            <p className="wp-muted">
              Explain requested changes. A reason is optional for approval.
            </p>
            {matching
              .filter((item) => item.operation === "review")
              .flatMap((item) =>
                (interaction.decisions ?? [])
                  .filter(
                    (choice): choice is "approved" | "changes_requested" =>
                      choice === "approved" || choice === "changes_requested",
                  )
                  .map((choice) => {
                    const blocked =
                      review.blockedReason ??
                      (choice === "changes_requested" && !review.reason.trim()
                        ? {
                            code: "INPUT_REQUIRED",
                            message:
                              "Explain the changes needed before submitting.",
                            correction: "Enter a review reason above.",
                          }
                        : undefined);
                    return (
                      <ActionButton
                        compactReasons
                        key={`${item.action_id}:${choice}`}
                        action={{
                          ...item,
                          title:
                            choice === "approved"
                              ? "Approve"
                              : "Request changes",
                          ...(item.enabled && blocked
                            ? { enabled: false, reasons: [blocked] }
                            : {}),
                        }}
                        busy={review.busy}
                        readOnly={review.readOnly}
                        onAction={
                          interaction.state === undefined ||
                          interaction.state === "waiting"
                            ? () => review.onSubmit(item, choice, review.reason)
                            : undefined
                        }
                        onNavigate={onNavigate}
                      />
                    );
                  }),
              )}
          </div>
        )}
      {execution &&
        matching.some(
          (item) => item.operation === "action" && item.enabled,
        ) && (
          <label className="wp-field">
            <input
              type="checkbox"
              checked={confirmedSubject === interaction.subject_digest}
              disabled={execution.busy || execution.readOnly}
              onChange={(event) =>
                setConfirmedSubject(
                  event.target.checked ? interaction.subject_digest : undefined,
                )
              }
            />
            I reviewed this action and its evidence
          </label>
        )}
      {interaction.kind === "input" &&
        response &&
        interaction.response_schema && (
          <SchemaField
            schema={interaction.response_schema}
            title="Your response"
            value={response.value}
            onChange={response.onChange}
            disabled={
              response.readOnly ||
              response.busy ||
              (interaction.state !== undefined &&
                interaction.state !== "waiting")
            }
            required
          />
        )}
      {matching
        .filter(
          (item) =>
            !(
              execution &&
              item.operation === "action" &&
              interaction.action_receipt
            ) &&
            !(
              review &&
              item.operation === "review" &&
              interaction.decisions?.length
            ),
        )
        .map((action) => (
          <ActionButton
            compactReasons={interaction.kind !== "input"}
            key={action.action_id}
            action={
              action.operation === "respond" &&
              response &&
              action.enabled &&
              (responseBlockedReason || response.value === undefined)
                ? {
                    ...action,
                    enabled: false,
                    reasons: [
                      responseBlockedReason ?? {
                        code: "INPUT_REQUIRED",
                        message:
                          "Provide the declared response before submitting.",
                        correction:
                          "Complete the response fields above. Wright will validate the answer before continuing.",
                      },
                    ],
                  }
                : action.operation === "action" &&
                    execution &&
                    action.enabled &&
                    (execution.blockedReason ||
                      confirmedSubject !== interaction.subject_digest)
                  ? {
                      ...action,
                      enabled: false,
                      reasons: [
                        execution.blockedReason ?? {
                          code: "INPUT_REQUIRED",
                          message:
                            "Review and confirm this action before continuing.",
                          correction:
                            "Inspect its evidence and select the confirmation above.",
                        },
                      ],
                    }
                  : action
            }
            onAction={
              interaction.state === undefined || interaction.state === "waiting"
                ? action.operation === "respond" && response
                  ? response.value === undefined
                    ? undefined
                    : () => response.onSubmit(action, response.value!)
                  : action.operation === "action" && execution
                    ? () => execution.onSubmit(action)
                    : onAction
                : undefined
            }
            busy={response?.busy || review?.busy || execution?.busy}
            readOnly={
              response?.readOnly || review?.readOnly || execution?.readOnly
            }
            onNavigate={onNavigate}
          />
        ))}
      {!matching.length && (
        <p className="wp-muted">
          No permitted response action is available in this view.
        </p>
      )}
      </div>
      </div>
      <details>
        <summary>Checkpoint identity</summary>
        <code>{interaction.checkpoint_id}</code>
        <p>Subject: {interaction.subject_digest}</p>
        {interaction.decision && (
          <>
            <p>Decision actor: {interaction.decision.actor}</p>
            {interaction.decision.request_id && (
              <p>Review request: {interaction.decision.request_id}</p>
            )}
          </>
        )}
      </details>
    </article>
  );
}

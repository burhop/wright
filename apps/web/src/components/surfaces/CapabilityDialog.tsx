import { useEffect, useId, useRef } from "react";

import "./CapabilityDialog.css";

export type CapabilityRisk = "low" | "high" | "mutating";
export type CapabilityDecision = "allow" | "deny" | "cancel";

export interface CapabilityConsentRequest {
  sourceTitle: string;
  sourceId: string;
  sourceVersion: string;
  workspaceName: string;
  operation: string;
  dataDescription: string;
  risk: CapabilityRisk;
  reason: string;
  effectivePolicy: string;
  duration: string;
  expiresAt: string;
  persistence: string;
  denialConsequence: string;
  administratorOnly: boolean;
}

export interface CapabilityDialogProps {
  request: CapabilityConsentRequest;
  actorRole: "engineer" | "admin";
  onDecision: (decision: CapabilityDecision) => void;
}

const riskLabels: Record<CapabilityRisk, string> = {
  low: "Low risk",
  high: "High risk",
  mutating: "Changes workspace or application data",
};

export function CapabilityDialog({
  request,
  actorRole,
  onDecision,
}: CapabilityDialogProps) {
  const titleId = useId();
  const descriptionId = useId();
  const allowRef = useRef<HTMLButtonElement>(null);
  const denyRef = useRef<HTMLButtonElement>(null);
  const administratorBlocked =
    request.administratorOnly && actorRole !== "admin";

  useEffect(() => {
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onDecision("cancel");
      }
    };
    document.addEventListener("keydown", escape);
    (administratorBlocked ? denyRef : allowRef).current?.focus();
    return () => document.removeEventListener("keydown", escape);
  }, [administratorBlocked, onDecision]);

  return (
    <div className="surface-capability-backdrop">
      <section
        className="surface-capability-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        data-testid="surface-capability-dialog"
      >
        <header>
          <p className="surface-capability-eyebrow">Permission requested</p>
          <h2 id={titleId}>Permission requested: {request.sourceTitle}</h2>
          <p id={descriptionId}>
            <strong>
              {request.sourceId} · version {request.sourceVersion}
            </strong>{" "}
            is asking to use a protected Wright capability in{" "}
            <strong>{request.workspaceName}</strong>.
          </p>
        </header>

        <dl className="surface-capability-details">
          <div>
            <dt>Operation</dt>
            <dd>{request.operation}</dd>
          </div>
          <div>
            <dt>Data shared</dt>
            <dd>{request.dataDescription}</dd>
          </div>
          <div>
            <dt>Risk</dt>
            <dd className={`risk-${request.risk}`}>
              {riskLabels[request.risk]}
            </dd>
          </div>
          <div>
            <dt>Why it is needed</dt>
            <dd>{request.reason}</dd>
          </div>
          <div>
            <dt>Effective policy</dt>
            <dd>{request.effectivePolicy}</dd>
          </div>
          <div>
            <dt>Duration</dt>
            <dd>{request.duration}</dd>
          </div>
          <div>
            <dt>Expires</dt>
            <dd>
              <time dateTime={request.expiresAt}>{request.expiresAt}</time>
            </dd>
          </div>
          <div>
            <dt>Persistence</dt>
            <dd>{request.persistence}</dd>
          </div>
        </dl>

        <p className="surface-capability-consequence">
          <strong>If you deny:</strong> {request.denialConsequence}
        </p>
        {administratorBlocked && (
          <p role="status" className="surface-capability-admin">
            Administrator approval is required. You can deny or cancel this
            request, but an engineer cannot broaden the effective policy.
          </p>
        )}

        <footer className="surface-capability-actions">
          <button
            ref={allowRef}
            type="button"
            data-testid="surface-capability-allow"
            disabled={administratorBlocked}
            onClick={() => onDecision("allow")}
          >
            Allow
          </button>
          <button
            ref={denyRef}
            type="button"
            data-testid="surface-capability-deny"
            onClick={() => onDecision("deny")}
          >
            Deny
          </button>
          <button
            type="button"
            data-testid="surface-capability-cancel"
            onClick={() => onDecision("cancel")}
          >
            Cancel
          </button>
        </footer>
      </section>
    </div>
  );
}

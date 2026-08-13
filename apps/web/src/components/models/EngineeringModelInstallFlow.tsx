import { useState } from "react";
import {
  EngineeringModelServiceError,
  engineeringModelService,
  type EngineeringModelOperation,
  type EngineeringModelPlan,
} from "../../services/engineering-model-service";

function bytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MiB`;
}

function failureMessage(error: unknown): { message: string; recovery: string } {
  if (error instanceof EngineeringModelServiceError) {
    return { message: error.message, recovery: error.recovery };
  }
  if (error instanceof Error) {
    const recovery = Reflect.get(error, "recovery");
    return {
      message: error.message,
      recovery:
        typeof recovery === "string"
          ? recovery
          : "Create and review a fresh plan before retrying.",
    };
  }
  return {
    message: "The engineering model operation failed.",
    recovery: "Create and review a fresh plan before retrying.",
  };
}

export function EngineeringModelInstallFlow({
  modelId,
  variantId,
}: {
  modelId: string;
  variantId: string;
}) {
  const [plan, setPlan] = useState<EngineeringModelPlan | null>(null);
  const [operation, setOperation] = useState<EngineeringModelOperation | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<{
    message: string;
    recovery: string;
  } | null>(null);

  const review = async () => {
    setBusy(true);
    setFailure(null);
    setOperation(null);
    try {
      setPlan(await engineeringModelService.createPlan(modelId, variantId));
    } catch (error) {
      setFailure(failureMessage(error));
    } finally {
      setBusy(false);
    }
  };

  const confirm = async () => {
    if (!plan) return;
    setBusy(true);
    setFailure(null);
    try {
      setOperation(
        await engineeringModelService.confirmPlan(
          plan.plan_id,
          plan.plan_digest,
        ),
      );
    } catch (error) {
      setFailure(failureMessage(error));
    } finally {
      setBusy(false);
    }
  };

  const cancel = async () => {
    if (!operation) return;
    setBusy(true);
    try {
      setOperation(
        await engineeringModelService.cancelOperation(operation.operation_id),
      );
    } catch (error) {
      setFailure(failureMessage(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section data-testid={`model-install-flow-${modelId}-${variantId}`}>
      <h4>Safe installation</h4>
      {!plan && !operation ? (
        <button
          type="button"
          data-testid="model-install-review"
          disabled={busy}
          onClick={() => void review()}
        >
          {busy ? "Preparing effects…" : "Review install effects"}
        </button>
      ) : null}

      {plan ? (
        <div data-testid="model-install-plan">
          <p>
            Network: {plan.requirements.network} · Access reference:{" "}
            {plan.requirements.credential} · License action:{" "}
            {plan.requirements.license_action}
          </p>
          <p>Expires: {plan.expires_at}</p>
          <ul>
            {plan.effects.map((effect, index) => (
              <li key={`${effect.kind}-${index}`}>
                {effect.description} {bytes(effect.maximum_bytes)} maximum ·{" "}
                {effect.reversible ? "reversible" : "not reversible"}
                {effect.safe_location ? ` · ${effect.safe_location}` : ""}
              </li>
            ))}
          </ul>
          <p>Rollback: {plan.rollback}</p>
          <p>Cleanup: {plan.cleanup}</p>
          {plan.blockers.length ? (
            <div role="alert">
              {plan.blockers.map((blocker) => (
                <div key={blocker.category}>
                  <p>{blocker.message}</p>
                  <p>Recovery: {blocker.recovery}</p>
                </div>
              ))}
            </div>
          ) : null}
          {plan.state === "confirmable" && !operation ? (
            <button
              type="button"
              data-testid="model-install-confirm"
              disabled={busy}
              onClick={() => void confirm()}
            >
              {busy ? "Installing…" : "Confirm and install"}
            </button>
          ) : null}
        </div>
      ) : null}

      {operation ? (
        <div aria-live="polite" data-testid="model-install-operation">
          <p>
            {operation.state} · {operation.phase}
          </p>
          <p>{operation.progress.message}</p>
          <progress
            aria-label="Engineering model installation progress"
            max={Math.max(operation.progress.maximum_bytes, 1)}
            value={operation.progress.completed_bytes}
          />
          <p>Cleanup: {operation.cleanup_state}</p>
          {!["succeeded", "failed", "cancelled"].includes(operation.state) ? (
            <button
              type="button"
              data-testid="model-install-cancel"
              disabled={busy || operation.state === "cancelling"}
              onClick={() => void cancel()}
            >
              Cancel installation
            </button>
          ) : null}
        </div>
      ) : null}

      {failure ? (
        <div role="alert">
          <p>{failure.message}</p>
          <p>Recovery: {failure.recovery}</p>
        </div>
      ) : null}
    </section>
  );
}

export default EngineeringModelInstallFlow;

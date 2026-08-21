import { useCallback, useEffect, useRef, useState } from "react";
import {
  engineeringModelService,
  type EngineeringModelMaintenanceStatus,
  type EngineeringModelOfflineExport,
  type EngineeringModelPlan,
  type EngineeringModelUpdateComparison,
} from "../../services/engineering-model-service";

export interface EngineeringModelMaintenanceProps {
  installationId: string;
  modelId: string;
  variantId: string;
}

function safeText(value: unknown, fallback: string): string {
  return typeof value === "string" && value ? value : fallback;
}

export function EngineeringModelMaintenance({
  installationId,
  modelId,
  variantId,
}: EngineeringModelMaintenanceProps) {
  const [maintenance, setMaintenance] =
    useState<EngineeringModelMaintenanceStatus | null>(null);
  const [comparison, setComparison] =
    useState<EngineeringModelUpdateComparison | null>(null);
  const [offlineExport, setOfflineExport] =
    useState<EngineeringModelOfflineExport | null>(null);
  const [pendingPlan, setPendingPlan] = useState<EngineeringModelPlan | null>(
    null,
  );
  const [rollbackTarget, setRollbackTarget] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const resultHeading = useRef<HTMLHeadingElement>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setMaintenance(
        await engineeringModelService.getInstallationMaintenance(
          installationId,
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Maintenance state could not be loaded.",
      );
    }
  }, [installationId]);

  useEffect(() => {
    void load();
  }, [load]);

  const complete = () => {
    queueMicrotask(() => resultHeading.current?.focus());
  };

  const compare = async () => {
    setBusy(true);
    setError(null);
    try {
      setComparison(
        await engineeringModelService.compareInstallationUpdate(
          installationId,
          modelId,
          variantId,
        ),
      );
      complete();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Comparison failed.");
    } finally {
      setBusy(false);
    }
  };

  const prepare = async (
    action: "disable" | "uninstall" | "purge" | "rollback" | "export",
    target?: string,
  ) => {
    setBusy(true);
    setError(null);
    try {
      setPendingPlan(
        await engineeringModelService.createMaintenancePlan(
          installationId,
          action,
          target,
        ),
      );
      complete();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Maintenance failed.");
    } finally {
      setBusy(false);
    }
  };

  const confirm = async () => {
    if (!pendingPlan || pendingPlan.state !== "confirmable") return;
    setBusy(true);
    setError(null);
    try {
      const operation = await engineeringModelService.confirmPlan(
        pendingPlan.plan_id,
        pendingPlan.plan_digest,
      );
      if (operation.state !== "succeeded") {
        throw new Error(
          operation.failure?.message ??
            `The ${pendingPlan.operation_kind} operation did not complete.`,
        );
      }
      if (pendingPlan.operation_kind === "export") {
        setOfflineExport(
          operation.result as unknown as EngineeringModelOfflineExport,
        );
      }
      setPendingPlan(null);
      await load();
      complete();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Maintenance failed.");
    } finally {
      setBusy(false);
    }
  };

  const archiveReference = async (referenceId: string) => {
    setBusy(true);
    setError(null);
    try {
      await engineeringModelService.setModelReferenceState(
        referenceId,
        "archived",
      );
      setMaintenance((current) =>
        current
          ? {
              ...current,
              blockers: current.blockers.filter(
                (item) => item.reference_id !== referenceId,
              ),
              references: current.references.map((item) =>
                item.reference_id === referenceId
                  ? { ...item, state: "archived" }
                  : item,
              ),
            }
          : current,
      );
      complete();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Reference update failed.",
      );
    } finally {
      setBusy(false);
    }
  };

  const blockers = maintenance?.blockers ?? [];

  return (
    <section aria-label="Model update, rollback, removal, and export">
      <h4 ref={resultHeading} tabIndex={-1}>
        Maintain this exact installation
      </h4>
      <p>
        Current state: {maintenance?.state ?? "loading"}. Reclaimable bytes:{" "}
        {maintenance?.reclaimable_bytes ?? 0}.
      </p>
      {error ? <p role="alert">{error}</p> : null}

      <button type="button" disabled={busy} onClick={() => void compare()}>
        Compare available revision
      </button>
      {comparison ? (
        <div role="status" aria-live="polite">
          <p>
            Changed facets: {comparison.changed_facets.join(", ") || "none"}
          </p>
          {comparison.requires_retest ? (
            <p>Standard retest required before activation.</p>
          ) : (
            <p>No behavioral retest change detected.</p>
          )}
          {comparison.requires_license_review ? (
            <p>License review required before update.</p>
          ) : null}
        </div>
      ) : null}

      <label>
        Rollback installation identity
        <input
          value={rollbackTarget}
          maxLength={128}
          onChange={(event) => setRollbackTarget(event.target.value.trim())}
        />
      </label>
      <button
        type="button"
        disabled={busy || !rollbackTarget}
        onClick={() => void prepare("rollback", rollbackTarget)}
      >
        Prepare rollback
      </button>

      <div>
        <button
          type="button"
          disabled={busy || maintenance?.state === "disabled"}
          onClick={() => void prepare("disable")}
        >
          Disable installation
        </button>
        <button
          type="button"
          disabled={busy || maintenance?.state !== "disabled"}
          onClick={() => void prepare("uninstall")}
        >
          Uninstall but retain verified bytes
        </button>
        <button
          type="button"
          disabled={
            busy || maintenance?.state !== "uninstalled" || blockers.length > 0
          }
          onClick={() => void prepare("purge")}
        >
          Purge verified bytes
        </button>
      </div>

      {blockers.length ? (
        <div role="status">
          <p>
            Purge is blocked by reproducibility references or active leases:
          </p>
          <ul>
            {blockers.map((item, index) => {
              const referenceId = safeText(item.reference_id, "");
              const owner = safeText(item.owner_id, `hold-${index + 1}`);
              return (
                <li key={referenceId || `${owner}-${index}`}>
                  {safeText(item.kind, "hold")}: {owner}{" "}
                  {referenceId ? (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void archiveReference(referenceId)}
                      aria-label={`Archive ${owner}`}
                    >
                      Archive reference
                    </button>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      <button
        type="button"
        disabled={busy}
        onClick={() => void prepare("export")}
      >
        Create offline export
      </button>
      {pendingPlan ? (
        <section aria-label="Review exact maintenance effects">
          <h5>Review {pendingPlan.operation_kind} before confirmation</h5>
          <ul>
            {pendingPlan.effects.map((effect, index) => (
              <li key={`${effect.kind}-${index}`}>
                {effect.description} Maximum bytes: {effect.maximum_bytes}.{" "}
                {effect.reversible ? "Reversible." : "Not reversible."}
              </li>
            ))}
          </ul>
          {pendingPlan.blockers.length ? (
            <div role="alert">
              <p>This plan cannot be confirmed:</p>
              <ul>
                {pendingPlan.blockers.map((blocker) => (
                  <li key={`${blocker.category}-${blocker.message}`}>
                    {blocker.message} {blocker.recovery}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <p>Rollback: {pendingPlan.rollback}</p>
          <p>Cleanup: {pendingPlan.cleanup}</p>
          <button
            type="button"
            disabled={busy || pendingPlan.state !== "confirmable"}
            onClick={() => void confirm()}
          >
            Confirm {pendingPlan.operation_kind}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => setPendingPlan(null)}
          >
            Cancel review
          </button>
        </section>
      ) : null}
      {offlineExport ? (
        <p role="status">
          Export {offlineExport.artifact_id} is ready ({offlineExport.size}{" "}
          bytes, SHA-256 {offlineExport.sha256}).
        </p>
      ) : null}
    </section>
  );
}

export default EngineeringModelMaintenance;

import { useCallback, useEffect, useRef, useState } from "react";
import {
  engineeringModelService,
  type EngineeringModelMaintenanceStatus,
  type EngineeringModelOfflineExport,
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

  const maintain = async (
    action: "disable" | "uninstall" | "purge" | "rollback",
    target?: string,
  ) => {
    setBusy(true);
    setError(null);
    try {
      const result = await engineeringModelService.maintainInstallation(
        installationId,
        action,
        target,
      );
      setMaintenance((current) => ({
        ...(current ?? { blockers: [], references: [] }),
        ...result,
      }));
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

  const createExport = async () => {
    setBusy(true);
    setError(null);
    try {
      setOfflineExport(
        await engineeringModelService.createOfflineExport(installationId),
      );
      complete();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Export failed.");
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
        onClick={() => void maintain("rollback", rollbackTarget)}
      >
        Prepare rollback
      </button>

      <div>
        <button
          type="button"
          disabled={busy || maintenance?.state === "disabled"}
          onClick={() => void maintain("disable")}
        >
          Disable installation
        </button>
        <button
          type="button"
          disabled={busy || maintenance?.state !== "disabled"}
          onClick={() => void maintain("uninstall")}
        >
          Uninstall but retain verified bytes
        </button>
        <button
          type="button"
          disabled={
            busy || maintenance?.state !== "uninstalled" || blockers.length > 0
          }
          onClick={() => void maintain("purge")}
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

      <button type="button" disabled={busy} onClick={() => void createExport()}>
        Create offline export
      </button>
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

import { useEffect, useState } from "react";
import {
  EngineeringModelServiceError,
  engineeringModelService,
  type EngineeringModelRuntimeTest,
  type EngineeringModelWorkspaceBinding,
} from "../../services/engineering-model-service";

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
          : "Inspect the exact installation and runtime, then retry.",
    };
  }
  return {
    message: "The engineering model runtime request failed.",
    recovery: "Inspect the exact installation and runtime, then retry.",
  };
}

export function EngineeringModelRuntimePanel({
  installationId,
  taskId,
  workspaceId,
}: {
  installationId: string;
  taskId: string;
  workspaceId: string;
}) {
  const [runtime, setRuntime] = useState<EngineeringModelRuntimeTest | null>(
    null,
  );
  const [binding, setBinding] =
    useState<EngineeringModelWorkspaceBinding | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<{
    message: string;
    recovery: string;
  } | null>(null);

  useEffect(() => {
    let active = true;
    setFailure(null);
    void engineeringModelService
      .getStandardTestEvidence(installationId)
      .then((value) => active && setRuntime(value))
      .catch((error) => active && setFailure(failureMessage(error)));
    return () => {
      active = false;
    };
  }, [installationId]);

  const runTest = async () => {
    setBusy(true);
    setFailure(null);
    try {
      setRuntime(await engineeringModelService.runStandardTest(installationId));
    } catch (error) {
      setFailure(failureMessage(error));
    } finally {
      setBusy(false);
    }
  };

  const enable = async () => {
    setBusy(true);
    setFailure(null);
    try {
      setBinding(
        await engineeringModelService.createWorkspaceBinding(
          workspaceId,
          installationId,
          taskId,
        ),
      );
    } catch (error) {
      setFailure(failureMessage(error));
    } finally {
      setBusy(false);
    }
  };

  const disable = async () => {
    if (!binding) return;
    setBusy(true);
    setFailure(null);
    try {
      setBinding(
        await engineeringModelService.setWorkspaceBindingState(
          workspaceId,
          binding.binding_id,
          "disabled",
        ),
      );
    } catch (error) {
      setFailure(failureMessage(error));
    } finally {
      setBusy(false);
    }
  };

  const ready = runtime?.installation_state === "ready";
  return (
    <section data-testid={`model-runtime-${installationId}`}>
      <h4>Standard test and workspace capability</h4>
      <p aria-live="polite">
        {ready
          ? `Ready for workspace use · ${runtime.adapter_id} ${runtime.adapter_version}`
          : "Standard test required before workspace enablement."}
      </p>
      {!ready ? (
        <button type="button" disabled={busy} onClick={() => void runTest()}>
          {busy ? "Testing…" : "Run mandatory standard test"}
        </button>
      ) : null}

      {runtime?.evidence.map((item) => (
        <article key={item.evidence_id}>
          <p>
            Evidence {item.evidence_id} · {item.state}
          </p>
          <p>Material digest: {item.material_digest}</p>
          <p>Observation digest: {item.observation_digest}</p>
        </article>
      ))}

      {ready && (!binding || binding.state === "disabled") ? (
        <button type="button" disabled={busy} onClick={() => void enable()}>
          Enable for workspace
        </button>
      ) : null}
      {binding ? (
        <div aria-live="polite">
          <p>
            {binding.tool_name} · {binding.state}
          </p>
          <p>Binding digest: {binding.binding_digest}</p>
          {binding.state === "enabled" ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void disable()}
            >
              Disable workspace capability
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

export default EngineeringModelRuntimePanel;

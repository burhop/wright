import { useEffect, useRef, useState } from "react";
import {
  nativeRunApi,
  type NativeBinding,
  type NativeBindingOption,
  type NativeDefinition,
  type NativeEvent,
  type NativeRunSummary,
  type SavedProcess,
} from "../../services/native-process";
import { canonicalJson, newId } from "./model";
import { activeRun, nativeErrorText, useNativeRun } from "./useNativeRun";
import { NativeArtifactCard } from "./NativeArtifactCard";
interface Props {
  sessionId: string;
  saved: SavedProcess | null;
  definition: NativeDefinition;
  dirty: boolean;
  authoringBusy: boolean;
  bindings: Record<string, NativeBinding>;
  setBindings: (bindings: Record<string, NativeBinding>) => void;
  inspectStep: (id: string) => void;
}
export function NativeRunPanel({
  sessionId,
  saved,
  definition,
  dirty,
  authoringBusy,
  bindings,
  setBindings,
  inspectStep,
}: Props) {
  const [history, setHistory] = useState<NativeRunSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [historyError, setHistoryError] = useState("");
  const [actionError, setActionError] = useState("");
  const [actionStatus, setActionStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [timeout, setTimeoutValue] = useState("60");
  const [options, setOptions] = useState<NativeBindingOption[]>([]);
  const [bindingError, setBindingError] = useState("");
  const [bindingRefresh, setBindingRefresh] = useState(0);
  const [eventCache, setEventCache] = useState<{
    runId: string;
    events: NativeEvent[];
    next: number;
  } | null>(null);
  const request = useRef<{ fingerprint: string; id: string } | null>(null);
  const {
    run,
    receivedAt,
    error: inspectionError,
  } = useNativeRun(sessionId, selectedId, refresh);
  const mcpSteps = definition.steps.filter(
    (step) => step.operation === "mcp.call@1",
  );
  const mcpKey = mcpSteps.map((step) => step.id).join(",");
  const selectedBindings = Object.fromEntries(
    mcpSteps.flatMap((step) =>
      bindings[step.id] ? [[step.id, bindings[step.id]]] : [],
    ),
  );
  const bindingIsCurrent = (binding: NativeBinding | undefined) =>
    binding &&
    options.some(
      (option) =>
        option.server_id === binding.server_id &&
        option.tool_name === binding.tool_name &&
        option.input_schema_digest === binding.input_schema_digest &&
        option.output_schema_digest === binding.output_schema_digest,
    );
  const bindingsReady = mcpSteps.every((step) =>
    bindingIsCurrent(bindings[step.id]),
  );
  const seconds = Number(timeout),
    timeoutValid = Number.isInteger(seconds) && seconds >= 1 && seconds <= 300;
  const canRun =
    Boolean(saved) &&
    !dirty &&
    !authoringBusy &&
    !busy &&
    timeoutValid &&
    bindingsReady;
  useEffect(() => {
    if (!saved) return;
    const controller = new AbortController();
    void nativeRunApi
      .history(sessionId, saved.definition.id, undefined, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setHistory(result.runs);
        setCursor(result.next_cursor);
        setHistoryError("");
        setSelectedId((previous) => previous ?? result.runs[0]?.run_id ?? null);
      })
      .catch((error) => {
        if (!controller.signal.aborted) setHistoryError(nativeErrorText(error));
      });
    return () => controller.abort();
  }, [sessionId, saved?.definition.id, historyRefresh, saved]);
  useEffect(() => {
    if (!mcpKey) return;
    const controller = new AbortController();
    void nativeRunApi
      .bindings(sessionId, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setOptions(result.bindings);
          setBindingError("");
        }
      })
      .catch((error) => {
        if (!controller.signal.aborted) setBindingError(nativeErrorText(error));
      });
    return () => controller.abort();
  }, [sessionId, mcpKey, bindingRefresh]);
  async function start(derivedFrom: string | null) {
    if (!saved || !canRun) return;
    const fingerprint = canonicalJson({
      token: saved.token,
      bindings: selectedBindings,
      seconds,
      derivedFrom,
      processId: saved.definition.id,
    });
    if (request.current?.fingerprint !== fingerprint)
      request.current = { fingerprint, id: newId("request") };
    setBusy(true);
    setActionError("");
    try {
      const result = await nativeRunApi.start(
        sessionId,
        saved.definition.id,
        saved.token,
        request.current.id,
        selectedBindings,
        seconds,
        derivedFrom,
      );
      setSelectedId(result.run_id);
      setRefresh((value) => value + 1);
      setHistoryRefresh((value) => value + 1);
      setActionStatus(
        `Service accepted run ${result.run_id}; submission response: ${result.state}. Results appear only as they are recorded.`,
      );
      request.current = null;
    } catch (error) {
      setActionError(nativeErrorText(error));
    } finally {
      setBusy(false);
    }
  }
  async function cancel() {
    if (!run || !activeRun(run.state)) return;
    setBusy(true);
    setActionError("");
    try {
      const result = await nativeRunApi.cancel(sessionId, run.run_id);
      setActionStatus(
        `Service reports run ${result.state} after the cancellation request.`,
      );
      setRefresh((value) => value + 1);
      setHistoryRefresh((value) => value + 1);
    } catch (error) {
      setActionError(nativeErrorText(error));
    } finally {
      setBusy(false);
    }
  }
  async function loadEvents() {
    if (!run) return;
    const runId = run.run_id,
      previous = eventCache?.runId === runId ? eventCache : null;
    setBusy(true);
    setActionError("");
    try {
      const result = await nativeRunApi.events(
        sessionId,
        runId,
        previous?.next ?? 0,
      );
      setEventCache({
        runId,
        events: [...(previous?.events ?? []), ...result.events].slice(-1000),
        next: result.next_sequence,
      });
    } catch (error) {
      setActionError(nativeErrorText(error));
    } finally {
      setBusy(false);
    }
  }
  const events = eventCache?.runId === selectedId ? eventCache : null;
  return (
    <section
      className="native-runs"
      id="native-run-inspection"
      tabIndex={-1}
      data-testid="native-run-panel"
      aria-labelledby="native-runs-heading"
    >
      <h2 id="native-runs-heading">Runs and actual outputs</h2>
      <p>
        Runs use immutable saved definitions. Artifact declarations become
        observed outputs only when the runtime records and verifies actual
        bytes.
      </p>
      {!saved ? (
        <p>Save this process to run it or view its retained history.</p>
      ) : dirty ? (
        <p role="status">
          Apply or discard field changes and save the current version before
          running. Previous run evidence remains inspectable below.
        </p>
      ) : (
        <p>
          The next run will use saved revision {saved.revision} ·{" "}
          <code>{saved.semantic_digest}</code>
        </p>
      )}
      <div className="native-actions">
        <label>
          Run time limit (seconds)
          <input
            data-testid="native-run-timeout"
            inputMode="numeric"
            value={timeout}
            onChange={(event) => setTimeoutValue(event.target.value)}
            aria-invalid={!timeoutValid}
          />
        </label>
        <button
          data-testid="native-run-start"
          disabled={!canRun}
          onClick={() => void start(null)}
        >
          Run saved version
        </button>
        {run && !activeRun(run.state) && run.state !== "succeeded" && (
          <button
            data-testid="native-run-derived"
            disabled={!canRun}
            onClick={() => void start(run.run_id)}
          >
            Run corrected saved version linked to this run
          </button>
        )}
        <button
          data-testid="native-run-refresh"
          disabled={!saved || busy}
          onClick={() => {
            setHistoryRefresh((value) => value + 1);
            setRefresh((value) => value + 1);
          }}
        >
          Refresh runs
        </button>
      </div>
      {!timeoutValid && (
        <p role="alert">Choose an integer time limit from 1 to 300 seconds.</p>
      )}
      {mcpSteps.length > 0 && (
        <section className="native-bindings" aria-label="Exact tool bindings">
          <h3>Tool bindings for this run</h3>
          <p>
            Choose an exact permitted tool. The runtime rechecks its identity,
            schemas and workspace policy before invocation.
          </p>
          {bindingError && <p role="alert">{bindingError}</p>}
          <button
            data-testid="native-bindings-refresh"
            onClick={() => setBindingRefresh((value) => value + 1)}
          >
            Refresh permitted tools
          </button>
          {mcpSteps.map((step) => (
            <div key={step.id}>
              <label>
                {step.title}
                <select
                  data-testid={`native-binding-${step.id}`}
                  value={
                    bindings[step.id] ? canonicalJson(bindings[step.id]) : ""
                  }
                  onChange={(event) => {
                    const next = { ...bindings };
                    if (event.target.value)
                      next[step.id] = JSON.parse(
                        event.target.value,
                      ) as NativeBinding;
                    else delete next[step.id];
                    setBindings(next);
                  }}
                >
                  <option value="">Choose exact tool</option>
                  {bindings[step.id] &&
                    !bindingIsCurrent(bindings[step.id]) && (
                      <option value={canonicalJson(bindings[step.id])}>
                        Prior binding is unavailable or changed — choose again
                      </option>
                    )}
                  {options.map((option) => {
                    const exact: NativeBinding = {
                      server_id: option.server_id,
                      tool_name: option.tool_name,
                      input_schema_digest: option.input_schema_digest,
                      output_schema_digest: option.output_schema_digest,
                    };
                    return (
                      <option
                        value={canonicalJson(exact)}
                        key={canonicalJson(exact)}
                      >
                        {option.title || option.tool_name} · {option.server_id}/
                        {option.tool_name}
                      </option>
                    );
                  })}
                </select>
              </label>
              {bindings[step.id] && (
                <details>
                  <summary>Exact selected identity and schema digests</summary>
                  <pre>{JSON.stringify(bindings[step.id], null, 2)}</pre>
                </details>
              )}
            </div>
          ))}
        </section>
      )}
      {actionStatus && <p role="status">{actionStatus}</p>}
      {actionError && (
        <p role="alert" data-testid="native-run-action-error">
          {actionError}
        </p>
      )}
      {historyError && (
        <p role="alert">
          History unavailable: {historyError} Existing evidence below may be
          stale; refresh to reconnect.
        </p>
      )}
      <label>
        Run history
        <select
          data-testid="native-run-history"
          value={selectedId ?? ""}
          onChange={(event) => {
            setSelectedId(event.target.value || null);
            setActionError("");
          }}
        >
          <option value="">Choose run</option>
          {selectedId &&
            !history.some((item) => item.run_id === selectedId) && (
              <option value={selectedId}>{selectedId}</option>
            )}
          {history.map((item) => (
            <option key={item.run_id} value={item.run_id}>
              {item.created_at} · {item.run_id} · {item.state}
            </option>
          ))}
        </select>
      </label>
      {cursor && saved && (
        <button
          data-testid="native-run-history-more"
          disabled={busy}
          onClick={() => {
            setBusy(true);
            void nativeRunApi
              .history(sessionId, saved.definition.id, cursor)
              .then((result) => {
                setHistory((previous) => [
                  ...previous,
                  ...result.runs.filter(
                    (item) =>
                      !previous.some((old) => old.run_id === item.run_id),
                  ),
                ]);
                setCursor(result.next_cursor);
              })
              .catch((error) => setHistoryError(nativeErrorText(error)))
              .finally(() => setBusy(false));
          }}
        >
          Older runs
        </button>
      )}
      {inspectionError && (
        <div
          className="native-warning"
          role="alert"
          data-testid="native-run-disconnected"
        >
          <p>Run updates are unavailable: {inspectionError}</p>
          <p>
            The last received snapshot is retained. Wright retries every five
            seconds; disconnecting this view does not cancel the run.
          </p>
          <button
            data-testid="native-run-reconnect"
            onClick={() => setRefresh((value) => value + 1)}
          >
            Reconnect now
          </button>
        </div>
      )}
      {selectedId && !run && !inspectionError && (
        <p role="status">Loading recorded run…</p>
      )}
      {run && (
        <div data-testid="native-run-inspection">
          <h3>
            Run {run.run_id}:{" "}
            <span data-testid="native-run-state">{run.state}</span>
          </h3>
          <p>
            {inspectionError ? "Last received snapshot" : "Recorded snapshot"}{" "}
            at {receivedAt}. Revision {run.snapshot.revision}; time limit{" "}
            {run.timeout_seconds} seconds.
          </p>
          <p>
            Semantic digest: <code>{run.semantic_digest}</code> · Trace:{" "}
            <code>{run.trace_id}</code>
          </p>
          {saved?.semantic_digest !== run.semantic_digest && (
            <p>
              This run used a different saved definition from the current editor
              version.
            </p>
          )}
          {run.derived_from_run_id && (
            <p>
              Recovery link: <code>{run.derived_from_run_id}</code>
            </p>
          )}
          {run.reason && (
            <div className="native-warning" data-testid="native-run-reason">
              <strong>{run.reason.code}</strong>: {run.reason.message}
              <p>{run.reason.recovery}</p>
            </div>
          )}
          {activeRun(run.state) && (
            <button
              data-testid="native-run-cancel"
              disabled={busy}
              onClick={() => void cancel()}
            >
              Cancel this run
            </button>
          )}
          <ol className="native-run-steps">
            {run.steps.map((step) => {
              const recorded = run.snapshot.definition.steps.find(
                (item) => item.id === step.step_id,
              );
              return (
                <li
                  key={step.step_id}
                  data-testid={`native-run-step-${step.step_id}`}
                >
                  <h3>
                    {recorded?.title ?? step.step_id} · {step.state}
                  </h3>
                  <p>
                    <code>{step.operation}</code> · <code>{step.step_id}</code>
                  </p>
                  {step.reason && (
                    <p>
                      <strong>{step.reason.code}</strong>: {step.reason.message}{" "}
                      {step.reason.recovery}
                    </p>
                  )}
                  <button
                    data-testid={`native-correct-${step.step_id}`}
                    disabled={
                      !definition.steps.some((item) => item.id === step.step_id)
                    }
                    onClick={() => inspectStep(step.step_id)}
                  >
                    Inspect current step to correct inputs
                  </button>
                  <details>
                    <summary>Actual inputs and outputs by exact port</summary>
                    <p>
                      Started {step.started_at ?? "not started"}; completed{" "}
                      {step.completed_at ?? "not completed"}.
                    </p>
                    <h4>Inputs</h4>
                    {step.inputs === null ? (
                      <p>No input record.</p>
                    ) : (
                      <pre>{JSON.stringify(step.inputs, null, 2)}</pre>
                    )}
                    <h4>Outputs</h4>
                    {step.outputs === null ? (
                      <p>No output record.</p>
                    ) : (
                      <pre>{JSON.stringify(step.outputs, null, 2)}</pre>
                    )}
                  </details>
                </li>
              );
            })}
          </ol>
          <h3>Recorded artifacts ({run.artifacts.length})</h3>
          {run.artifacts.length === 0 && (
            <p>
              No artifacts are recorded for this run. Declared process outputs
              are not proof of generated files.
            </p>
          )}
          {run.artifacts.map((artifact) => (
            <NativeArtifactCard
              key={`${run.run_id}/${artifact.artifact_id}`}
              sessionId={sessionId}
              runId={run.run_id}
              artifact={artifact}
              runState={run.state}
            />
          ))}
          <details>
            <summary>Immutable definition and bindings actually used</summary>
            <p>Actor: {run.actor}</p>
            <pre>{JSON.stringify(run.snapshot, null, 2)}</pre>
            <pre>{JSON.stringify(run.bindings, null, 2)}</pre>
          </details>
          <details>
            <summary>Recorded events and traces</summary>
            <p>
              Snapshot includes sequence {run.last_sequence}. This view retains
              at most the latest 1000 loaded events; each request loads at most
              200.
            </p>
            <button
              data-testid="native-run-events"
              disabled={
                busy || Boolean(events && events.next >= run.last_sequence)
              }
              onClick={() => void loadEvents()}
            >
              {events ? "Load next recorded events" : "Load recorded events"}
            </button>
            {events && (
              <ol>
                {events.events.map((event) => (
                  <li key={event.sequence}>
                    <strong>
                      {event.sequence}: {event.kind}
                    </strong>{" "}
                    · {event.occurred_at} · trace <code>{event.trace_id}</code>
                    <pre>{JSON.stringify(event.payload, null, 2)}</pre>
                  </li>
                ))}
              </ol>
            )}
          </details>
        </div>
      )}
    </section>
  );
}

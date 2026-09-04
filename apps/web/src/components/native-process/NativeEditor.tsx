import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  nativeProcessApi,
  NativeProcessError,
  type NativeCheck,
  type NativeContract,
  type NativeDocument,
  type NativeExample,
  type ProcessSummary,
  type SavedProcess,
} from "../../services/native-process";
import {
  canonicalJson,
  emptyDocument,
  newId,
  pushCommand,
  redo,
  undo,
  validateDocument,
  type NativeCommand,
  type NativeHistory,
} from "./model";
import { NativeCanvas } from "./NativeCanvas";
import { NativeInspector, type StepBuffer } from "./NativeInspector";
import { NativeConfirmDialog } from "./NativeConfirmDialog";

interface DraftCheckpoint {
  version: 1;
  document: NativeDocument;
  saved: SavedProcess | null;
  baseline: string;
  buffers: Record<string, StepBuffer>;
  title: string;
}
function readDraft(key: string): DraftCheckpoint | null {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw || raw.length > 1500000) return null;
    const value = JSON.parse(raw) as DraftCheckpoint;
    return value.version === 1 ? value : null;
  } catch {
    return null;
  }
}
function errorText(error: unknown): string {
  return error instanceof NativeProcessError
    ? `${error.detail.message} ${error.detail.recovery}${error.detail.trace_id ? ` (Trace: ${error.detail.trace_id})` : ""}`
    : error instanceof Error
      ? error.message
      : "The request failed. Your draft is retained.";
}
export function NativeEditor({
  sessionId,
  onDirtyChange,
}: {
  sessionId: string;
  onDirtyChange?: (dirty: boolean) => void;
}) {
  const draftKey = `wright-native-draft-v1:${sessionId}`;
  const [contract, setContract] = useState<NativeContract | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [history, setHistory] = useState<NativeHistory>(() => ({
    present: emptyDocument(),
    past: [],
    future: [],
  }));
  const [saved, setSaved] = useState<SavedProcess | null>(null);
  const [baseline, setBaseline] = useState(() =>
    canonicalJson(history.present),
  );
  const [buffers, setBuffers] = useState<Record<string, StepBuffer>>({});
  const [title, setTitle] = useState(history.present.definition.title);
  const [recovery, setRecovery] = useState(() => readDraft(draftKey));
  const [selected, setSelected] = useState<string | null>(null);
  const [sourcePort, setSourcePort] = useState("");
  const [targetPort, setTargetPort] = useState("");
  const [operation, setOperation] = useState("");
  const [examples, setExamples] = useState<NativeExample[]>([]);
  const [documents, setDocuments] = useState<ProcessSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [openId, setOpenId] = useState("");
  const [exampleId, setExampleId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Loading the process language…");
  const [check, setCheck] = useState<{
    result: NativeCheck;
    semantic: string;
  } | null>(null);
  const [conflict, setConflict] = useState(false);
  const [pendingAction, setPendingAction] = useState<{
    label: string;
    action: () => void;
  } | null>(null);
  const [storageError, setStorageError] = useState("");
  const saveAttempt = useRef<{ fingerprint: string; id: string } | null>(null);
  const titleRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const document = history.present;
  const dirty =
    canonicalJson(document) !== baseline ||
    Object.keys(buffers).length > 0 ||
    title !== document.definition.title;
  const semantic = canonicalJson(document.definition);
  const currentCheck = check?.semantic === semantic ? check.result : null;
  const hasBuffers =
    Object.keys(buffers).length > 0 || title !== document.definition.title;
  useEffect(() => {
    onDirtyChange?.(dirty);
    return () => onDirtyChange?.(false);
  }, [dirty, onDirtyChange]);

  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([
      nativeProcessApi.contract(sessionId, controller.signal),
      nativeProcessApi.examples(sessionId, controller.signal),
      nativeProcessApi.list(sessionId, undefined, controller.signal),
    ])
      .then(([language, exampleResponse, list]) => {
        if (controller.signal.aborted) return;
        if (
          language.format !== "wright-native-process" ||
          language.schema_version !== "1.0.0" ||
          !Array.isArray(language.operations)
        )
          throw new Error(
            "This build cannot edit the service's process language.",
          );
        setContract(language);
        setOperation(language.operations[0]?.id ?? "");
        setExamples(exampleResponse.examples);
        setDocuments(list.documents);
        setCursor(list.next_cursor);
        setStatus("Ready to author. Add a step or open a development example.");
        setError("");
      })
      .catch((failure) => {
        if (!controller.signal.aborted) {
          setError(errorText(failure));
          setStatus(
            "Native authoring is unavailable until the service reconnects.",
          );
        }
      });
    return () => controller.abort();
  }, [sessionId, loadAttempt]);

  useEffect(() => {
    if (!contract || recovery) return;
    try {
      if (dirty)
        sessionStorage.setItem(
          draftKey,
          JSON.stringify({
            version: 1,
            document,
            saved,
            baseline,
            buffers,
            title,
          } satisfies DraftCheckpoint),
        );
      else sessionStorage.removeItem(draftKey);
      setStorageError("");
    } catch {
      setStorageError(
        "This browser cannot retain a recovery draft. Save or copy the process source before leaving.",
      );
    }
  }, [
    contract,
    recovery,
    dirty,
    document,
    saved,
    baseline,
    buffers,
    title,
    draftKey,
  ]);

  useEffect(() => {
    if (!dirty) return;
    function beforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault();
      event.returnValue = "";
    }
    function click(event: MouseEvent) {
      const link =
        event.target instanceof Element ? event.target.closest("a") : null;
      if (
        !link ||
        event.defaultPrevented ||
        event.button !== 0 ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey ||
        link.target === "_blank" ||
        link.hasAttribute("download")
      )
        return;
      const url = new URL(link.href, window.location.href);
      if (url.href === window.location.href) return;
      event.preventDefault();
      event.stopPropagation();
      setPendingAction({
        label: "Leave this process",
        action: () => {
          if (url.origin === window.location.origin)
            navigate(url.pathname + url.search + url.hash);
          else window.location.assign(url.href);
        },
      });
    }
    window.addEventListener("beforeunload", beforeUnload);
    window.document.addEventListener("click", click, true);
    return () => {
      window.removeEventListener("beforeunload", beforeUnload);
      window.document.removeEventListener("click", click, true);
    };
  }, [dirty, navigate]);

  const command = useCallback(
    (next: NativeCommand): boolean => {
      if (!contract || busy) return false;
      try {
        const updated = pushCommand(history, next, contract);
        setHistory(updated);
        setError("");
        setStatus(
          next.type === "position"
            ? "Layout updated; process meaning is unchanged."
            : "Process definition updated. Save to retain this version.",
        );
        return true;
      } catch (failure) {
        setError(errorText(failure));
        return false;
      }
    },
    [contract, history, busy],
  );
  function updateBuffer(id: string, buffer: StepBuffer | null) {
    setBuffers((previous) => {
      const next = { ...previous };
      if (buffer) next[id] = buffer;
      else delete next[id];
      return next;
    });
  }
  function reset(next: NativeDocument, envelope: SavedProcess | null = null) {
    if (!contract) return;
    const editable = {
      definition: next.definition,
      presentation: next.presentation,
    };
    validateDocument(editable, contract);
    setHistory({ present: editable, past: [], future: [] });
    setSaved(envelope);
    setBaseline(envelope ? canonicalJson(editable) : "");
    setBuffers({});
    setTitle(next.definition.title);
    setSelected(null);
    setSourcePort("");
    setTargetPort("");
    setCheck(null);
    setConflict(false);
    setError("");
    saveAttempt.current = null;
  }
  function guard(label: string, action: () => void) {
    if (dirty) setPendingAction({ label, action });
    else action();
  }
  function newProcess() {
    guard("Start a new process", () => {
      reset(emptyDocument());
      setStatus("New process. Add a step to begin.");
      titleRef.current?.focus();
    });
  }
  function openExample() {
    const example = examples.find((item) => item.id === exampleId);
    if (!example) return;
    guard("Open a development example", () => {
      try {
        const next = structuredClone({
          definition: example.definition,
          presentation: example.presentation,
        });
        next.definition.id = newId("process");
        reset(next);
        setStatus(
          "Development example copied to a new identity. It has not run.",
        );
      } catch (failure) {
        setError(errorText(failure));
      }
    });
  }
  async function loadDocument(id: string) {
    setBusy(true);
    setError("");
    try {
      const envelope = await nativeProcessApi.get(sessionId, id);
      reset(envelope, envelope);
      setStatus(`Opened saved revision ${envelope.revision}.`);
    } catch (failure) {
      setError(errorText(failure));
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    if (!contract || hasBuffers) {
      setError("Apply or discard field changes before saving.");
      return;
    }
    const snapshot = document;
    const fingerprint = canonicalJson({
      document: snapshot,
      token: saved?.token ?? null,
    });
    if (saveAttempt.current?.fingerprint !== fingerprint)
      saveAttempt.current = { fingerprint, id: newId("request") };
    setBusy(true);
    setError("");
    try {
      validateDocument(snapshot, contract);
      const envelope = saved
        ? await nativeProcessApi.save(
            sessionId,
            snapshot,
            saved.token,
            saveAttempt.current.id,
          )
        : await nativeProcessApi.create(
            sessionId,
            snapshot,
            saveAttempt.current.id,
          );
      setSaved(envelope);
      setBaseline(
        canonicalJson({
          definition: envelope.definition,
          presentation: envelope.presentation,
        }),
      );
      setConflict(false);
      setDocuments((previous) => [
        {
          id: envelope.definition.id,
          title: envelope.definition.title,
          revision: envelope.revision,
          token: envelope.token,
          updated_at: envelope.updated_at,
        },
        ...previous.filter((item) => item.id !== envelope.definition.id),
      ]);
      setOpenId(envelope.definition.id);
      setStatus(
        `Saved revision ${envelope.revision}. The process has not been executed by saving.`,
      );
      // An idempotent replay may return an earlier save; never present it as the current remote head.
      const latest = await nativeProcessApi.get(
        sessionId,
        envelope.definition.id,
      );
      if (latest.token !== envelope.token) {
        setConflict(true);
        setError(
          "The service holds a newer version than this save. Your draft is retained. Compare the current saved version or save a copy.",
        );
      }
      saveAttempt.current = null;
    } catch (failure) {
      setError(errorText(failure));
      if (
        failure instanceof NativeProcessError &&
        ["NATIVE_CONFLICT", "NATIVE_REQUEST_REUSED"].includes(
          failure.detail.code,
        )
      )
        setConflict(true);
    } finally {
      setBusy(false);
    }
  }
  async function validate() {
    if (hasBuffers) {
      setError(
        "Apply or discard field changes before checking the definition.",
      );
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await nativeProcessApi.check(
        sessionId,
        document.definition,
      );
      setCheck({ result, semantic });
      setStatus(
        result.ready
          ? "The service reports this definition ready. No execution has occurred."
          : "The service found items to resolve before execution.",
      );
    } catch (failure) {
      setError(errorText(failure));
    } finally {
      setBusy(false);
    }
  }
  const connect = useCallback(
    (source: string, target: string) => {
      if (
        command({ type: "connect", id: newId("connection"), source, target })
      ) {
        setSourcePort("");
        setTargetPort("");
      }
    },
    [command],
  );
  const choosePort = useCallback(
    (id: string) => {
      const port = document.definition.ports.find((item) => item.id === id);
      if (!port) return;
      if (port.direction === "output") {
        setSourcePort(id);
        setStatus("Output selected. Choose the exact input port to connect.");
      } else if (sourcePort) connect(sourcePort, id);
      else {
        setTargetPort(id);
        setStatus(
          "Input selected. Choose an output in the connection controls.",
        );
      }
    },
    [document.definition.ports, sourcePort, connect],
  );
  const portLabel = (id: string) => {
    const port = document.definition.ports.find((item) => item.id === id)!;
    return `${document.definition.steps.find((step) => step.id === port.step_id)?.title}: ${port.label} (${port.type}) · ${port.id}`;
  };
  const selectStep = useCallback((id: string) => setSelected(id), []);
  const move = useCallback(
    (id: string, x: number, y: number) => {
      command({ type: "position", id, x, y });
    },
    [command],
  );

  return (
    <div className="native-editor" data-testid="native-editor" aria-busy={busy}>
      <p className="native-status" role="status" data-testid="native-status">
        {status}
      </p>
      {error && (
        <div className="native-warning" role="alert" data-testid="native-error">
          {error}
        </div>
      )}
      {storageError && <p role="alert">{storageError}</p>}
      {!contract ? (
        <button
          data-testid="native-reconnect"
          onClick={() => setLoadAttempt((value) => value + 1)}
        >
          Reconnect to native service
        </button>
      ) : (
        <>
          {recovery && (
            <section
              className="native-warning"
              aria-label="Recover local draft"
            >
              <h2>Recover this tab’s unsaved work</h2>
              <p>
                A process draft, including unapplied fields, was retained for
                this workspace. Its save token will still be checked by the
                service.
              </p>
              <button
                data-testid="native-recover"
                onClick={() => {
                  try {
                    validateDocument(recovery.document, contract);
                    reset(recovery.document, recovery.saved);
                    setBaseline(recovery.baseline);
                    setBuffers(recovery.buffers);
                    setTitle(recovery.title);
                    setRecovery(null);
                    setStatus(
                      "Local draft recovered. Check the saved version before resolving any conflict.",
                    );
                  } catch (failure) {
                    setError(errorText(failure));
                  }
                }}
              >
                Recover draft
              </button>
              <button
                data-testid="native-discard-recovery"
                onClick={() => {
                  setRecovery(null);
                  sessionStorage.removeItem(draftKey);
                }}
              >
                Discard recovery draft
              </button>
            </section>
          )}
          <fieldset
            className="native-work"
            disabled={busy || Boolean(recovery)}
          >
            <legend className="sr-only">Author process</legend>
            <div className="native-actions native-library">
              <button data-testid="native-new" onClick={newProcess}>
                New process
              </button>
              <label>
                Saved processes
                <select
                  data-testid="native-saved-list"
                  value={openId}
                  onChange={(e) => setOpenId(e.target.value)}
                >
                  <option value="">Choose saved process</option>
                  {documents.map((item) => (
                    <option value={item.id} key={item.id}>
                      {item.title} · revision {item.revision}
                    </option>
                  ))}
                </select>
              </label>
              <button
                data-testid="native-open"
                disabled={!openId}
                onClick={() =>
                  guard("Open a saved process", () => void loadDocument(openId))
                }
              >
                Open
              </button>
              {cursor && (
                <button
                  data-testid="native-more"
                  onClick={() => {
                    setBusy(true);
                    void nativeProcessApi
                      .list(sessionId, cursor)
                      .then((result) => {
                        setDocuments((previous) => [
                          ...previous,
                          ...result.documents.filter(
                            (item) =>
                              !previous.some((old) => old.id === item.id),
                          ),
                        ]);
                        setCursor(result.next_cursor);
                      })
                      .catch((failure) => setError(errorText(failure)))
                      .finally(() => setBusy(false));
                  }}
                >
                  More saved processes
                </button>
              )}
              <label>
                Development examples
                <select
                  data-testid="native-example-list"
                  value={exampleId}
                  onChange={(e) => setExampleId(e.target.value)}
                >
                  <option value="">Choose example</option>
                  {examples.map((example) => (
                    <option value={example.id} key={example.id}>
                      {example.title}
                    </option>
                  ))}
                </select>
              </label>
              <button
                data-testid="native-open-example"
                disabled={!exampleId}
                onClick={openExample}
              >
                Use example
              </button>
            </div>
            <div className="native-actions">
              <label className="native-title-label">
                Process title
                <input
                  ref={titleRef}
                  data-testid="native-process-title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      command({ type: "title", title });
                    }
                  }}
                />
              </label>
              <button
                data-testid="native-apply-title"
                disabled={title === document.definition.title}
                onClick={() => command({ type: "title", title })}
              >
                Apply title
              </button>
              <button
                data-testid="native-save"
                disabled={hasBuffers || !dirty}
                onClick={() => void save()}
              >
                Save process
              </button>
              <button
                data-testid="native-check"
                disabled={hasBuffers}
                onClick={() => void validate()}
              >
                Check readiness
              </button>
              <button
                data-testid="native-undo"
                disabled={!history.past.length || hasBuffers}
                onClick={() => {
                  const next = undo(history);
                  setHistory(next);
                  setTitle(next.present.definition.title);
                  setStatus("Undid the last complete edit.");
                }}
              >
                Undo
              </button>
              <button
                data-testid="native-redo"
                disabled={!history.future.length || hasBuffers}
                onClick={() => {
                  const next = redo(history);
                  setHistory(next);
                  setTitle(next.present.definition.title);
                  setStatus("Redid the last complete edit.");
                }}
              >
                Redo
              </button>
            </div>
            <p>
              <strong>
                {dirty
                  ? "Unsaved changes"
                  : saved
                    ? `Saved revision ${saved.revision}`
                    : "New process"}
              </strong>{" "}
              · {document.definition.steps.length} steps ·{" "}
              {document.definition.connections.length} connections ·{" "}
              {document.definition.outputs.length} declared outputs
            </p>
            {conflict && (
              <section className="native-warning" aria-label="Save conflict">
                <h2>Resolve concurrent changes</h2>
                <p>
                  Your local definition remains intact. Loading the current
                  saved version replaces this draft only after confirmation.
                  Saving a copy preserves both definitions.
                </p>
                <button
                  data-testid="native-load-current"
                  onClick={() =>
                    guard(
                      "Replace draft with current saved version",
                      () => void loadDocument(document.definition.id),
                    )
                  }
                >
                  Load current saved version
                </button>
                <button
                  data-testid="native-save-copy"
                  onClick={() => {
                    const copy = structuredClone(document);
                    copy.definition.id = newId("process");
                    reset(copy);
                    setStatus(
                      "Copy created locally. Save to preserve it alongside the other version.",
                    );
                  }}
                >
                  Create a separate copy
                </button>
              </section>
            )}
            <div className="native-actions">
              <label>
                Add step
                <select
                  data-testid="native-operation"
                  value={operation}
                  onChange={(e) => setOperation(e.target.value)}
                >
                  {contract.operations.map((op) => (
                    <option key={op.id}>{op.id}</option>
                  ))}
                </select>
              </label>
              <button
                data-testid="native-add-step"
                disabled={!operation || document.definition.steps.length >= 100}
                onClick={() => {
                  const id = newId("step");
                  if (
                    command({
                      type: "add-step",
                      operation,
                      id,
                      title: operation.split("@")[0].replaceAll(".", " "),
                    })
                  )
                    setSelected(id);
                }}
              >
                Add step
              </button>
              <label>
                Select step
                <select
                  data-testid="native-step-list"
                  value={selected ?? ""}
                  onChange={(e) => setSelected(e.target.value || null)}
                >
                  <option value="">Choose step</option>
                  {document.definition.steps.map((step) => (
                    <option value={step.id} key={step.id}>
                      {step.title}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="native-editor-grid">
              <div className="native-graph-region">
                <NativeCanvas
                  document={document}
                  selected={selected}
                  selectedPort={sourcePort || null}
                  select={selectStep}
                  choosePort={choosePort}
                  connect={connect}
                  move={move}
                />
                <fieldset className="native-connection-controls">
                  <legend>Connect exact ports</legend>
                  <p>
                    Choose an output, then its destination input. These controls
                    also work with a keyboard.
                  </p>
                  <label>
                    From output
                    <select
                      data-testid="native-connect-source"
                      value={sourcePort}
                      onChange={(e) => setSourcePort(e.target.value)}
                    >
                      <option value="">Choose output port</option>
                      {document.definition.ports
                        .filter((port) => port.direction === "output")
                        .map((port) => (
                          <option value={port.id} key={port.id}>
                            {portLabel(port.id)}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    To input
                    <select
                      data-testid="native-connect-target"
                      value={targetPort}
                      onChange={(e) => setTargetPort(e.target.value)}
                    >
                      <option value="">Choose input port</option>
                      {document.definition.ports
                        .filter((port) => port.direction === "input")
                        .map((port) => (
                          <option value={port.id} key={port.id}>
                            {portLabel(port.id)}
                          </option>
                        ))}
                    </select>
                  </label>
                  <button
                    data-testid="native-connect"
                    disabled={!sourcePort || !targetPort}
                    onClick={() => connect(sourcePort, targetPort)}
                  >
                    Connect ports
                  </button>
                </fieldset>
              </div>
              <NativeInspector
                key={selected ?? "none"}
                document={document}
                contract={contract}
                selected={selected}
                buffer={selected ? buffers[selected] : undefined}
                updateBuffer={updateBuffer}
                command={command}
                select={setSelected}
              />
            </div>
          </fieldset>
          {currentCheck && (
            <section
              className="native-check-results"
              aria-label="Service readiness results"
            >
              <h2>
                {currentCheck.ready
                  ? "Ready for execution"
                  : "Readiness findings"}
              </h2>
              <p>
                This is a validation result. It does not prove that a process
                ran or produced an artifact.
              </p>
              <ul>
                {currentCheck.findings.map((finding, index) => (
                  <li key={index}>
                    <strong>{finding.code}</strong>: {finding.message}{" "}
                    {finding.recovery}
                    {finding.step_id && (
                      <button
                        data-testid={`native-finding-${index}`}
                        onClick={() => setSelected(finding.step_id!)}
                      >
                        Inspect step
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}
          {check && !currentCheck && (
            <p role="status">
              The definition changed after its last readiness check. Check it
              again.
            </p>
          )}
          <details className="native-source">
            <summary data-testid="native-source-toggle">
              Process language · canonical source and readable steps
            </summary>
            <p>
              This versioned document is the source of truth for the canvas,
              programmatic clients and runtime. Layout is separate. Input
              configuration appears in the Inspector.
            </p>
            <ol>
              {document.definition.steps.map((step) => (
                <li key={step.id}>
                  <strong>{step.title}</strong> uses{" "}
                  <code>{step.operation}</code>;{" "}
                  {
                    document.definition.ports.filter(
                      (port) =>
                        port.step_id === step.id && port.direction === "input",
                    ).length
                  }{" "}
                  input ports.
                </li>
              ))}
            </ol>
            <label>
              Canonical process source
              <textarea
                data-testid="native-source"
                readOnly
                value={semantic}
                rows={12}
                spellCheck={false}
              />
            </label>
            {saved && (
              <p>
                Last saved semantic digest: <code>{saved.semantic_digest}</code>
                {dirty ? " (the current draft may differ)" : ""}
              </p>
            )}
          </details>
          <p
            className="native-execution-boundary"
            data-testid="native-execution-boundary"
          >
            Run inspection is not available in this authoring increment.
            Readiness checks and declared outputs are not execution evidence.
          </p>
        </>
      )}
      {pendingAction && (
        <NativeConfirmDialog
          title={pendingAction.label}
          stay={() => setPendingAction(null)}
          proceed={() => {
            const action = pendingAction.action;
            setPendingAction(null);
            action();
          }}
        >
          <p>
            You have unsaved changes. Stay to save them, or continue. Navigation
            retains a recovery draft in this tab when browser storage is
            available; opening another definition replaces the current draft.
          </p>
        </NativeConfirmDialog>
      )}
    </div>
  );
}

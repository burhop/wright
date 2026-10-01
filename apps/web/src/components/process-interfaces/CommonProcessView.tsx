import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ProcessClientError,
  type Action,
  type ArtifactRef,
  type InputBinding,
  type InputDefinition,
  type InputSnapshot,
  type InteractionSnapshot,
  type NavigationTarget,
  type ProcessClient,
  type Readiness,
  type Reason,
  type StartReceipt,
  type JsonValue,
  type ResponseRequest,
} from "@wright/process-client";
import {
  ActionButton,
  CheckpointCard,
  InputEditor,
  NavigationButton,
  ProcessUI,
  ProgressPanel,
  ReadinessPanel,
  ReasonNotice,
  RepresentationViewer,
  ResultCard,
  Section,
} from "@wright/ui-kit";
import {
  sameProcessReference,
  type ProcessNavigationRequest,
} from "../../services/process-navigation";
import {
  compactInput,
  createProcessViewRecoveryStore,
  processViewReason,
  processViewRequestId,
  type ProcessViewRecovery,
  type ProcessViewRecoveryStore,
} from "../../services/process-view-recovery";

export interface CommonProcessViewProps {
  readonly client: ProcessClient;
  readonly sessionId: string;
  readonly title?: string;
  readonly runId?: string;
  readonly readOnly?: boolean;
  readonly theme?: "dark" | "light";
  readonly recoveryStore?: ProcessViewRecoveryStore;
  readonly onUpload?: (
    file: File,
    definition: InputDefinition,
  ) => Promise<ArtifactRef>;
  readonly canReadRepresentations?: boolean;
  readonly canNavigate?: boolean;
  readonly onRunAttached?: (runId: string, receipt?: StartReceipt) => void;
  readonly onPrepareAnother?: () => void;
  readonly navigation?: ProcessNavigationRequest;
}

const terminal = (state: InteractionSnapshot["state"]) =>
  ["completed", "failed", "cancelled"].includes(state);
const clientIdentities = new WeakMap<ProcessClient, number>();
let nextClientIdentity = 0;
function clientIdentity(client: ProcessClient): number {
  const existing = clientIdentities.get(client);
  if (existing !== undefined) return existing;
  const next = ++nextClientIdentity;
  clientIdentities.set(client, next);
  return next;
}
const message = (error: unknown): Reason =>
  error instanceof ProcessClientError
    ? error.reason
    : {
        code: "CAPABILITY_UNAVAILABLE",
        message: "Wright could not finish this request.",
        correction:
          "Refresh the saved view and inspect the related step. No automatic retry was sent.",
      };
function binding(definition: InputDefinition): InputBinding | null {
  const value = definition.current_value;
  if (!value) return null;
  // Owning schemas permit omitted default discriminators; preserve actual values and provenance.
  if ("reference" in value) return { ...value, kind: "file" };
  if ("option_id" in value) return { ...value, kind: "option" };
  return { ...value, kind: "value" };
}
function RepresentationDownload({ blob, name }: { blob: Blob; name: string }) {
  const [link, setLink] = useState<{ blob: Blob; url: string }>();
  useEffect(() => {
    const url = URL.createObjectURL(blob);
    setLink({ blob, url });
    return () => URL.revokeObjectURL(url);
  }, [blob]);
  return link?.blob === blob ? (
    <a
      className="wp-link"
      href={link.url}
      download={name.split("/").at(-1) || "representation"}
    >
      Download exact file
    </a>
  ) : null;
}
function mergePage(
  current: InteractionSnapshot,
  next: InteractionSnapshot,
): InteractionSnapshot {
  if (
    current.context.cursor !== next.context.cursor ||
    current.context.run_id !== next.context.run_id ||
    current.context.input_snapshot_id !== next.context.input_snapshot_id ||
    current.context.input_digest !== next.context.input_digest
  )
    throw new ProcessClientError({
      code: "SUBJECT_STALE",
      message: "The results changed while this page was loading.",
      correction: "Refresh the view to inspect the current result revisions.",
    });
  const merge = <T,>(
    a: readonly T[] | undefined,
    b: readonly T[] | undefined,
    key: (item: T) => string,
  ) =>
    Array.from(
      new Map(
        [...(a ?? []), ...(b ?? [])].map((item) => [key(item), item]),
      ).values(),
    );
  return {
    ...next,
    inputs: merge(current.inputs, next.inputs, (i) => i.input_id),
    outputs: merge(current.outputs, next.outputs, (o) => o.result_id),
    interactions: merge(
      current.interactions,
      next.interactions,
      (i) => i.checkpoint_id,
    ),
    actions: merge(current.actions, next.actions, (a) => a.action_id),
    observations: merge(
      current.observations,
      next.observations,
      (o) => o.observation_id,
    ),
    navigation: merge(current.navigation, next.navigation, (n) =>
      JSON.stringify(n),
    ),
  };
}

/** Key the controller to its host-derived scope. Late replies never enter another process/run. */
export function CommonProcessView(props: CommonProcessViewProps) {
  const { process } = props.client;
  const key = JSON.stringify([
    clientIdentity(props.client),
    props.sessionId,
    process.workspace_id,
    process.source_path,
    process.source_digest,
    props.runId ?? null,
  ]);
  return <CommonProcessController key={key} {...props} />;
}

function CommonProcessController({
  client,
  sessionId,
  title,
  runId,
  readOnly = false,
  theme,
  recoveryStore,
  onUpload,
  canReadRepresentations = false,
  canNavigate = false,
  onRunAttached,
  onPrepareAnother,
  navigation,
}: CommonProcessViewProps) {
  const store = useMemo(
    () =>
      recoveryStore ??
      createProcessViewRecoveryStore(client.process, sessionId),
    [recoveryStore, client, sessionId],
  );
  const [snapshot, setSnapshot] = useState<InteractionSnapshot>();
  const snapshotRef = useRef<InteractionSnapshot | undefined>(undefined);
  const [prepared, setPrepared] = useState<InputSnapshot>();
  const preparedRef = useRef<InputSnapshot | undefined>(undefined);
  const [readiness, setReadiness] = useState<Readiness>();
  const [drafts, setDrafts] = useState<Record<string, InputBinding | null>>({});
  const [answers, setAnswers] = useState<Record<string, JsonValue | undefined>>({});
  const [pendingResponse, setPendingResponse] = useState<ResponseRequest>();
  const draftsRef = useRef<Record<string, InputBinding | null>>({});
  const [dirty, setDirty] = useState(false);
  const [recovery, setRecovery] = useState<ProcessViewRecovery | null>(null);
  const recoveryRef = useRef<ProcessViewRecovery | null>(null);
  const [activeRun, setActiveRun] = useState<string | undefined>(runId);
  const activeRunRef = useRef(runId);
  const [busy, setBusy] = useState("");
  const [uploadCount, setUploadCount] = useState(0);
  const [navigationReason, setNavigationReason] = useState<Reason>();
  const uploads = useRef(0);
  const operation = useRef(false);
  const [reason, setReason] = useState<Reason>();
  const [storageReason, setStorageReason] = useState<Reason>();
  const [loading, setLoading] = useState(true);
  const [activity, setActivity] = useState<string>();
  const [connection, setConnection] = useState<"connected" | "reconnecting">();
  const [following, setFollowing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [now, setNow] = useState(Date.now);
  const [representation, setRepresentation] = useState<{
    reference: ArtifactRef;
    blob?: Blob;
  }>();
  const representationGeneration = useRef(0);
  const workingRoot = useRef<HTMLDivElement | null>(null);
  const focusedNavigation = useRef<string | undefined>(undefined);
  const representationRead = useRef<AbortController | undefined>(undefined);
  const alive = useRef(false);
  const revision = useRef(0);
  const readGeneration = useRef(0);
  const onRunAttachedRef = useRef(onRunAttached);
  useEffect(() => {
    onRunAttachedRef.current = onRunAttached;
  }, [onRunAttached]);
  const invalidatePendingReads = useCallback(() => {
    representationGeneration.current++;
    representationRead.current?.abort();
    representationRead.current = undefined;
    readGeneration.current++;
  }, []);

  const remember = useCallback(
    (value: ProcessViewRecovery | null) => {
      if (value) store.write(value);
      else store.clear();
      recoveryRef.current = value;
      if (alive.current) setRecovery(value);
    },
    [store],
  );
  const publish = useCallback((value: InteractionSnapshot) => {
    // Compare new observations with the read's receipt time, not a previous tick.
    setNow(Date.now());
    snapshotRef.current = value;
    setSnapshot(value);
    if (!activeRunRef.current && preparedRef.current && value.readiness)
      setReadiness(value.readiness);
  }, []);
  const attachReceipt = useCallback(
    (receipt: StartReceipt, attempt: ProcessViewRecovery) => {
      // Persist acceptance even if the observer closed during the request.
      const saved = store.read();
      if (saved?.start?.requestId === attempt.start?.requestId)
        remember({
          ...attempt,
          start: { requestId: receipt.request_id, receipt },
        });
      if (!alive.current) return;
      activeRunRef.current = receipt.run_id;
      setActiveRun(receipt.run_id);
      setReason(undefined);
      setActivity("Start accepted; waiting for recorded progress.");
      onRunAttachedRef.current?.(receipt.run_id, receipt);
    },
    [store, remember],
  );

  useEffect(() => {
    alive.current = true;
    const control = new AbortController();
    let mounted = true;
    const initialize = async () => {
      let saved: ProcessViewRecovery | null = null;
      try {
        saved = store.read();
      } catch (error) {
        if (mounted) setStorageReason(message(error));
      }
      if (!mounted) return;
      // An explicit recorded-run tab cannot adopt a different recovery record.
      if (runId && saved?.start?.receipt?.run_id !== runId) saved = null;
      recoveryRef.current = saved;
      setRecovery(saved);
      preparedRef.current = saved?.input;
      setPrepared(saved?.input);
      const restoredRun = runId ?? saved?.start?.receipt?.run_id;
      activeRunRef.current = restoredRun;
      setActiveRun(restoredRun);
      if (restoredRun) {
        setLoading(false);
        onRunAttachedRef.current?.(restoredRun, saved?.start?.receipt);
        return;
      }
      try {
        const next = await client.getSnapshot({
          inputSnapshotId: saved?.input.snapshot_id,
          signal: control.signal,
        });
        if (!mounted) return;
        publish(next);
        setReadiness(saved ? (next.readiness ?? undefined) : undefined);
        if (saved?.start && !saved.start.receipt)
          setReason({
            code: "OUTCOME_UNKNOWN",
            message:
              "The previous start request has no confirmed acknowledgement.",
            correction:
              "Reconcile that exact request. A new start is disabled until its outcome is known.",
          });
      } catch (error) {
        if (mounted) setReason(message(error));
      } finally {
        if (mounted) setLoading(false);
      }
    };
    void initialize();
    const clock = setInterval(() => setNow(Date.now()), 1000);
    return () => {
      mounted = false;
      alive.current = false;
      control.abort();
      clearInterval(clock);
      invalidatePendingReads();
    };
  }, [client, store, runId, publish, invalidatePendingReads]);

  useEffect(() => {
    if (!activeRun) return;
    const control = new AbortController();
    let mounted = true;
    setFollowing(true);
    setConnection(undefined);
    setLoading(true);
    void (async () => {
      try {
        for await (const update of client.follow({
          runId: activeRun,
          signal: control.signal,
        })) {
          if (!mounted) return;
          if (update.type === "snapshot") {
            publish(update.snapshot);
            setLoading(false);
          } else if (update.type === "connection") setConnection(update.state);
          else if (update.type === "reconciliation") setReason(update.reason);
          else {
            const event = update.page.events?.at(-1);
            if (event?.task_title)
              setActivity(
                `${event.task_title}${event.kind === "task_completed" ? " complete" : ""}`,
              );
          }
        }
      } catch (error) {
        if (mounted) setReason(message(error));
      } finally {
        if (mounted) {
          setFollowing(false);
          setConnection(undefined);
          setLoading(false);
        }
      }
    })();
    return () => {
      mounted = false;
      control.abort();
    };
  }, [client, activeRun, refreshKey, publish]);

  const refresh = async () => {
    if (operation.current) return;
    if (activeRunRef.current) {
      setReason(undefined);
      setRefreshKey((v) => v + 1);
      return;
    }
    const generation = ++readGeneration.current,
      draftRevision = revision.current;
    setLoading(true);
    try {
      const saved = store.read();
      setStorageReason(undefined);
      if (saved?.start && recoverStart(saved)) return;
      const next = await client.getSnapshot({
        inputSnapshotId: preparedRef.current?.snapshot_id,
      });
      if (
        alive.current &&
        generation === readGeneration.current &&
        draftRevision === revision.current
      ) {
        publish(next);
        setReason(undefined);
      }
    } catch (error) {
      if (alive.current && generation === readGeneration.current)
        setReason(message(error));
    } finally {
      if (alive.current && generation === readGeneration.current)
        setLoading(false);
    }
  };
  const recoverStart = (saved: ProcessViewRecovery | null): boolean => {
    if (!saved?.start) return false;
    recoveryRef.current = saved;
    setRecovery(saved);
    preparedRef.current = saved.input;
    setPrepared(saved.input);
    if (saved.start.receipt) attachReceipt(saved.start.receipt, saved);
    else
      setReason({
        code: "OUTCOME_UNKNOWN",
        message: "Another view has a start request awaiting acknowledgement.",
        correction:
          "Reconcile its exact request before changing the inputs or starting again.",
      });
    return true;
  };
  const edit = (definition: InputDefinition, value: InputBinding | null) => {
    if (
      operation.current ||
      storageReason ||
      readOnly ||
      activeRunRef.current ||
      recoveryRef.current?.start
    )
      return;
    try {
      if (recoverStart(store.read())) return;
      if (recoveryRef.current) remember(null);
    } catch (error) {
      setStorageReason(message(error));
      return;
    }
    revision.current++;
    readGeneration.current++;
    preparedRef.current = undefined;
    setPrepared(undefined);
    setReadiness(undefined);
    draftsRef.current = { ...draftsRef.current, [definition.input_id]: value };
    setDrafts(draftsRef.current);
    setDirty(true);
    setReason(undefined);
  };
  const prepare = async () => {
    if (
      operation.current ||
      uploads.current > 0 ||
      storageReason ||
      readOnly ||
      activeRunRef.current ||
      recoveryRef.current?.start ||
      !snapshotRef.current
    )
      return;
    operation.current = true;
    setBusy("prepare");
    setReason(undefined);
    try {
      if (recoverStart(store.read())) return;
      const values = (snapshotRef.current.inputs ?? [])
        .map((input) =>
          Object.hasOwn(draftsRef.current, input.input_id)
            ? draftsRef.current[input.input_id]
            : binding(input),
        )
        .filter((value): value is InputBinding => value !== null);
      const input = await client.setInputs(values);
      if (!alive.current) return;
      if (recoverStart(store.read())) return;
      remember({ version: "1", input: compactInput(input) });
      preparedRef.current = input;
      setPrepared(input);
      setStorageReason(undefined);
      const assessed = await client.checkReadiness(input);
      if (!alive.current) return;
      setReadiness(assessed);
      const next = await client.getSnapshot({
        inputSnapshotId: input.snapshot_id,
      });
      if (!alive.current) return;
      publish(next);
      setDirty(false);
      draftsRef.current = {};
      setDrafts({});
    } catch (error) {
      if (alive.current) setReason(message(error));
    } finally {
      operation.current = false;
      if (alive.current) setBusy("");
    }
  };
  const expired =
    !!readiness?.expires_at &&
    (!Number.isFinite(Date.parse(readiness.expires_at)) ||
      Date.parse(readiness.expires_at) <= now);
  const start = async (reconcile = false) => {
    if (
      operation.current ||
      uploads.current > 0 ||
      readOnly ||
      activeRunRef.current ||
      storageReason
    )
      return;
    const input = preparedRef.current;
    if (
      !input ||
      (!reconcile &&
        (dirty ||
          !readiness ||
          readiness.state !== "ready" ||
          expired ||
          !snapshotRef.current?.actions?.some(
            (a) =>
              a.operation === "start" &&
              a.enabled &&
              a.subject_digest === input.digest,
          )))
    )
      return;
    operation.current = true;
    setBusy("start");
    setReason(undefined);
    let attemptedRequest: string | undefined;
    try {
      const saved = store.read();
      if (saved?.start?.receipt) {
        attachReceipt(saved.start.receipt, saved);
        return;
      }
      if (
        saved?.start &&
        (saved.input.snapshot_id !== input.snapshot_id ||
          saved.input.digest !== input.digest)
      )
        throw processViewReason(
          "Another start request needs reconciliation first.",
        );
      if (reconcile && !saved?.start)
        throw processViewReason(
          "The exact saved start request is unavailable.",
        );
      const requestId =
        saved?.start?.requestId ??
        (await processViewRequestId(
          "start",
          `${input.snapshot_id}:${input.digest}`,
        ));
      if (!alive.current) return;
      const latest = store.read();
      if (latest?.start?.requestId && latest.start.requestId !== requestId) {
        recoverStart(latest);
        return;
      }
      const attempt: ProcessViewRecovery = {
        version: "1",
        input: compactInput(input),
        start: { requestId },
      };
      remember(attempt); // Must succeed before any process mutation is submitted.
      attemptedRequest = requestId;
      const receipt = await client.start(input, requestId);
      attachReceipt(receipt, attempt);
    } catch (error) {
      if (alive.current) {
        setReason(message(error));
        if (
          error instanceof ProcessClientError &&
          !error.uncertain &&
          error.httpStatus &&
          error.httpStatus < 500
        ) {
          const saved = store.read();
          if (
            attemptedRequest &&
            saved?.start &&
            saved.start.requestId === attemptedRequest &&
            !saved.start.receipt
          )
            remember({ version: "1", input: saved.input });
        }
      }
    } finally {
      operation.current = false;
      if (alive.current) setBusy("");
    }
  };
  const cancel = async () => {
    const current = activeRunRef.current;
    if (
      !current ||
      operation.current ||
      readOnly ||
      !snapshotRef.current?.actions?.some(
        (a) => a.operation === "cancel" && a.enabled,
      )
    )
      return;
    operation.current = true;
    setBusy("cancel");
    try {
      const requestId = await processViewRequestId("cancel", current);
      // This deterministic identity is preserved on every repeat, including recorded-run tabs.
      try {
        const saved = store.read();
        if (saved?.start?.receipt?.run_id === current)
          remember({ ...saved, cancellation: { requestId, runId: current } });
      } catch (error) {
        // The deterministic run-derived cancellation ID survives without a browser journal.
        if (alive.current) setStorageReason(message(error));
      }
      const receipt = await client.cancel(current, requestId);
      if (!alive.current) return;
      setReason({
        code: "CANCELLATION_REQUESTED",
        message: "Cancellation was requested.",
        correction:
          "Wait for the recorded outcome; the request does not confirm the operation has stopped.",
      });
      if (receipt.run_id === current) setRefreshKey((v) => v + 1);
    } catch (error) {
      if (alive.current) setReason(message(error));
    } finally {
      operation.current = false;
      if (alive.current) setBusy("");
    }
  };
  const navigate = canNavigate
    ? (target: NavigationTarget) => {
        const pinned =
          target.run_id || !activeRunRef.current
            ? target
            : { ...target, run_id: activeRunRef.current };
        void client.navigate(pinned).catch((error) => {
          if (alive.current) setNavigationReason(message(error));
        });
      }
    : undefined;
  const upload = onUpload
    ? async (file: File, definition: InputDefinition) => {
        uploads.current++;
        setUploadCount(uploads.current);
        try {
          return await onUpload(file, definition);
        } finally {
          uploads.current--;
          if (alive.current) setUploadCount(uploads.current);
        }
      }
    : undefined;
  const requestRepresentation = useCallback(
    (reference: ArtifactRef) => {
      const generation = ++representationGeneration.current;
      representationRead.current?.abort();
      const control = new AbortController();
      representationRead.current = control;
      setRepresentation({ reference });
      void client
        .getRepresentation(
          reference,
          activeRunRef.current
            ? { runId: activeRunRef.current, signal: control.signal }
            : {
                inputSnapshotId: preparedRef.current?.snapshot_id,
                signal: control.signal,
              },
        )
        .then((blob) => {
          if (alive.current && generation === representationGeneration.current)
            setRepresentation({ reference, blob });
        })
        .catch((error) => {
          if (
            alive.current &&
            generation === representationGeneration.current
          ) {
            setRepresentation(undefined);
            setReason(message(error));
          }
        });
    },
    [client],
  );
  const openRepresentation = canReadRepresentations
    ? requestRepresentation
    : undefined;
  useEffect(() => {
    if (
      !navigation ||
      focusedNavigation.current === navigation.requestId ||
      !snapshot
    )
      return;
    const {
      process,
      target,
      representation: reference,
    } = navigation.resolution;
    if (
      !sameProcessReference(process, client.process) ||
      target.run_id !== snapshot.context.run_id
    ) {
      focusedNavigation.current = navigation.requestId;
      setNavigationReason({
        code: "SCOPE_DENIED",
        message: "This item belongs to another process or run.",
        correction: "Open it from its exact recorded working view.",
      });
      return;
    }
    if (target.kind === "process" || target.kind === "block") return;
    const output = snapshot.outputs?.find(
      (item) => item.result_id === target.result_id,
    );
    if (target.kind !== "run" && !output) {
      setNavigationReason({
        code: "CAPABILITY_UNAVAILABLE",
        message: "The requested result is not in the loaded page.",
        correction: snapshot.next_page
          ? "Load the next results page to inspect this exact item."
          : "Refresh the exact run or use its canonical result reader.",
      });
      return;
    }
    if (
      target.kind === "assessment" &&
      !output?.assessments?.some(
        (item) => item.assessment_id === target.assessment_id,
      )
    ) {
      focusedNavigation.current = navigation.requestId;
      setNavigationReason({
        code: "SUBJECT_STALE",
        message: "The requested assessment is not linked to this result.",
        correction: "Refresh the exact result and assessment.",
      });
      return;
    }
    focusedNavigation.current = navigation.requestId;
    setNavigationReason(undefined);
    const selector =
      target.kind === "run"
        ? "[data-process-section=progress]"
        : target.kind === "assessment"
          ? "[data-assessment-id]"
          : "[data-result-id]";
    const destination = [
      ...(workingRoot.current?.querySelectorAll<HTMLElement>(selector) ?? []),
    ].find(
      (element) =>
        target.kind === "run" ||
        (target.kind === "assessment"
          ? element.dataset.assessmentId === target.assessment_id
          : element.dataset.resultId === target.result_id),
    );
    destination?.focus();
    destination?.scrollIntoView?.({ block: "nearest" });
    if (
      reference &&
      (target.kind === "assessment" || target.kind === "evidence")
    ) {
      if (openRepresentation) openRepresentation(reference);
      else
        setNavigationReason({
          code: "CAPABILITY_UNAVAILABLE",
          message: "This view cannot read the recorded representation.",
          correction: "Open the exact file with its supported reader.",
        });
    }
  }, [navigation, snapshot, client, openRepresentation]);
  const loadMore = async () => {
    const previous = snapshotRef.current;
    if (!previous?.next_page || operation.current) return;
    operation.current = true;
    setBusy("page");
    try {
      const next = await client.getSnapshot({
        runId: activeRunRef.current,
        inputSnapshotId: activeRunRef.current
          ? undefined
          : preparedRef.current?.snapshot_id,
        page: previous.next_page,
      });
      if (alive.current && previous === snapshotRef.current)
        publish(mergePage(previous, next));
    } catch (error) {
      if (alive.current) setReason(message(error));
    } finally {
      operation.current = false;
      if (alive.current) setBusy("");
    }
  };
  const respond = async (
    action: Action,
    value: JsonValue,
    reconcile = false,
  ) => {
    if (
      operation.current ||
      readOnly ||
      !activeRunRef.current ||
      !action.checkpoint_id ||
      !action.subject_digest
    )
      return;
    if (
      !reconcile &&
      (!action.enabled ||
        pendingResponse ||
        !snapshotRef.current?.actions?.some(
          (item) =>
            item.operation === "respond" &&
            item.enabled &&
            item.checkpoint_id === action.checkpoint_id &&
            item.subject_digest === action.subject_digest,
        ))
    )
      return;
    const attempt = reconcile
      ? pendingResponse
      : {
          checkpointId: action.checkpoint_id,
          subjectDigest: action.subject_digest,
          value: JSON.parse(JSON.stringify(value)) as JsonValue,
          requestId: crypto.randomUUID(),
        };
    if (!attempt) return;
    operation.current = true;
    setPendingResponse(attempt);
    setBusy("respond");
    setReason(undefined);
    try {
      const response = await client.respond(attempt);
      if (response.run_id !== activeRunRef.current)
        throw new ProcessClientError(
          {
            code: "OUTCOME_UNKNOWN",
            message: "The saved response does not identify this run.",
            correction:
              "Refresh this exact run and inspect its declared input before continuing.",
          },
          { uncertain: true, requestId: attempt.requestId },
        );
      if (!alive.current) return;
      setPendingResponse(undefined);
      setRefreshKey((key) => key + 1);
    } catch (error) {
      if (alive.current) {
        setReason(message(error));
        if (error instanceof ProcessClientError && !error.uncertain)
          setPendingResponse(undefined);
      }
    } finally {
      operation.current = false;
      if (alive.current) setBusy("");
    }
  };
  const pendingStart = !!recovery?.start && !recovery.start.receipt;
  const startDisabledReason: Reason | undefined = pendingStart
    ? {
        code: "OUTCOME_UNKNOWN",
        message: "A previous start is awaiting reconciliation.",
        correction:
          "Use Reconcile start request to resolve the same request identity.",
      }
    : dirty || !prepared
      ? {
          code: "INPUT_REQUIRED",
          message: "These values have not been prepared for a run.",
          correction: "Choose Prepare and check inputs before starting.",
        }
      : expired
        ? {
            code: "OPTION_STALE",
            message: "The readiness check has expired.",
            correction:
              "Refresh readiness before starting; live choices may have changed.",
          }
        : storageReason;
  const startAction = snapshot?.actions?.find((a) => a.operation === "start");
  const permittedStart: Action | undefined = startAction && {
    ...startAction,
    enabled:
      startAction.enabled &&
      !activeRun &&
      !startDisabledReason &&
      readiness?.state === "ready" &&
      readiness.input_digest === prepared?.digest &&
      startAction.subject_digest === prepared?.digest,
    reasons: startDisabledReason
      ? [startDisabledReason, ...(startAction.reasons ?? [])]
      : startAction.reasons,
  };

  return (
    <ProcessUI theme={theme} className="common-process-view">
      <div data-testid="common-process-view" ref={workingRoot}>
        <header className="wp-row">
          <h1>
            {title ??
              client.process.source_path
                .split("/")
                .at(-1)
                ?.replace(/\.workflow\.wflow$|\.wflow$/i, "") ??
              "Process"}
          </h1>
          <NavigationButton
            title="Open process"
            target={{
              kind: "process",
              ...(activeRun ? { run_id: activeRun } : {}),
            }}
            onNavigate={navigate}
          />
          <button
            type="button"
            className="wp-link"
            disabled={!!busy || loading}
            onClick={() => void refresh()}
          >
            Refresh view
          </button>
        </header>
        {readOnly && <p className="wp-muted">This view is read-only.</p>}
        {loading && <p role="status">Loading the saved process state…</p>}
        {storageReason && (
          <ReasonNotice reason={storageReason} onNavigate={navigate} />
        )}
        {navigationReason && (
          <ReasonNotice reason={navigationReason} onNavigate={navigate} />
        )}
        {reason && (
          <ReasonNotice
            reason={reason}
            tone={reason.code === "CANCELLATION_REQUESTED" ? "info" : "error"}
            onNavigate={navigate}
          />
        )}
        {busy === "start" && (
          <p role="status">Sending the prepared run to Wright…</p>
        )}
        {pendingStart && (
          <button
            type="button"
            className="wp-button"
            disabled={readOnly || !!busy || !!storageReason}
            onClick={() => void start(true)}
          >
            Reconcile start request
          </button>
        )}
        {pendingResponse && !busy && (
          <button
            type="button"
            className="wp-link"
            disabled={readOnly}
            onClick={() =>
              void respond(
                {
                  action_id: "reconcile-response",
                  operation: "respond",
                  title: "Reconcile response request",
                  enabled: false,
                  checkpoint_id: pendingResponse.checkpointId,
                  subject_digest: pendingResponse.subjectDigest,
                },
                pendingResponse.value,
                true,
              )
            }
          >
            Reconcile response request
          </button>
        )}
        {snapshot && (
          <>
            <div className="wp-columns">
              <Section
                title={activeRun ? "Run inputs" : "Inputs"}
                description={
                  activeRun
                    ? "These are the frozen inputs used by this run."
                    : "Prepare the inputs for this run. The accepted process remains separate."
                }
              >
                {(snapshot.inputs ?? []).map((input) => (
                  <div key={input.input_id}>
                    <InputEditor
                      definition={input}
                      binding={
                        Object.hasOwn(drafts, input.input_id)
                          ? drafts[input.input_id]
                          : undefined
                      }
                      onChange={(value) => edit(input, value)}
                      onUpload={upload}
                      now={now}
                      disabled={
                        readOnly ||
                        !!activeRun ||
                        !!busy ||
                        pendingStart ||
                        !!storageReason
                      }
                    />
                    {input.default && !input.current_value && (
                      <p className="wp-muted">
                        A declared default is available; the backend checks its
                        use during preparation.
                      </p>
                    )}
                    <NavigationButton
                      title="Open input step"
                      target={{ kind: "block", block_id: input.block_id }}
                      onNavigate={navigate}
                    />
                  </div>
                ))}
                {!snapshot.inputs?.length && (
                  <p className="wp-muted">
                    No user inputs are available on this page.
                  </p>
                )}
                {!activeRun && (
                  <>
                    <button
                      type="button"
                      className="wp-button"
                      disabled={
                        readOnly ||
                        !!storageReason ||
                        !!busy ||
                        pendingStart ||
                        loading ||
                        uploadCount > 0
                      }
                      aria-busy={busy === "prepare" || undefined}
                      onClick={() => void prepare()}
                    >
                      {busy === "prepare"
                        ? "Preparing and checking…"
                        : "Prepare and check inputs"}
                    </button>
                    {uploadCount > 0 && (
                      <p role="status">
                        Finish preparing the selected files before checking
                        inputs.
                      </p>
                    )}
                    <ReadinessPanel
                      readiness={dirty ? undefined : readiness}
                      onNavigate={navigate}
                      now={now}
                    />
                    {permittedStart && (
                      <ActionButton
                        action={permittedStart}
                        readOnly={readOnly}
                        busy={busy === "start"}
                        onAction={!busy ? () => void start() : undefined}
                        onNavigate={navigate}
                      />
                    )}
                  </>
                )}
              </Section>
              <Section title="Progress" focusId="progress">
                {(snapshot.diagnostics ?? []).map((diagnostic, index) => (
                  <ReasonNotice
                    key={`${diagnostic.code}:${diagnostic.step_id ?? "run"}:${index}`}
                    reason={diagnostic}
                    onNavigate={navigate}
                  />
                ))}
                <ProgressPanel
                  state={snapshot.state}
                  observations={snapshot.observations ?? []}
                  activity={activity}
                  connection={connection}
                  now={now}
                />
                {activeRun && !following && !terminal(snapshot.state) && (
                  <p className="wp-muted">
                    Live updates are not attached. Refresh to reconcile the
                    saved run.
                  </p>
                )}
                {activeRun && (
                  <>
                    <p className="wp-muted">
                      Closing this view leaves the run with Wright.
                    </p>
                    <NavigationButton
                      title="Open run details"
                      target={{ kind: "run", run_id: activeRun }}
                      onNavigate={navigate}
                    />
                    <details>
                      <summary>Run identity</summary>
                      <code>{activeRun}</code>
                    </details>
                  </>
                )}
                {(snapshot.actions ?? [])
                  .filter((a) => a.operation !== "start" && !a.checkpoint_id)
                  .map((action) => (
                    <ActionButton
                      key={action.action_id}
                      action={action}
                      readOnly={readOnly}
                      busy={busy === "cancel"}
                      onAction={
                        action.operation === "cancel" && !busy
                          ? () => void cancel()
                          : undefined
                      }
                      onNavigate={navigate}
                    />
                  ))}
                {activeRun && terminal(snapshot.state) && onPrepareAnother && (
                  <button
                    type="button"
                    className="wp-link"
                    disabled={!!busy || readOnly}
                    onClick={() => {
                      try {
                        if (
                          recoveryRef.current?.start?.receipt?.run_id ===
                          activeRun
                        )
                          remember(null);
                        onPrepareAnother();
                      } catch (error) {
                        setReason(message(error));
                      }
                    }}
                  >
                    Prepare another run
                  </button>
                )}
              </Section>
            </div>
            {!!snapshot.interactions?.length && (
              <Section title="Declared interactions">
                {snapshot.interactions.map((interaction) => (
                  <CheckpointCard
                    key={interaction.checkpoint_id}
                    interaction={interaction}
                    actions={snapshot.actions ?? []}
                    onOpen={openRepresentation}
                    onNavigate={navigate}
                    response={
                      interaction.kind === "input"
                        ? {
                            value: answers[interaction.subject_digest],
                            onChange: (value) =>
                              setAnswers((current) => ({
                                ...current,
                                [interaction.subject_digest]: value,
                              })),
                            onSubmit: (action, value) =>
                              void respond(action, value),
                            busy: !!busy,
                            readOnly: readOnly || !!pendingResponse,
                            blockedReason: pendingResponse
                              ? {
                                  code: "OUTCOME_UNKNOWN",
                                  message:
                                    "This response is awaiting confirmation.",
                                  correction:
                                    "Use Reconcile response request to check the same saved answer.",
                                }
                              : undefined,
                          }
                        : undefined
                    }
                  >
                    <NavigationButton
                      title="Open interaction step"
                      target={{
                        kind: "block",
                        block_id: interaction.step_id,
                        ...(activeRun ? { run_id: activeRun } : {}),
                      }}
                      onNavigate={navigate}
                    />
                    {interaction.kind !== "input" && (
                      <p className="wp-muted">
                        Open the interaction step to inspect this checkpoint.
                        Response controls are unavailable in this view.
                      </p>
                    )}
                  </CheckpointCard>
                ))}
              </Section>
            )}
            <Section
              title="Results and checks"
              description="Inspect the exact output revisions and their linked assessments."
            >
              {(snapshot.outputs ?? []).map((output) => (
                <ResultCard
                  key={output.result_id}
                  output={output}
                  onNavigate={navigate}
                  onOpen={openRepresentation}
                />
              ))}
              {!snapshot.outputs?.length && (
                <p className="wp-muted">
                  No outputs are recorded on this page yet.
                </p>
              )}
              {!canReadRepresentations && (
                <p className="wp-muted">
                  Representation previews are unavailable in this host. Use the
                  exact result and evidence links.
                </p>
              )}
              {snapshot.next_page && (
                <button
                  type="button"
                  className="wp-link"
                  disabled={!!busy}
                  onClick={() => void loadMore()}
                >
                  {busy === "page"
                    ? "Loading more…"
                    : "Load more process information"}
                </button>
              )}
            </Section>
            {representation && (
              <Section title="Representation">
                <button
                  type="button"
                  className="wp-link"
                  onClick={() => {
                    representationGeneration.current++;
                    representationRead.current?.abort();
                    representationRead.current = undefined;
                    setRepresentation(undefined);
                  }}
                >
                  Close representation
                </button>
                {representation.blob ? (
                  <>
                    <RepresentationViewer
                      blob={representation.blob}
                      title={representation.reference.artifact_ref}
                    />
                    <RepresentationDownload
                      blob={representation.blob}
                      name={representation.reference.artifact_ref}
                    />
                  </>
                ) : (
                  <p role="status">Opening the exact representation…</p>
                )}
                <details>
                  <summary>Representation identity</summary>
                  <p>{representation.reference.artifact_ref}</p>
                  <code>{representation.reference.sha256}</code>
                </details>
              </Section>
            )}
          </>
        )}
      </div>
    </ProcessUI>
  );
}

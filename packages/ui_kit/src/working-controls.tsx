import { useEffect, useRef, useState } from "react";
import type {
  Action,
  InputBinding,
  InputSnapshot,
  InteractionSnapshot,
  JsonValue,
  NavigationTarget,
  ProcessClient,
  Readiness,
  Reason,
} from "@wright/process-client";
import { ProcessClientError } from "@wright/process-client";
import { InputEditor } from "./inputs";
import {
  ActionButton,
  CheckpointCard,
  ReadinessPanel,
  ReasonNotice,
  Section,
} from "./patterns";

type Intent = {
  version: 1;
  scope: string;
  kind: "start" | "review" | "response" | "action" | "cancel";
  requestId: string;
  checkpointId?: string;
  subjectDigest?: string;
  runId?: string;
};
const notice = (message: string, correction: string): Reason => ({
  code: "ACTION_NOT_PERMITTED",
  message,
  correction,
});
const uncertain = notice(
  "A request is awaiting confirmation.",
  "Reconcile the recorded request. If it remains uncertain, use Wright's common working view; do not submit another request.",
);

/** Shared form/controller composition over the existing scoped client; no executor. */
export function WorkingControls(props: {
  client: ProcessClient;
  snapshot: InteractionSnapshot;
  readOnly: boolean;
  onNavigate?: (target: NavigationTarget) => void;
}) {
  const { snapshot } = props;
  const p = snapshot.context.process;
  const scope = JSON.stringify([
    p.workspace_id,
    p.source_path,
    p.source_digest,
    snapshot.context.run_id ?? null,
  ]);
  return <ScopedControls key={scope} {...props} scope={scope} />;
}

function ScopedControls({
  client,
  snapshot,
  readOnly,
  onNavigate,
  scope,
}: {
  client: ProcessClient;
  snapshot: InteractionSnapshot;
  readOnly: boolean;
  onNavigate?: (target: NavigationTarget) => void;
  scope: string;
}) {
  const storageKey = "wright-working-control:" + scope;
  const [drafts, setDrafts] = useState<Record<string, InputBinding | null>>({});
  const [frozen, setFrozen] = useState<InputSnapshot>();
  const [readiness, setReadiness] = useState<Readiness>();
  const [prepared, setPrepared] = useState<InteractionSnapshot>();
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [responses, setResponses] = useState<
    Record<string, JsonValue | undefined>
  >({});
  const [reason, setReason] = useState<Reason>();
  const [pending, setPending] = useState<Intent>();
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [clock, setClock] = useState(Date.now);
  const active = useRef(true);
  const operation = useRef(false);
  const reads = useRef(new Set<AbortController>());
  const current = useRef(snapshot);
  current.current = snapshot;
  useEffect(() => {
    active.current = true;
    try {
      const raw = sessionStorage.getItem(storageKey);
      if (raw) {
        const value = JSON.parse(raw) as Intent;
        if (
          value.version !== 1 ||
          value.scope !== scope ||
          typeof value.requestId !== "string" ||
          !value.requestId
        )
          throw new Error("Invalid retained request");
        setPending(value);
      }
      setLoaded(true);
    } catch {
      setReason(
        notice(
          "Wright could not retain control requests in this view.",
          "Use the common working view to inspect or recover this process.",
        ),
      );
    }
    const timer = setInterval(() => setClock(Date.now()), 1000);
    return () => {
      active.current = false;
      for (const controller of reads.current) controller.abort();
      reads.current.clear();
      clearInterval(timer);
    };
  }, [scope, storageKey]);
  const blocked = readOnly || !loaded || busy || !!pending;
  const permitted = (action: Action, kind: string) =>
    !readOnly &&
    loaded &&
    !operation.current &&
    !pending &&
    action.operation === kind &&
    !!current.current.context.run_id &&
    !!action.subject_digest &&
    current.current.actions?.some(
      (a) =>
        a.enabled &&
        a.action_id === action.action_id &&
        a.operation === kind &&
        a.subject_digest === action.subject_digest &&
        a.checkpoint_id === action.checkpoint_id,
    );
  const failure = (error: unknown) =>
    error instanceof ProcessClientError
      ? error.reason
      : notice(
          "Wright could not confirm this operation.",
          "Inspect the same run in the common working view before trying another request.",
        );
  async function mutate(
    intent: Omit<Intent, "version" | "scope" | "requestId">,
    send: (id: string) => Promise<unknown>,
  ) {
    if (blocked || operation.current) return;
    operation.current = true;
    setBusy(true);
    setReason(undefined);
    let retained = false;
    try {
      const value: Intent = {
        ...intent,
        version: 1,
        scope,
        requestId: crypto.randomUUID(),
      };
      sessionStorage.setItem(storageKey, JSON.stringify(value));
      retained = true;
      setPending(value);
      await send(value.requestId);
      sessionStorage.removeItem(storageKey);
      if (active.current) setPending(undefined);
    } catch (error) {
      if (retained && error instanceof ProcessClientError && !error.uncertain) {
        try {
          sessionStorage.removeItem(storageKey);
          if (active.current) setPending(undefined);
        } catch {
          /* Preserve unresolved intent when persistence cannot be confirmed. */
        }
      }
      if (active.current) setReason(failure(error));
    } finally {
      operation.current = false;
      if (active.current) setBusy(false);
    }
  }
  async function check() {
    if (blocked || operation.current || current.current.context.run_id) return;
    operation.current = true;
    setBusy(true);
    setReason(undefined);
    setReadiness(undefined);
    setPrepared(undefined);
    setFrozen(undefined);
    const controller = new AbortController();
    reads.current.add(controller);
    try {
      const bindings = Object.values(drafts).filter(
        (b): b is InputBinding => b !== null,
      );
      const input = await client.setInputs(bindings, {
        signal: controller.signal,
      });
      const checked = await client.checkReadiness(input, {
        signal: controller.signal,
      });
      const projection = await client.getSnapshot({
        inputSnapshotId: input.snapshot_id,
        signal: controller.signal,
      });
      if (
        projection.context.process.workspace_id !==
          client.process.workspace_id ||
        projection.context.process.source_path !== client.process.source_path ||
        projection.context.process.source_digest !==
          client.process.source_digest ||
        projection.context.run_id ||
        checked.input_digest !== input.digest ||
        projection.readiness?.input_digest !== input.digest
      )
        throw new Error("Different input preparation");
      if (active.current) {
        setFrozen(input);
        setReadiness(checked);
        setPrepared(projection);
      }
    } catch (error) {
      if (active.current) setReason(failure(error));
    } finally {
      reads.current.delete(controller);
      operation.current = false;
      if (active.current) setBusy(false);
    }
  }
  async function reconcile() {
    if (!pending || operation.current) return;
    operation.current = true;
    setBusy(true);
    const controller = new AbortController();
    reads.current.add(controller);
    try {
      const observed = await client.getSnapshot({ signal: controller.signal });
      if (
        JSON.stringify([
          observed.context.process.workspace_id,
          observed.context.process.source_path,
          observed.context.process.source_digest,
          observed.context.run_id ?? null,
        ]) !== scope
      )
        throw new Error("Different process/run");
      const checkpoint = observed.interactions?.find(
        (i) =>
          i.checkpoint_id === pending.checkpointId &&
          i.subject_digest === pending.subjectDigest,
      );
      const confirmed =
        pending.kind === "review"
          ? checkpoint?.decision?.request_id === pending.requestId
          : pending.kind === "action"
            ? checkpoint?.action_receipt?.request_id === pending.requestId
            : false;
      if (confirmed) {
        sessionStorage.removeItem(storageKey);
        if (active.current) {
          setPending(undefined);
          setReason(undefined);
        }
      } else if (active.current) setReason(uncertain);
    } catch (error) {
      if (active.current) setReason(failure(error));
    } finally {
      reads.current.delete(controller);
      operation.current = false;
      if (active.current) setBusy(false);
    }
  }
  const expires = readiness?.expires_at
    ? Date.parse(readiness.expires_at)
    : NaN;
  const ready =
    readiness?.state === "ready" &&
    Number.isFinite(expires) &&
    expires > clock &&
    !!frozen &&
    prepared?.actions?.some(
      (action) =>
        action.operation === "start" &&
        action.enabled &&
        action.subject_digest === frozen.digest,
    );
  const runId = snapshot.context.run_id;
  return (
    <>
      <Section title={runId ? "Run inputs" : "Prepare the process"}>
        {!snapshot.inputs?.length && (
          <p>This process uses its configured inputs.</p>
        )}
        {(snapshot.inputs ?? []).map((definition) => (
          <InputEditor
            key={definition.input_id}
            definition={definition}
            binding={drafts[definition.input_id]}
            disabled={blocked || !!runId}
            onChange={(binding) => {
              setDrafts((d) => ({ ...d, [definition.input_id]: binding }));
              setFrozen(undefined);
              setReadiness(undefined);
              setPrepared(undefined);
            }}
            onUpload={async (file, input) => {
              const controller = new AbortController();
              reads.current.add(controller);
              try {
                return await client.uploadInput(input.input_id, file, {
                  signal: controller.signal,
                });
              } finally {
                reads.current.delete(controller);
              }
            }}
          />
        ))}
        {!runId && (
          <>
            <ReadinessPanel readiness={readiness} onNavigate={onNavigate} />
            {frozen &&
              readiness?.state === "ready" &&
              !prepared?.actions?.some(
                (action) =>
                  action.operation === "start" &&
                  action.enabled &&
                  action.subject_digest === frozen.digest,
              ) && (
                <ReasonNotice
                  reason={
                    prepared?.actions?.find(
                      (action) => action.operation === "start",
                    )?.reasons?.[0] ??
                    notice(
                      "Starting is not permitted from this interface.",
                      "Inspect this process's permitted actions in the common working view.",
                    )
                  }
                  onNavigate={onNavigate}
                />
              )}
            <button
              type="button"
              className="wp-button"
              disabled={blocked}
              onClick={() => void check()}
            >
              Check inputs and readiness
            </button>
            <button
              type="button"
              className="wp-button"
              disabled={blocked || !ready}
              onClick={() => {
                if (
                  !frozen ||
                  !ready ||
                  Date.parse(readiness!.expires_at!) <= Date.now()
                )
                  return;
                void mutate({ kind: "start" }, (id) =>
                  client.start(frozen, id),
                );
              }}
            >
              Start process
            </button>
          </>
        )}
      </Section>
      <Section title="Declared reviews and actions">
        {readOnly && <p>Preview: process controls are read-only.</p>}
        {reason && <ReasonNotice reason={reason} onNavigate={onNavigate} />}
        {pending && (
          <>
            <ReasonNotice reason={uncertain} />
            <button
              type="button"
              className="wp-button"
              disabled={busy}
              onClick={() => void reconcile()}
            >
              Reconcile recorded request
            </button>
          </>
        )}
        {!snapshot.interactions?.length && (
          <p>
            No declared interaction is currently available. Inspect diagnostics
            and assessments.
          </p>
        )}
        {(snapshot.interactions ?? []).map((interaction) => (
          <CheckpointCard
            key={interaction.checkpoint_id}
            interaction={interaction}
            actions={snapshot.actions ?? []}
            onNavigate={onNavigate}
            onOpen={(ref) =>
              onNavigate?.({
                kind: "evidence",
                artifact_ref: ref.artifact_ref,
                result_id: ref.result_id,
              })
            }
            review={{
              reason: reasons[interaction.checkpoint_id] ?? "",
              onReasonChange: (value) =>
                setReasons((r) => ({
                  ...r,
                  [interaction.checkpoint_id]: value,
                })),
              busy,
              readOnly: blocked,
              onSubmit: (action, decision, text) => {
                if (
                  !permitted(action, "review") ||
                  action.checkpoint_id !== interaction.checkpoint_id ||
                  action.subject_digest !== interaction.subject_digest
                )
                  return;
                void mutate(
                  {
                    kind: "review",
                    checkpointId: action.checkpoint_id!,
                    subjectDigest: action.subject_digest!,
                    runId: runId!,
                  },
                  (id) =>
                    client.decide({
                      checkpointId: action.checkpoint_id!,
                      subjectDigest: action.subject_digest!,
                      decision,
                      reason: text,
                      requestId: id,
                    }),
                );
              },
            }}
            response={{
              value: responses[interaction.checkpoint_id],
              onChange: (value) =>
                setResponses((r) => ({
                  ...r,
                  [interaction.checkpoint_id]: value,
                })),
              busy,
              readOnly: blocked,
              onSubmit: (action, value) => {
                if (
                  !permitted(action, "respond") ||
                  action.checkpoint_id !== interaction.checkpoint_id ||
                  action.subject_digest !== interaction.subject_digest
                )
                  return;
                void mutate(
                  {
                    kind: "response",
                    checkpointId: action.checkpoint_id!,
                    subjectDigest: action.subject_digest!,
                    runId: runId!,
                  },
                  (id) =>
                    client.respond({
                      checkpointId: action.checkpoint_id!,
                      subjectDigest: action.subject_digest!,
                      value,
                      requestId: id,
                    }),
                );
              },
            }}
            execution={{
              busy,
              readOnly: blocked,
              onSubmit: (action) => {
                if (
                  !permitted(action, "action") ||
                  action.checkpoint_id !== interaction.checkpoint_id ||
                  action.subject_digest !== interaction.subject_digest
                )
                  return;
                void mutate(
                  {
                    kind: "action",
                    checkpointId: action.checkpoint_id!,
                    subjectDigest: action.subject_digest!,
                    runId: runId!,
                  },
                  (id) =>
                    client.requestAction({
                      actionId: action.action_id,
                      subjectDigest: action.subject_digest!,
                      requestId: id,
                    }),
                );
              },
            }}
          />
        ))}
        {(snapshot.actions ?? [])
          .filter((a) => a.operation === "cancel")
          .map((action) => (
            <ActionButton
              key={action.action_id}
              action={action}
              busy={busy}
              readOnly={blocked}
              onNavigate={onNavigate}
              onAction={(selected) => {
                if (!permitted(selected, "cancel") || !runId) return;
                void mutate({ kind: "cancel", runId }, (id) =>
                  client.cancel(runId, id),
                );
              }}
            />
          ))}
      </Section>
    </>
  );
}

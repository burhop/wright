import { useCallback, useEffect, useRef, useState } from "react";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import type { WorkflowEditorDraftSnapshot } from "../workflow-recovery/WorkflowRecoveryConcept";
import type {
  EditorDraftMetadata,
  EditorDraftRecord,
  NativeEditorDraftClient,
} from "./native-editor-draft-client";

/** Short coalesced autosaves, one in flight, never retry an unconfirmed write. */
export function useNativeEditorDrafts(
  client: NativeEditorDraftClient | undefined,
  initial: WorkspaceWorkflowSourceDocument,
  onRestoreBase?: (document: WorkspaceWorkflowSourceDocument) => void,
) {
  const accepted = useRef(initial);
  const [acceptedDigest, setAcceptedDigest] = useState(initial.storage_digest);
  const wanted = useRef<
    | { snapshot: WorkflowEditorDraftSnapshot; dirty: boolean; key: string }
    | undefined
  >(undefined);
  const acknowledged = useRef("");
  const attempted = useRef("");
  const inFlight = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const alive = useRef(true);
  const [rows, setRows] = useState<EditorDraftMetadata[]>([]);
  const [message, setMessage] = useState(
    client ? "Checking saved drafts…" : "",
  );
  const [restored, setRestored] = useState<EditorDraftRecord>();
  const [inspected, setInspected] = useState<EditorDraftRecord>();
  const [generation, setGeneration] = useState(0);
  const flush = useCallback(
    async function flushLatest(): Promise<void> {
      if (
        !client ||
        !alive.current ||
        inFlight.current ||
        client.requiresRead ||
        !wanted.current ||
        acknowledged.current === wanted.current.key
      )
        return;
      const next = wanted.current;
      attempted.current = next.key;
      inFlight.current = true;
      setMessage("Preserving editor draft…");
      try {
        const saved = await client.save(
          next.snapshot,
          accepted.current,
          next.dirty,
        );
        acknowledged.current = next.key;
        if (alive.current && saved)
          setRows((current) => [
            ...current.filter((row) => row.draft_id !== saved.draft_id),
            ...(!saved.matches_accepted && !saved.accepted_checkpoint
              ? [saved]
              : []),
          ]);
        if (alive.current)
          setMessage(
            next.dirty
              ? "Draft preserved in Wright. Save to accept your workflow."
              : "Workflow saved; no unsaved draft changes.",
          );
      } catch (error) {
        if (alive.current)
          setMessage(
            error instanceof Error
              ? error.message
              : "Draft save is unconfirmed. Inspect saved state.",
          );
      } finally {
        inFlight.current = false;
      }
      if (
        alive.current &&
        !client.requiresRead &&
        wanted.current?.key !== next.key
      )
        await flushLatest();
    },
    [client],
  );
  const change = useCallback(
    (snapshot: WorkflowEditorDraftSnapshot, dirty: boolean) => {
      if (!client) return;
      const key = JSON.stringify([
        snapshot,
        dirty,
        accepted.current.storage_digest,
      ]);
      if (wanted.current?.key === key) return;
      wanted.current = { snapshot, dirty, key };
      if (timer.current) clearTimeout(timer.current);
      setMessage(
        client.requiresRead
          ? "Draft save needs inspection; your open edits are preserved."
          : dirty
            ? "Unsaved draft — preserving shortly…"
            : "Workflow saved.",
      );
      timer.current = setTimeout(() => void flush(), 500);
    },
    [client, flush],
  );
  const discover = useCallback(async () => {
    if (!client) return;
    const saved = await client.list();
    if (alive.current)
      setRows(
        saved.filter(
          (row) => !row.matches_accepted && !row.accepted_checkpoint,
        ),
      );
  }, [client]);
  useEffect(() => {
    alive.current = true;
    if (client)
      void discover()
        .then(() => {
          if (alive.current && !wanted.current)
            setMessage("Saved drafts checked.");
        })
        .catch(() => {
          if (alive.current)
            setMessage(
              "Saved drafts could not be read. Your accepted workflow is unchanged.",
            );
        });
    return () => {
      alive.current = false;
      if (timer.current) clearTimeout(timer.current);
    };
  }, [client, discover]);
  const inspect = async (id: string) => {
    if (!client || inFlight.current) return;
    try {
      setInspected(await client.read(id));
    } catch {
      setMessage(
        "This draft could not be read. Your open edits are unchanged.",
      );
    }
  };
  const resume = async (id: string, dirty: boolean) => {
    if (!client || inFlight.current || dirty || client.requiresRead) return;
    try {
      const saved = await client.read(id);
      client.resume(saved, accepted.current);
      onRestoreBase?.(accepted.current);
      setRestored(saved);
      setGeneration((value) => value + 1);
      setMessage("Draft reopened. Check and save it to accept the workflow.");
      setInspected(undefined);
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Draft cannot be resumed.",
      );
    }
  };
  return {
    rows,
    message,
    restored,
    inspected,
    generation,
    change,
    inspect,
    resume,
    acceptedDigest,
    accepted: (document: WorkspaceWorkflowSourceDocument) => {
      accepted.current = document;
      setAcceptedDigest(document.storage_digest);
      setRestored(undefined);
    },
    refresh: async () => {
      if (!client || inFlight.current) return;
      try {
        const reconciled = await client.inspectPending();
        if (reconciled) acknowledged.current = attempted.current;
        await discover();
        setMessage(
          reconciled
            ? "The previous draft save was found. No write was repeated."
            : "Saved drafts read. Your open edits are unchanged.",
        );
        if (reconciled) void flush();
      } catch {
        setMessage("Draft outcome remains unconfirmed. No write was repeated.");
      }
    },
    separate: () => {
      try {
        client?.startSeparateDraft();
        setMessage("A separate draft will preserve your current edits.");
        void flush();
      } catch {
        setMessage("Read the unconfirmed draft before starting another.");
      }
    },
  };
}

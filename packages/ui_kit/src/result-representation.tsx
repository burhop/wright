import { useEffect, useState } from "react";
import type {
  ArtifactRef,
  InteractionSnapshot,
  ProcessClient,
} from "@wright/process-client";
import { RepresentationDownload, RepresentationViewer } from "./representations";

/** A result reader, not a process observer or executor. The host supplies state;
 * the scoped client/file owner retains authority for every exact read.
 */
export function ResultRepresentation({
  client,
  snapshot,
  reference,
  onClose,
}: {
  client: Pick<ProcessClient, "getRepresentation">;
  snapshot: InteractionSnapshot;
  reference?: ArtifactRef | null;
  onClose?: () => void;
}) {
  const runId = snapshot.context.run_id ?? undefined;
  const member = !!reference && (snapshot.outputs ?? []).some((output) =>
    (output.representations ?? []).some((item) =>
      item.result_id === reference.result_id &&
      item.artifact_ref === reference.artifact_ref &&
      item.sha256 === reference.sha256 &&
      item.representation_id === reference.representation_id,
    ),
  );
  const key = JSON.stringify([
    snapshot.context.process, runId, reference ?? null, member,
  ]);
  const [state, setState] = useState<{
    key: string;
    blob?: Blob;
    failed?: boolean;
  }>();

  useEffect(() => {
    if (!reference || !runId || !member) return;
    const control = new AbortController();
    let active = true;
    setState({ key });
    void client.getRepresentation(reference, { runId, signal: control.signal })
      .then((blob) => {
        if (active) setState({ key, blob });
      })
      .catch(() => {
        if (active) setState({ key, failed: true });
      });
    return () => {
      active = false;
      control.abort();
    };
  }, [client, key]);

  if (!reference) return null;
  const current = state?.key === key ? state : undefined;
  return (
    <div className="wp-result-representation">
      {onClose && (
        <button type="button" className="wp-link" onClick={onClose}>
          Close representation
        </button>
      )}
      {!member || !runId ? (
        <p role="status">
          This representation is not part of the current recorded run. Refresh
          its results and select the exact output.
        </p>
      ) : current?.failed ? (
        <p role="alert">
          Wright could not open this recorded representation. Refresh the common
          working view and inspect the exact result.
        </p>
      ) : current?.blob ? (
        <>
          <RepresentationViewer
            blob={current.blob}
            title={reference.artifact_ref}
            sourceSha256={reference.sha256}
            readToolpaths={(signal) => client.getRepresentation(reference, {
              runId, preview: "toolpaths", signal,
            })}
          />
          <RepresentationDownload blob={current.blob} name={reference.artifact_ref} />
        </>
      ) : (
        <p role="status">Opening the exact result representation…</p>
      )}
    </div>
  );
}

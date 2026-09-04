import { useEffect, useRef, useState } from "react";
import {
  fetchNativeArtifact,
  type NativeArtifact,
} from "../../services/native-process";
import { nativeErrorText } from "./useNativeRun";
export function NativeArtifactCard({
  sessionId,
  runId,
  artifact,
  runState,
}: {
  sessionId: string;
  runId: string;
  artifact: NativeArtifact;
  runState: string;
}) {
  const [loaded, setLoaded] = useState<{
    url: string;
    preview: string | null;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => request.current?.abort(), []);
  useEffect(
    () => () => {
      if (loaded) URL.revokeObjectURL(loaded.url);
    },
    [loaded],
  );
  async function inspect() {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setError("");
    try {
      const blob = await fetchNativeArtifact(
        sessionId,
        runId,
        artifact,
        controller.signal,
      );
      if (controller.signal.aborted) return;
      let preview: string | null = null;
      if (
        artifact.media_type.startsWith("text/") ||
        ["application/json", "application/csv"].includes(artifact.media_type)
      ) {
        try {
          preview = new TextDecoder("utf-8", { fatal: true }).decode(
            await blob.slice(0, 65536).arrayBuffer(),
          );
          if (blob.size > 65536)
            preview +=
              "\n[Preview limited to 64 KiB; the download contains all verified bytes.]";
        } catch {
          preview = null;
        }
      }
      if (!controller.signal.aborted)
        setLoaded({ url: URL.createObjectURL(blob), preview });
    } catch (failure) {
      if (!controller.signal.aborted) setError(nativeErrorText(failure));
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  return (
    <article
      className="native-artifact"
      data-testid={`native-artifact-${artifact.artifact_id}`}
    >
      <h3>{artifact.filename}</h3>
      <p>
        {artifact.size} bytes · {artifact.media_type} · overall run {runState}
      </p>
      <p>
        Producer step <code>{artifact.step_id}</code>, output port{" "}
        <code>{artifact.port_id}</code>
      </p>
      <p>
        Recorded content SHA-256: <code>{artifact.content_digest}</code>
      </p>
      {error && <p role="alert">{error}</p>}
      <button
        disabled={busy}
        data-testid={`native-inspect-artifact-${artifact.artifact_id}`}
        onClick={() => void inspect()}
      >
        {busy
          ? "Verifying artifact…"
          : loaded
            ? "Verify artifact again"
            : "Inspect and verify actual artifact"}
      </button>
      {loaded && (
        <div>
          <p role="status">
            Actual artifact bytes verified against the run index and service
            digest.
          </p>
          <a
            data-testid={`native-download-${artifact.artifact_id}`}
            href={loaded.url}
            download={artifact.filename.replace(/[\\/:*?"<>|]/g, "_")}
          >
            Download verified artifact
          </a>
          {loaded.preview !== null ? (
            <label>
              Actual content preview
              <textarea
                data-testid={`native-artifact-content-${artifact.artifact_id}`}
                readOnly
                rows={8}
                value={loaded.preview}
              />
            </label>
          ) : (
            <p>
              A text preview is unavailable for these bytes. Use the verified
              download.
            </p>
          )}
        </div>
      )}
      <details>
        <summary data-testid={`native-provenance-${artifact.artifact_id}`}>
          Recorded provenance
        </summary>
        <pre>{JSON.stringify(artifact.provenance, null, 2)}</pre>
      </details>
    </article>
  );
}

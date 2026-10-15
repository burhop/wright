import { useEffect, useState } from "react";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";

/** Plain text only; file content never becomes HTML or an execution request. */
export function NativeFilePreview({
  call,
  workspace,
  path,
  onClose,
}: {
  call: HomeCall;
  workspace: DesktopWorkspace;
  path: string;
  onClose: () => void;
}) {
  const [preview, setPreview] = useState<{
    content?: string;
    reason?: string;
    digest?: string;
  }>();
  useEffect(() => {
    let active = true;
    void call("wright_workspace_file_preview", {
      workspace_id: workspace.workspace_id,
      session_id: workspace.session_id,
      path,
    })
      .then((result) => {
        if (!active) return;
        if (result.isError) throw new Error("Read failed");
        const text = result.content.find((item) => item.type === "text");
        const data =
          result.structuredContent ??
          (text?.type === "text" ? JSON.parse(text.text) : undefined);
        if (
          !data ||
          data.workspace_id !== workspace.workspace_id ||
          data.session_id !== workspace.session_id ||
          data.path !== path
        )
          throw new Error("Read scope differs");
        if (data.supported === false && typeof data.reason === "string") {
          setPreview({ reason: data.reason });
        } else if (
          data.supported === true &&
          typeof data.content === "string" &&
          new TextEncoder().encode(data.content).length <= 65536 &&
          /^[a-f0-9]{64}$/.test(data.sha256)
        ) {
          setPreview({ content: data.content, digest: data.sha256 });
        } else throw new Error("Unsupported read response");
      })
      .catch(() => {
        if (active)
          setPreview({
            reason: "Preview could not be read. Close and reopen to retry.",
          });
      });
    return () => {
      active = false;
    };
  }, [call, workspace.workspace_id, workspace.session_id, path]);
  return (
    <section aria-label="File preview">
      <h3>{path}</h3>
      <button type="button" onClick={onClose}>
        Close preview
      </button>
      {!preview && <p role="status">Reading file…</p>}
      {preview?.reason && <p role="status">{preview.reason}</p>}
      {preview?.content !== undefined && (
        <>
          <p>Read-only text preview · current saved file</p>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
              maxHeight: "50vh",
              overflow: "auto",
            }}
          >
            {preview.content}
          </pre>
          <details>
            <summary>File identity</summary>
            <code>{preview.digest}</code>
          </details>
        </>
      )}
    </section>
  );
}

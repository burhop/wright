import { useEffect, useRef, useState } from "react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";
import { encodeFile } from "./native-process-client";

interface Upload {
  filename: string;
  content_base64: string;
  sha256: string;
  bytes: number;
  path: string;
}
function document(result: CallToolResult) {
  if (result.isError) throw Error("Unconfirmed operation");
  const text = result.content.find((item) => item.type === "text");
  return (
    result.structuredContent ??
    (text?.type === "text" ? JSON.parse(text.text) : null)
  );
}

/** Stage input bytes only. Reconciliation reads the same known subject, never retries a write. */
export function NativeFileUpload({
  call,
  workspace,
  onUploaded,
}: {
  call: HomeCall;
  workspace: DesktopWorkspace;
  onUploaded: (path: string) => void;
}) {
  const alive = useRef(true);
  const flight = useRef(false);
  const [file, setFile] = useState<File>();
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState<Upload>();
  const [message, setMessage] = useState("");
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  const scope = {
    workspace_id: workspace.workspace_id,
    session_id: workspace.session_id,
  };
  function matches(data: Record<string, unknown> | null, upload: Upload) {
    return (
      data?.workspace_id === workspace.workspace_id &&
      data.session_id === workspace.session_id &&
      data.path === upload.path &&
      data.filename === upload.filename &&
      data.sha256 === upload.sha256 &&
      data.bytes === upload.bytes
    );
  }
  function saved(upload: Upload) {
    setUncertain(undefined);
    setMessage(
      `Saved ${upload.filename} in uploads. Existing files are unchanged.`,
    );
    onUploaded(upload.path);
  }
  async function upload() {
    if (!file || flight.current || uncertain) return;
    flight.current = true;
    setBusy(true);
    setMessage("");
    let pending: Upload | undefined;
    let sent = false;
    try {
      if (!file.size || file.size > 16 * 1024 * 1024) {
        setMessage("Choose a nonempty file up to 16 MiB.");
        return;
      }
      const encoded = await encodeFile(file);
      const bytes = Uint8Array.from(atob(encoded), (char) =>
        char.charCodeAt(0),
      );
      const sha256 = Array.from(
        new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
        (v) => v.toString(16).padStart(2, "0"),
      ).join("");
      if (!alive.current) return;
      pending = {
        filename: file.name,
        content_base64: encoded,
        sha256,
        bytes: bytes.length,
        path: `uploads/${sha256}/${file.name}`,
      };
      sent = true;
      const data = document(
        await call("wright_workspace_file_upload", {
          request: {
            ...scope,
            filename: pending.filename,
            content_base64: encoded,
            sha256,
          },
        }),
      );
      if (!alive.current) return;
      if (data?.ok === false && data.error?.outcome_known === true) {
        setMessage(
          "Upload was rejected. Check workspace access, file size and filename.",
        );
        return;
      }
      if (data?.ok !== true || !matches(data.document, pending))
        throw Error("Identity unconfirmed");
      saved(pending);
    } catch {
      if (alive.current) {
        if (sent && pending) {
          setUncertain(pending);
          setMessage(
            "Upload outcome is unconfirmed. Check saved upload before another attempt; no write was repeated.",
          );
        } else setMessage("This file could not be read. No upload was sent.");
      }
    } finally {
      flight.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function reconcile() {
    if (!uncertain || flight.current) return;
    flight.current = true;
    setBusy(true);
    try {
      const data = document(
        await call("wright_workspace_file_download", {
          ...scope,
          path: uncertain.path,
        }),
      );
      if (!alive.current) return;
      if (
        !matches(data, uncertain) ||
        data.supported !== true ||
        data.content_base64 !== uncertain.content_base64
      )
        throw Error("Saved bytes unconfirmed");
      saved(uncertain);
    } catch {
      if (alive.current)
        setMessage(
          "The saved upload is not confirmed. Inspect Files and workspace access before another attempt; no write was repeated.",
        );
    } finally {
      flight.current = false;
      if (alive.current) setBusy(false);
    }
  }
  return (
    <section aria-label="Upload input file">
      <label>
        Choose input file{" "}
        <input
          type="file"
          disabled={busy || !!uncertain}
          onChange={(event) => {
            setFile(event.target.files?.[0]);
            setMessage("");
          }}
        />
      </label>
      <button
        type="button"
        disabled={!file || busy || !!uncertain}
        onClick={() => void upload()}
      >
        {busy ? "Working…" : "Upload file"}
      </button>
      {uncertain && (
        <button type="button" disabled={busy} onClick={() => void reconcile()}>
          Check saved upload
        </button>
      )}
      <p>
        Stage files up to 16 MiB in uploads without replacing existing files.
        Uploading does not run or approve a workflow.
      </p>
      {message && <p role="status">{message}</p>}
    </section>
  );
}

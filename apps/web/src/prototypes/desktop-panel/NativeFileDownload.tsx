import { useEffect, useRef, useState } from "react";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";
import { useFileDownload, fileDownloadMessage } from "@wright/ui-kit";

/** Retrieve current bytes; optional recorder provenance must match before delivery. */
export function NativeFileDownload({
  call,
  workspace,
  path,
  recordedEvidence,
}: {
  call: HomeCall;
  workspace: DesktopWorkspace;
  path: string;
  recordedEvidence?: { runId: string; sha256: string };
}) {
  const alive = useRef(true);
  const pending = useRef(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const requestDownload = useFileDownload();
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  async function download() {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setMessage("");
    try {
      if (!requestDownload) {
        setMessage(fileDownloadMessage("unavailable"));
        return;
      }
      const result = await call("wright_workspace_file_download", {
        workspace_id: workspace.workspace_id,
        session_id: workspace.session_id,
        path,
      });
      if (!alive.current) return;
      if (result.isError) throw new Error("Read failed");
      const text = result.content.find((item) => item.type === "text");
      const data =
        result.structuredContent ??
        (text?.type === "text" ? JSON.parse(text.text) : null);
      if (
        !data ||
        data.workspace_id !== workspace.workspace_id ||
        data.session_id !== workspace.session_id ||
        data.path !== path
      )
        throw new Error("Scope differs");
      if (data.supported === false) {
        setMessage(
          "Download unavailable. Choose a visible workspace file up to 16 MiB.",
        );
        return;
      }
      if (
        recordedEvidence &&
        (!recordedEvidence.runId ||
          !/^[a-f0-9]{64}$/.test(recordedEvidence.sha256) ||
          data.sha256 !== recordedEvidence.sha256)
      ) {
        setMessage(
          "The saved file no longer matches this run’s recorded evidence. No download was requested.",
        );
        return;
      }
      const name = path.replaceAll("\\", "/").split("/").at(-1);
      if (
        data.supported !== true ||
        !name ||
        data.filename !== name ||
        Array.from(name).some(
          (char) => char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127,
        ) ||
        name.startsWith(".") ||
        typeof data.content_base64 !== "string" ||
        data.content_base64.length > 22369624 ||
        !Number.isInteger(data.bytes) ||
        data.bytes < 0 ||
        data.bytes > 16 * 1024 * 1024 ||
        typeof data.sha256 !== "string" ||
        !/^[a-f0-9]{64}$/.test(data.sha256)
      )
        throw new Error("Invalid file response");
      const raw = atob(data.content_base64);
      const bytes = Uint8Array.from(raw, (char) => char.charCodeAt(0));
      if (bytes.byteLength !== data.bytes) throw new Error("Size differs");
      const hash = Array.from(
        new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
        (value) => value.toString(16).padStart(2, "0"),
      ).join("");
      if (!alive.current) return;
      if (hash !== data.sha256) throw new Error("Digest differs");
      const delivery = await requestDownload(
        new Blob([bytes], { type: "application/octet-stream" }),
        name,
      );
      if (alive.current)
        setMessage(
          fileDownloadMessage(delivery) +
            (delivery === "requested"
              ? recordedEvidence
                ? " Bytes match this saved run."
                : " This is the current saved file, not verified run evidence."
              : ""),
        );
    } catch {
      if (alive.current)
        setMessage(
          "Download could not be verified. No file delivery is confirmed.",
        );
    } finally {
      pending.current = false;
      if (alive.current) setBusy(false);
    }
  }
  return (
    <div>
      <button type="button" disabled={busy} onClick={() => void download()}>
        {busy ? "Preparing download…" : "Download file"}
      </button>
      {message && <p role="status">{message}</p>}
    </div>
  );
}

import { useCallback, useEffect, useState } from "react";
import type { RecoveryBlock } from "./model";
import type { RecoveryCommand } from "./command-system";
import type { AuthoringWorkspaceFile } from "./AuthoringControls";
import { workspaceContentUrl } from "../../services/viewer-panel/providers/workspace-content-url";

export function InputBlockEditor({ block, sessionId, readOnly, onApply, onListFiles, isImage = false }: {
  isImage?: boolean; block: RecoveryBlock; sessionId?: string; readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
  onListFiles?: () => Promise<AuthoringWorkspaceFile[]>;
}) {
  const [files, setFiles] = useState<AuthoringWorkspaceFile[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const image = isImage || block.configuration.authoring_template === "image-input";
  const fileInput = image || block.configuration.input_mode === "workspace-file";
  const path = String(block.configuration.workspace_file ?? "");
  const update = (key: string, value: string) => onApply([{kind: "set_block_configuration", blockId: block.id, key, value}]);
  const load = useCallback(async () => {
    if (!onListFiles) return;
    try { setFiles(await onListFiles()); setMessage(""); }
    catch { setMessage("Could not list workspace files. Try refreshing the list."); }
  }, [onListFiles]);
  useEffect(() => { if (fileInput) void load(); }, [fileInput, load]);
  const choices = files.filter(file => !image || /\.(png|jpe?g|gif|webp)$/i.test(file.path));
  const upload = async (file: File) => {
    if (!sessionId || readOnly) return;
    setBusy(true); setMessage("");
    try {
      if (file.size > 4 * 1024 * 1024) throw new Error("Choose an image smaller than 4 MiB.");
      const body = new FormData(); body.append("file", file);
      const response = await fetch(`/api/workspace/workflow-sources/images?session_id=${encodeURIComponent(sessionId)}`, {method: "POST", body});
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "The image could not be uploaded.");
      await load(); update("workspace_file", result.path);
    } catch (error) { setMessage(error instanceof Error ? error.message : "The image could not be uploaded."); }
    finally { setBusy(false); }
  };
  return <section className="recovery-prompt-editor" data-testid="workflow-recovery-input-editor">
    {fileInput ? <>
      <label>{image ? "Image" : "Workspace file"}<select data-testid="workflow-recovery-input-select" disabled={readOnly || busy} value={path} onChange={e => update("workspace_file", e.target.value)}>
        <option value="">{image ? "Choose an image" : "Choose a file"}</option>
        {path && !choices.some(file => file.path === path) && <option value={path}>{path} · not in current list</option>}
        {choices.map(file => <option key={file.path} value={file.path}>{file.path}</option>)}
      </select></label>
      {image && <label className="recovery-button recovery-button--secondary">{busy ? "Uploading…" : "Upload image"}<input type="file" accept="image/png,image/jpeg,image/gif,image/webp" disabled={readOnly || busy || !sessionId} data-testid="workflow-recovery-input-upload" onChange={e => { const file = e.target.files?.[0]; if (file) void upload(file); e.target.value = ""; }} /></label>}
      {image && path && sessionId && <img src={workspaceContentUrl(path, sessionId)} alt={`Selected image: ${path}`} style={{maxWidth: "100%", maxHeight: 200, objectFit: "contain"}} />}
      <button type="button" className="recovery-button recovery-button--quiet" onClick={() => void load()} disabled={busy}>Refresh files</button>
      {!image && <details><summary>Enter a relative path</summary><label>File path<input data-testid={`workflow-recovery-input-file-${block.id}`} value={path} disabled={readOnly} onChange={e => update("workspace_file", e.target.value)} /></label><small>A filename without a folder is in the workspace root.</small></details>}
    </> : <label>Text<textarea rows={9} data-testid={`workflow-recovery-input-text-${block.id}`} value={String(block.configuration.input_text ?? "")} readOnly={readOnly} onChange={e => update("input_text", e.target.value)} /></label>}
    {message && <p role="alert">{message}</p>}
  </section>;
}

import { useEffect, useRef } from "react";
import { NativeConnections, type ConnectionsCall } from "./NativeConnections";
import type { DesktopWorkspace } from "./NativeHomePanel";

export function NativeEditorConnections({
  workspace,
  call,
  openLink,
  onClose,
}: {
  workspace: DesktopWorkspace;
  call: ConnectionsCall;
  openLink?: (url: string) => Promise<void>;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  return (
    <dialog
      ref={dialog}
      className="native-editor-connections"
      aria-label="Workspace connections"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
    >
      <header>
        <strong>{workspace.workspace_name} · Connections</strong>
        <button type="button" onClick={onClose}>
          Back to workflow
        </button>
      </header>
      <div className="native-home">
        <NativeConnections
          workspace={workspace}
          call={call}
          openLink={openLink}
        />
      </div>
    </dialog>
  );
}

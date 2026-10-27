import { useRef, useState } from "react";
import { blankWorkflowSource } from "../../services/blank-workflow";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";

/** Creates source only. Readiness, execution and review remain separate. */
export function NativeNewWorkflow({
  workspace,
  call,
  onOpen,
  onBusy,
  disabled,
  resetAfterOpen = false,
}: {
  readonly workspace: DesktopWorkspace;
  readonly call: HomeCall;
  readonly onOpen: (workspace: DesktopWorkspace, path: string) => Promise<void>;
  readonly onBusy: (busy: boolean) => void;
  readonly disabled: boolean;
  readonly resetAfterOpen?: boolean;
}) {
  const [visible, setVisible] = useState(false);
  const [title, setTitle] = useState("");
  const [notice, setNotice] = useState("");
  const [savedPath, setSavedPath] = useState<string>();
  const [uncertain, setUncertain] = useState(false);
  const flight = useRef(false);
  const openSaved = async (path: string) => {
    try {
      await onOpen(workspace, path);
      if (resetAfterOpen) {
        setVisible(false);
        setTitle("");
        setSavedPath(undefined);
        setNotice("");
      }
    } catch {
      setNotice(
        "Your workflow was saved. Opening the editor failed; try Open saved workflow.",
      );
    }
  };
  const create = async () => {
    if (flight.current || disabled || uncertain || savedPath || !title.trim())
      return;
    flight.current = true;
    onBusy(true);
    const path = `workflows/untitled-workflow-${crypto.randomUUID()}.workflow.wflow`;
    const source = blankWorkflowSource(title.trim());
    setNotice("");
    try {
      const result = await call("wright_workflow_create", {
        workspace_id: workspace.workspace_id,
        session_id: workspace.session_id,
        path,
        source,
      });
      if (result.isError) throw new Error("Creation not confirmed");
      const text = result.content.find((item) => item.type === "text");
      const receipt =
        result.structuredContent ??
        (text?.type === "text" ? JSON.parse(text.text) : undefined);
      if (
        receipt?.workspace_id !== workspace.workspace_id ||
        receipt.path !== path ||
        typeof receipt.source !== "string" ||
        typeof receipt.storage_digest !== "string" ||
        !/^[a-f0-9]{64}$/.test(receipt.storage_digest)
      )
        throw new Error("Creation identity not confirmed");
      // The source owner materializes versioned instruction defaults on creation.
      // Its saved source/digest is authoritative; it need not equal the blank input.
      setSavedPath(path);
      await openSaved(path);
    } catch {
      setUncertain(true);
      setNotice(
        `Creation was not confirmed. Refresh and check ${path} before creating another workflow. This form will not repeat the request.`,
      );
    } finally {
      flight.current = false;
      onBusy(false);
    }
  };
  return (
    <div className="native-new-workflow">
      <button
        disabled={disabled || uncertain || !!savedPath}
        onClick={() => setVisible((value) => !value)}
      >
        New workflow
      </button>
      {visible && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void create();
          }}
        >
          <label htmlFor="wright-workflow-title">Workflow name</label>
          <input
            id="wright-workflow-title"
            value={title}
            required
            disabled={disabled || uncertain || !!savedPath}
            onChange={(event) => setTitle(event.target.value)}
          />
          <button
            type="submit"
            disabled={disabled || uncertain || !!savedPath || !title.trim()}
          >
            Create workflow
          </button>
        </form>
      )}
      {notice && <p role="alert">{notice}</p>}
      {savedPath && (
        <button
          disabled={disabled}
          onClick={async () => {
            if (flight.current) return;
            flight.current = true;
            onBusy(true);
            try {
              await openSaved(savedPath);
            } finally {
              flight.current = false;
              onBusy(false);
            }
          }}
        >
          Open saved workflow
        </button>
      )}
    </div>
  );
}

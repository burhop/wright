import { NativeActionForm } from "./NativeActionForm";
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
  onPlanInChat,
}: {
  readonly workspace: DesktopWorkspace;
  readonly call: HomeCall;
  readonly onOpen: (workspace: DesktopWorkspace, path: string) => Promise<void>;
  readonly onBusy: (busy: boolean) => void;
  readonly disabled: boolean;
  readonly resetAfterOpen?: boolean;
  readonly onPlanInChat?: (
    workspace: DesktopWorkspace,
  ) => Promise<"sent" | "unsupported">;
}) {
  const [visible, setVisible] = useState(false);
  const [title, setTitle] = useState("");
  const [notice, setNotice] = useState("");
  const [savedPath, setSavedPath] = useState<string>();
  const [uncertain, setUncertain] = useState(false);
  const flight = useRef(false);
  const [handoff, setHandoff] = useState<
    "idle" | "pending" | "sent" | "unsupported" | "uncertain"
  >("idle");
  const handoffFlight = useRef(false);
  const planInChat = async () => {
    if (
      !onPlanInChat ||
      disabled ||
      handoffFlight.current ||
      handoff !== "idle"
    )
      return;
    handoffFlight.current = true;
    setHandoff("pending");
    onBusy(true);
    try {
      setHandoff(await onPlanInChat(workspace));
    } catch {
      setHandoff("uncertain");
    } finally {
      handoffFlight.current = false;
      onBusy(false);
    }
  };
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
        <NativeActionForm
          onAction={() => {
            void create();
          }}
        >
          <p>
            Describe the job for <strong>{workspace.workspace_name}</strong> in
            Codex chat. Attach new references there, or name existing workspace
            files to include as workflow inputs.
          </p>
          {onPlanInChat && (
            <button
              type="button"
              disabled={disabled || handoff !== "idle"}
              onClick={() => void planInChat()}
            >
              {handoff === "pending"
                ? "Sending to Codex chat…"
                : handoff === "sent"
                  ? "Sent to Codex chat"
                  : "Plan in Codex chat"}
            </button>
          )}
          {handoff === "sent" && (
            <p role="status">
              Workspace context sent. Continue in the Codex chat beside this
              panel. After chat confirms saving your workflow, return here,
              choose Refresh, and open it from Workspace files.
            </p>
          )}
          {handoff === "unsupported" && (
            <p role="status">
              This host cannot send the request to chat. In this conversation,
              ask to create a workflow in {workspace.workspace_name}.
            </p>
          )}
          {handoff === "uncertain" && (
            <p role="alert">
              Delivery was not confirmed. Check the conversation before sending
              another request. Nothing was run.
            </p>
          )}
          <details open={!onPlanInChat}>
            <summary>Start with a blank workflow</summary>
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
          </details>
        </NativeActionForm>
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

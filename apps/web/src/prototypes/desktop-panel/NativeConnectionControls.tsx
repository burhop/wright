import { useEffect, useRef, useState } from "react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { DesktopWorkspace } from "./NativeHomePanel";
import type { ConnectionsCall } from "./NativeConnections";

export interface ControlState {
  capability_id: string;
  server_id: string;
  shared_scope: "wright-host";
  control_digest: string;
  installed: boolean;
  active: boolean;
  status: string;
  installed_version: string | null;
  bound_workspace_id: string | null;
  tools: {
    tool_id: string;
    name: string;
    enabled: boolean;
    reported_read_only: boolean;
  }[];
}
type Operation = "start" | "stop" | "uninstall" | "tool-enable" | "tool-disable";
function payload(result: CallToolResult) {
  if (result.isError) throw Error("Unconfirmed control response");
  const text = result.content.find((item) => item.type === "text");
  return (
    result.structuredContent ??
    (text?.type === "text" ? JSON.parse(text.text) : null)
  );
}

/** Existing registry/lifecycle controls; workspace availability and process reviews remain separate. */
export function NativeConnectionControls({
  call,
  workspace,
  capabilityId,
  serverId,
  onChanged,
}: {
  call: ConnectionsCall;
  workspace: DesktopWorkspace;
  capabilityId: string;
  serverId: string;
  onChanged: (state: ControlState) => void;
}) {
  const [state, setState] = useState<ControlState>();
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [message, setMessage] = useState("");
  const [uninstallSubject, setUninstallSubject] = useState<string>();
  const flight = useRef(false);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  const scope = {
    workspace_id: workspace.workspace_id,
    session_id: workspace.session_id,
    capability_id: capabilityId,
    server_id: serverId,
  };
  function checked(data: Record<string, unknown>): ControlState {
    const next = data?.state as ControlState | undefined;
    if (
      data?.workspace_id !== workspace.workspace_id ||
      data.session_id !== workspace.session_id ||
      next?.capability_id !== capabilityId ||
      next.server_id !== serverId ||
      next.shared_scope !== "wright-host" ||
      !/^[a-f0-9]{64}$/.test(next.control_digest) ||
      typeof next.active !== "boolean" ||
      typeof next.installed !== "boolean" ||
      typeof next.status !== "string" ||
      !(
        next.bound_workspace_id === null ||
        typeof next.bound_workspace_id === "string"
      ) ||
      !Array.isArray(next.tools) ||
      next.tools.some(
        (t) =>
          typeof t.tool_id !== "string" ||
          typeof t.name !== "string" ||
          typeof t.enabled !== "boolean",
      )
    ) {
      throw Error("Control subject not confirmed");
    }
    return next;
  }
  async function refresh() {
    if (flight.current) return;
    flight.current = true;
    setUninstallSubject(undefined);
    setBusy(true);
    try {
      const next = checked(
        payload(await call("wright_connection_controls", scope)),
      );
      if (!alive.current) return;
      setState(next);
      setUncertain(false);
      setMessage("Saved provider state refreshed.");
      onChanged(next);
    } catch {
      if (alive.current)
        setMessage(
          "Provider state could not be read. Refresh before another action.",
        );
    } finally {
      flight.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function change(operation: Operation, toolId?: string) {
    if (flight.current || uncertain || !state) return;
    if (operation === "uninstall" && uninstallSubject !== state.control_digest) return;
    setUninstallSubject(undefined);
    flight.current = true;
    setBusy(true);
    setMessage("");
    try {
      const result = payload(
        await call("wright_connection_control", {
          request: {
            ...scope,
            operation,
            shared_scope: "wright-host",
            control_digest: state.control_digest,
            ...(toolId ? { tool_id: toolId } : {}),
          },
        }),
      );
      if (!alive.current) return;
      if (result?.ok === false && result.error?.outcome_known === true) {
        setUncertain(true);
        setMessage(
          "Wright rejected this control. Refresh provider state and check operator access before another action.",
        );
        return;
      }
      if (
        result?.ok !== true ||
        result.document?.operation !== operation ||
        result.document?.tool_id !== (toolId ?? null)
      )
        throw Error("Operation not confirmed");
      const next = checked(result.document);
      const reached =
        operation === "start"
          ? next.active
          : operation === "stop"
            ? !next.active
            : operation === "uninstall"
              ? !next.active && !next.installed
            : next.tools.find((t) => t.tool_id === toolId)?.enabled ===
              (operation === "tool-enable");
      if (!reached) throw Error("Requested state not reached");
      setState(next);
      setMessage("Shared provider state updated.");
      onChanged(next);
    } catch {
      if (alive.current) {
        setUncertain(true);
        setMessage(
          "Control outcome is not confirmed. Refresh saved provider state before another action; no request was repeated.",
        );
      }
    } finally {
      flight.current = false;
      if (alive.current) setBusy(false);
    }
  }
  return (
    <details
      onToggle={(event) => {
        if (event.currentTarget.open) void refresh();
      }}
    >
      <summary>Provider controls</summary>
      <p>
        Provider processes and tool switches are shared across Wright workspaces
        on this host. Start uses the selected workspace.
      </p>
      <button disabled={busy} onClick={() => void refresh()}>
        Refresh provider state
      </button>
      {message && <p role="status">{message}</p>}
      {state && (
        <>
          <p>
            Process: {state.status}.{" "}
            {state.bound_workspace_id
              ? state.bound_workspace_id === workspace.workspace_id
                ? "Bound to this workspace."
                : "Bound to another workspace; stop explicitly before starting here."
              : "Workspace binding is not reported."}
          </p>
          <button
            disabled={busy || uncertain || !state.installed || state.active}
            onClick={() => void change("start")}
          >
            Start for this workspace
          </button>
          <button
            disabled={busy || uncertain || !state.installed || !state.active}
            onClick={() => void change("stop")}
          >
            Stop provider (shared)
          </button>
          <button
            disabled={busy || uncertain || !state.installed}
            onClick={() => setUninstallSubject(state.control_digest)}
          >
            Uninstall provider (shared)
          </button>
          {uninstallSubject && <section aria-label="Confirm provider uninstall">
            <p>This stops the provider for every Wright workspace and marks it uninstalled. Saved setup, credentials and downloaded packages are retained. Review setup again before using it.</p>
            <button disabled={busy || uncertain || uninstallSubject !== state.control_digest}
              onClick={() => void change("uninstall")}>Uninstall for all workspaces</button>
            <button disabled={busy} onClick={() => setUninstallSubject(undefined)}>Keep provider</button>
          </section>}
          <ul>
            {state.tools.map((tool) => (
              <li key={tool.tool_id}>
                <label>
                  <input
                    type="checkbox"
                    checked={tool.enabled}
                    disabled={busy || uncertain || !state.installed}
                    onChange={(event) =>
                      void change(
                        event.target.checked ? "tool-enable" : "tool-disable",
                        tool.tool_id,
                      )
                    }
                  />
                  {tool.name} — {tool.enabled ? "Enabled" : "Disabled"} on this
                  host
                </label>
              </li>
            ))}
          </ul>
          {!state.tools.length && (
            <p>
              No tool contracts are currently advertised. Start or validate the
              provider to discover them.
            </p>
          )}
        </>
      )}
    </details>
  );
}

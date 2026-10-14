import { useEffect, useState } from "react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { DesktopWorkspace } from "./NativeHomePanel";

export type ConnectionsCall = (
  name: "wright_connections_list" | "wright_connection_plan",
  args: Record<string, unknown>,
) => Promise<CallToolResult>;
interface Connection {
  capability_id: string;
  name: string;
  description: string;
  installed: boolean;
  active: boolean;
  enabled_here: boolean;
  credentials_missing: boolean;
  process_status: string;
  installed_version: string | null;
  compatibility: {
    status: string;
    reasons: { code: string; message: string; recovery: string }[];
  };
}
interface SetupPlan {
  plan_id: string;
  capability_id: string;
  workspace_id: string;
  requested_scope: string;
  state: string;
  requirements?: { license?: { reference: string | null } };
  approval_gates?: string[];
  blocking_reasons: { code: string; message: string; recovery: string }[];
  effects: { step_id: string; description: string }[];
}

export function NativeConnections({
  workspace,
  call,
}: {
  readonly workspace: DesktopWorkspace;
  readonly call: ConnectionsCall;
}) {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState<string | null>(null);
  const [next, setNext] = useState<string | null>(null);
  const [items, setItems] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [planning, setPlanning] = useState(false);
  const [plan, setPlan] = useState<SetupPlan>();
  const [planError, setPlanError] = useState(false);
  const [licenseCapability, setLicenseCapability] = useState<string | null>(
    null,
  );
  async function prepare(capabilityId: string) {
    setPlanning(true);
    setPlan(undefined);
    setPlanError(false);
    try {
      const result = await call("wright_connection_plan", {
        workspace_id: workspace.workspace_id,
        session_id: workspace.session_id,
        capability_id: capabilityId,
        independently_completed_license: licenseCapability === capabilityId,
      });
      const data = result.structuredContent;
      const candidate = data?.plan as SetupPlan | undefined;
      if (
        result.isError ||
        data?.workspace_id !== workspace.workspace_id ||
        data?.session_id !== workspace.session_id ||
        !candidate ||
        candidate.workspace_id !== workspace.workspace_id ||
        candidate.requested_scope !== "workspace" ||
        candidate.capability_id !== capabilityId
      )
        throw new Error("Unconfirmed plan");
      setPlan(candidate);
    } catch {
      setPlanError(true);
    } finally {
      setPlanning(false);
    }
  }
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(false);
    void call("wright_connections_list", {
      workspace_id: workspace.workspace_id,
      session_id: workspace.session_id,
      search: query,
      ...(cursor ? { cursor } : {}),
    })
      .then((result) => {
        const data = result.structuredContent;
        if (
          result.isError ||
          !data ||
          data.workspace_id !== workspace.workspace_id ||
          data.session_id !== workspace.session_id ||
          !Array.isArray(data.connections)
        )
          throw new Error("Unconfirmed connection scope");
        if (!active) return;
        setItems(data.connections as Connection[]);
        setNext(typeof data.next_cursor === "string" ? data.next_cursor : null);
      })
      .catch(() => {
        if (active) setError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [
    call,
    workspace.workspace_id,
    workspace.session_id,
    query,
    cursor,
    refresh,
  ]);
  return (
    <section aria-label="Connections">
      <h2>Connections</h2>
      <p>
        Engineering tools for {workspace.workspace_name}. Availability here does
        not approve workflow actions.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          setCursor(null);
          setQuery(search);
          setRefresh((value) => value + 1);
        }}
      >
        <label htmlFor="connection-search">Find an MCP</label>
        <input
          id="connection-search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <button type="submit" disabled={loading}>
          Search / refresh
        </button>
      </form>
      {loading ? (
        <p role="status">Loading connections…</p>
      ) : error ? (
        <p role="alert">
          Connections could not be read. Search / refresh to retry; no settings
          changed.
        </p>
      ) : (
        <>
          {!items.length && <p>No matching connections.</p>}
          <ul>
            {items.map((item) => (
              <li key={item.capability_id}>
                <strong>{item.name}</strong>
                <p>{item.description}</p>
                <p>
                  {!item.installed
                    ? "Setup needed"
                    : item.credentials_missing
                      ? "Sign-in or credentials needed"
                      : !item.active
                        ? "Inactive"
                        : !item.enabled_here
                          ? "Not enabled in this workspace"
                          : "Enabled in this workspace"}
                </p>
                <details>
                  <summary>Readiness details</summary>
                  <p>
                    Host compatibility: {item.compatibility.status}. Process:{" "}
                    {item.process_status}.
                  </p>
                  <p>
                    Installed version:{" "}
                    {item.installed_version ?? "Not reported"}.
                  </p>
                  {item.compatibility.reasons.map((reason) => (
                    <p key={reason.code}>
                      {reason.message} {reason.recovery}
                    </p>
                  ))}
                </details>
                <button
                  disabled={planning}
                  onClick={() => void prepare(item.capability_id)}
                >
                  Review setup for {item.name}
                </button>
              </li>
            ))}
          </ul>
          {next && (
            <button onClick={() => setCursor(next)}>Next connections</button>
          )}
          {cursor && (
            <button onClick={() => setCursor(null)}>First connections</button>
          )}
        </>
      )}
      {planning && <p role="status">Preparing setup plan…</p>}
      {planError && (
        <p role="alert">
          The setup plan was not confirmed. No installation or permission change
          was requested.
        </p>
      )}
      {plan && (
        <section aria-label="Setup plan">
          <h3>Review setup</h3>
          <p>
            Plan state: {plan.state}. Nothing has been installed or approved.
          </p>
          {plan.requirements?.license?.reference && (
            <p>{plan.requirements.license.reference}</p>
          )}
          {(plan.approval_gates ?? []).map((gate) => (
            <p key={gate}>
              Separate setup approval required: {gate.replaceAll("_", " ")}
            </p>
          ))}
          <label>
            <input
              type="checkbox"
              checked={licenseCapability === plan.capability_id}
              onChange={(event) =>
                setLicenseCapability(
                  event.target.checked ? plan.capability_id : null,
                )
              }
            />
            I have independently completed the publisher account and terms setup
            for this provider.
          </label>
          <p>
            This records existing completion only; it does not purchase a
            subscription or sign in. Review setup again to create a new plan.
          </p>
          {plan.effects.map((effect) => (
            <p key={effect.step_id}>{effect.description}</p>
          ))}
          {plan.blocking_reasons.map((reason) => (
            <p key={reason.code}>
              {reason.message} {reason.recovery}
            </p>
          ))}
        </section>
      )}
      <p>
        Installation, sign-in and permission changes are not yet available in
        this panel.
      </p>
    </section>
  );
}

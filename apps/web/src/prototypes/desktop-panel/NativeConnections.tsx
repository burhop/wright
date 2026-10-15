import { useEffect, useState } from "react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { DesktopWorkspace } from "./NativeHomePanel";
import { NativeSignin } from "./NativeSignin";

export type ConnectionsCall = (
  name:
    | "wright_connections_list"
    | "wright_connection_plans"
    | "wright_connection_plan"
    | "wright_connection_plan_read"
    | "wright_connection_plan_update"
    | "wright_connection_signin"
    | "wright_connection_validate"
    | "wright_connection_enable",
  args: Record<string, unknown>,
) => Promise<CallToolResult>;
interface Connection {
  capability_id: string;
  name: string;
  description: string;
  local_validation?: {
    evidence_id: string;
    state: string;
    observed_at: string;
    reason_codes: string[];
  } | null;
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
  plan_digest: string;
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
  openLink,
}: {
  readonly workspace: DesktopWorkspace;
  readonly call: ConnectionsCall;
  readonly openLink?: (url: string) => Promise<void>;
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
  const [saved, setSaved] = useState<{
    capabilityId: string;
    plans: { plan_id: string; state: string; created_at: string }[];
  } | null>(null);
  const [savedError, setSavedError] = useState(false);
  async function savedPlans(capabilityId: string, planId?: string) {
    if (planning || acting) return;
    setPlanning(true);
    setSavedError(false);
    try {
      const result = await call(
        planId ? "wright_connection_plan_read" : "wright_connection_plans",
        {
          workspace_id: workspace.workspace_id,
          session_id: workspace.session_id,
          ...(planId ? { plan_id: planId } : { capability_id: capabilityId }),
        },
      );
      const data = result.structuredContent;
      if (
        result.isError ||
        data?.workspace_id !== workspace.workspace_id ||
        data?.session_id !== workspace.session_id
      )
        throw Error("Unconfirmed saved setup scope");
      if (planId) {
        const current = data?.plan as SetupPlan | undefined;
        if (
          !current ||
          current.plan_id !== planId ||
          current.workspace_id !== workspace.workspace_id ||
          current.requested_scope !== "workspace" ||
          current.capability_id !== capabilityId
        )
          throw Error("Unconfirmed saved plan");
        setPlan(current);
        setUncertain(false);
      } else {
        if (
          data.capability_id !== capabilityId ||
          !Array.isArray(data.plans) ||
          data.plans.some(
            (item) =>
              item.workspace_id !== workspace.workspace_id ||
              item.capability_id !== capabilityId,
          )
        )
          throw Error("Unconfirmed saved plan list");
        setSaved({ capabilityId, plans: data.plans });
      }
    } catch {
      setSavedError(true);
    } finally {
      setPlanning(false);
    }
  }
  const [plan, setPlan] = useState<SetupPlan>();
  const [planError, setPlanError] = useState(false);
  const [acting, setActing] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [licenseCapability, setLicenseCapability] = useState<string | null>(
    null,
  );
  async function prepare(capabilityId: string) {
    setPlanning(true);
    setPlan(undefined);
    setPlanError(false);
    setUncertain(false);
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
  async function planAction(operation: "read" | "approve" | "apply") {
    if (!plan || acting) return;
    setActing(true);
    try {
      const scope = {
        workspace_id: workspace.workspace_id,
        session_id: workspace.session_id,
        plan_id: plan.plan_id,
      };
      if (operation !== "read") {
        const result = await call("wright_connection_plan_update", {
          ...scope,
          operation,
          plan_digest: plan.plan_digest,
        });
        if (result.isError) throw new Error("Setup response not confirmed");
        // Re-read the durable owner after any mutation. Never repeat a mutation
        // to determine whether its response was lost.
      }
      const result = await call("wright_connection_plan_read", scope);
      const data = result.structuredContent;
      const current = data?.plan as SetupPlan | undefined;
      if (
        result.isError ||
        data?.workspace_id !== workspace.workspace_id ||
        data?.session_id !== workspace.session_id ||
        !current ||
        current.plan_id !== plan.plan_id ||
        current.workspace_id !== workspace.workspace_id ||
        current.requested_scope !== "workspace" ||
        current.capability_id !== plan.capability_id
      )
        throw new Error("Plan identity not confirmed");
      setPlan(current);
      setUncertain(false);
      if (current.state === "completed") setRefresh((value) => value + 1);
    } catch {
      setUncertain(true);
    } finally {
      setActing(false);
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
                  {item.local_validation ? (
                    <div>
                      <p>
                        Last recorded protocol validation:{" "}
                        {item.local_validation.state}.
                      </p>
                      <p>
                        Observed: {item.local_validation.observed_at}. Evidence:{" "}
                        {item.local_validation.evidence_id}.
                      </p>
                      {item.local_validation.reason_codes.map((reason) => (
                        <p key={reason}>{reason.replaceAll("_", " ")}</p>
                      ))}
                      <p>
                        This record does not confirm current readiness or grant
                        workflow actions.
                      </p>
                    </div>
                  ) : (
                    <p>No local protocol validation recorded.</p>
                  )}
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
                  disabled={planning || acting || uncertain}
                  onClick={() => void savedPlans(item.capability_id)}
                >
                  Saved setup for {item.name}
                </button>
                <button
                  disabled={planning || acting || uncertain}
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
      {planning && <p role="status">Reading setup…</p>}
      {savedError && (
        <p role="alert">
          Saved setup could not be read. No setup action was requested.
        </p>
      )}
      {saved && (
        <section aria-label="Saved setup plans">
          <h3>Saved setup plans</h3>
          <p>
            Up to 20 most recent plans for this provider in this workspace.
            Opening one does not resume setup.
          </p>
          {saved.plans.length === 0 && (
            <p>No saved setup plans for this provider.</p>
          )}
          {saved.plans.map((item) => (
            <button
              key={item.plan_id}
              disabled={planning || acting || uncertain}
              onClick={() => void savedPlans(saved.capabilityId, item.plan_id)}
            >
              Open {item.state} setup — {item.created_at}
            </button>
          ))}
        </section>
      )}
      {planError && (
        <p role="alert">
          The setup plan was not confirmed. No installation or permission change
          was requested.
        </p>
      )}
      {plan && (
        <section aria-label="Setup plan">
          <h3>Review setup</h3>
          <p>Plan state: {plan.state}.</p>
          {["blocked", "reviewable", "draft"].includes(plan.state) && (
            <p>Nothing has been installed or approved by this plan.</p>
          )}
          {plan.state === "completed" && (
            <p>
              Registration completed. Sign-in, protocol validation and workspace
              permission still need their own checks.
            </p>
          )}
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
          {uncertain && (
            <p role="alert">
              Setup outcome is not confirmed. Check saved status before taking
              another action; nothing will be repeated automatically.
            </p>
          )}
          <button disabled={acting} onClick={() => void planAction("read")}>
            Check saved setup status
          </button>
          {plan.state === "reviewable" && (
            <button
              disabled={acting || uncertain}
              onClick={() => void planAction("approve")}
            >
              Approve this setup plan
            </button>
          )}
          {plan.state === "approved" && (
            <button
              disabled={acting || uncertain}
              onClick={() => void planAction("apply")}
            >
              Apply approved setup
            </button>
          )}
        </section>
      )}
      {plan?.state === "completed" && (
        <NativeSignin
          key={plan.plan_id}
          scope={{
            workspace_id: workspace.workspace_id,
            session_id: workspace.session_id,
            plan_id: plan.plan_id,
            plan_digest: plan.plan_digest,
          }}
          call={call}
          openLink={openLink}
        />
      )}
      <p>
        Workspace availability never approves individual tool actions or
        engineering reviews.
      </p>
    </section>
  );
}

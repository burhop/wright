import { useRef, useState } from "react";
import type { DesktopWorkspace } from "./NativeHomePanel";
import type { ConnectionsCall, SetupPlan } from "./NativeConnections";

interface Preview {
  token: string;
  draft: {
    draft_id: string;
    draft_digest: string;
    name: string;
    endpoint: string;
  };
  expires: string;
}
export function NativeCustomConnection({
  workspace,
  call,
  disabled,
  onBusy,
  onPlan,
}: {
  workspace: DesktopWorkspace;
  call: ConnectionsCall;
  disabled: boolean;
  onBusy: (busy: boolean) => void;
  onPlan: (plan: SetupPlan) => void;
}) {
  const inFlight = useRef(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [preview, setPreview] = useState<Preview>();
  const [completedSetup, setCompletedSetup] = useState(false);
  const [error, setError] = useState("");
  const [uncertain, setUncertain] = useState(false);
  async function prepare() {
    if (inFlight.current || uncertain) return;
    setError("");
    let parsed: URL;
    try {
      parsed = new URL(url);
    } catch {
      setError("Enter a public HTTPS MCP endpoint.");
      return;
    }
    if (
      parsed.protocol !== "https:" ||
      parsed.username ||
      parsed.password ||
      parsed.search ||
      parsed.hash
    ) {
      setError(
        "Use a public HTTPS endpoint without credentials, query or fragment. Nothing was sent.",
      );
      return;
    }
    inFlight.current = true;
    onBusy(true);
    setPreview(undefined);
    try {
      const result = await call("wright_connection_preview", {
        workspace_id: workspace.workspace_id,
        session_id: workspace.session_id,
        name: name.trim(),
        url,
      });
      const data = result.structuredContent;
      const value = data?.preview as
        | {
            drafts?: (Preview["draft"] & { errors: unknown[] })[];
            document_errors?: unknown[];
            expires_at?: string;
          }
        | undefined;
      const draft = value?.drafts?.[0];
      if (
        result.isError ||
        data?.workspace_id !== workspace.workspace_id ||
        data?.session_id !== workspace.session_id ||
        typeof data.preview_token !== "string" ||
        value?.drafts?.length !== 1 ||
        !draft ||
        draft.errors.length ||
        value.document_errors?.length ||
        draft.name !== name.trim() ||
        draft.endpoint !== url ||
        !value.expires_at
      )
        throw Error();
      setPreview({
        token: data.preview_token,
        draft,
        expires: value.expires_at,
      });
    } catch {
      setError(
        "Preview could not be confirmed. No setup was applied. You can explicitly preview again.",
      );
    } finally {
      inFlight.current = false;
      onBusy(false);
    }
  }
  async function savePlan() {
    if (!preview || uncertain || inFlight.current) return;
    inFlight.current = true;
    onBusy(true);
    setError("");
    try {
      const result = await call("wright_connection_import_plan", {
        workspace_id: workspace.workspace_id,
        session_id: workspace.session_id,
        preview_token: preview.token,
        draft_id: preview.draft.draft_id,
        draft_digest: preview.draft.draft_digest,
        independently_completed_license: completedSetup,
      });
      const data = result.structuredContent;
      const plan = data?.plan as SetupPlan | undefined;
      if (
        result.isError ||
        data?.workspace_id !== workspace.workspace_id ||
        data?.session_id !== workspace.session_id ||
        !plan ||
        plan.workspace_id !== workspace.workspace_id ||
        plan.requested_scope !== "workspace" ||
        !plan.capability_id.startsWith("import:")
      )
        throw Error();
      onPlan(plan);
      setPreview(undefined);
    } catch {
      setUncertain(true);
      setError(
        "The setup plan response was not confirmed. Use Saved setup in this workspace to check for the saved plan. Do not repeat creation automatically; no installation was requested here.",
      );
    } finally {
      inFlight.current = false;
      onBusy(false);
    }
  }
  return (
    <details>
      <summary>Add a custom MCP</summary>
      <p>
        Public HTTPS endpoints are supported here. Do not enter passwords,
        tokens or private credential URLs. Local commands, configuration-file
        imports and credential entry are not available in this form yet.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void prepare();
        }}
      >
        <label>
          Connection name
          <input
            value={name}
            maxLength={100}
            required
            disabled={disabled || uncertain}
            onChange={(event) => {
              setName(event.target.value);
              setPreview(undefined);
              setCompletedSetup(false);
            }}
          />
        </label>
        <label>
          Public MCP endpoint
          <input
            value={url}
            type="url"
            maxLength={2048}
            required
            disabled={disabled || uncertain}
            onChange={(event) => {
              setUrl(event.target.value);
              setPreview(undefined);
              setCompletedSetup(false);
            }}
          />
        </label>
        <button disabled={disabled || uncertain || !name.trim() || !url}>
          Preview connection
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {preview && (
        <section aria-label="Custom connection preview">
          <p>
            {preview.draft.name}: {preview.draft.endpoint}
          </p>
          <p>
            Preview expires: {preview.expires}. Previewing does not connect or
            install.
          </p>
          <label>
            <input
              type="checkbox"
              checked={completedSetup}
              disabled={disabled || uncertain}
              onChange={(event) => setCompletedSetup(event.target.checked)}
            />
            I independently reviewed this source and completed its publisher
            terms and account requirements.
          </label>
          <button
            disabled={disabled || uncertain}
            onClick={() => void savePlan()}
          >
            Review custom setup
          </button>
        </section>
      )}
    </details>
  );
}

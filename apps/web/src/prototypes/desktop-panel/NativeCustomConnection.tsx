import {
  importConnectionConfiguration,
  type ImportedConnection,
} from "./connection-config-import";
import { useEffect, useRef, useState } from "react";
import type { DesktopWorkspace } from "./NativeHomePanel";
import type { ConnectionsCall, SetupPlan } from "./NativeConnections";

interface Preview {
  token: string;
  draft: {
    draft_id: string;
    draft_digest: string;
    name: string;
    transport?: string;
    endpoint?: string | null;
    command?: string | null;
    arguments?: string[];
    launch_env?: Record<string, string>;
    env_vars?: { name: string }[];
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
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [transport, setTransport] = useState("https");
  const [command, setCommand] = useState("");
  const [argumentsText, setArgumentsText] = useState("[]");
  const [imports, setImports] = useState<ImportedConnection[]>([]);
  const [imported, setImported] = useState<ImportedConnection>();
  const [publicFields, setPublicFields] = useState<Record<string, boolean>>({});
  function selectImport(candidate: ImportedConnection) {
    setImported(candidate);
    setPublicFields({});
    setName(candidate.name);
    setTransport(candidate.type);
    setCommand(candidate.command);
    setArgumentsText(JSON.stringify(candidate.arguments));
    setUrl(candidate.url);
    setPreview(undefined);
    setError("");
    setCompletedSetup(false);
  }
  async function loadConfiguration(file?: File) {
    if (!file || disabled || uncertain) return;
    setPreview(undefined);
    setImports([]);
    setImported(undefined);
    setPublicFields({});
    setError("");
    try {
      if (file.size > 256 * 1024) throw Error();
      const candidates = importConnectionConfiguration(await file.text());
      if (!mounted.current) return;
      setImports(candidates);
      selectImport(candidates[0]);
    } catch {
      setError(
        "Configuration was not imported or sent. Use supported JSON with literal commands or public HTTPS endpoints. HTTP headers, extra fields and credential arguments are not qualified here.",
      );
    }
  }
  const [preview, setPreview] = useState<Preview>();
  const [completedSetup, setCompletedSetup] = useState(false);
  const [error, setError] = useState("");
  const [uncertain, setUncertain] = useState(false);
  async function prepare() {
    if (inFlight.current || uncertain) return;
    setError("");
    let arguments_: string[] = [];
    if (transport === "https") {
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
    } else {
      try {
        const value: unknown = JSON.parse(argumentsText);
        if (
          !Array.isArray(value) ||
          value.length > 512 ||
          !value.every(
            (item) => typeof item === "string" && item.length <= 4096,
          ) ||
          value.reduce((total, item: string) => total + item.length, 0) > 65536
        ) {
          throw Error();
        }
        arguments_ = value;
      } catch {
        setError(
          "Arguments must be a bounded JSON array of strings. Nothing was sent.",
        );
        return;
      }
    }
    inFlight.current = true;
    onBusy(true);
    setPreview(undefined);
    try {
      const scope = {
        workspace_id: workspace.workspace_id,
        session_id: workspace.session_id,
        name: name.trim(),
      };
      const result =
        transport === "https"
          ? await call("wright_connection_preview", { ...scope, url })
          : await call(
              imported?.environmentFields.length
                ? "wright_connection_configuration_preview"
                : "wright_connection_command_preview",
              {
                request: {
                  ...scope,
                  command: command.trim(),
                  arguments: arguments_,
                  ...(imported?.environmentFields.length
                    ? {
                        environment_fields: imported.environmentFields,
                        public_environment: Object.fromEntries(
                          Object.entries(imported.publicCandidates).filter(
                            ([key]) => publicFields[key],
                          ),
                        ),
                      }
                    : {}),
                },
              },
            );
      if (!mounted.current) return;
      const data = result.structuredContent;
      const value = data?.preview as
        | {
            drafts?: (Preview["draft"] & { errors: { message?: string }[] })[];
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
        value.document_errors?.length ||
        draft.name !== name.trim() ||
        !value.expires_at
      )
        throw Error();
      if (draft.errors.length) {
        setError(
          "Configuration needs changes: " +
            draft.errors
              .map((item) => item.message || "Review the source configuration.")
              .join(" "),
        );
        return;
      }
      if (
        transport === "https"
          ? draft.endpoint !== url
          : draft.transport !== "stdio" ||
            draft.command !== command.trim() ||
            JSON.stringify(draft.arguments) !== JSON.stringify(arguments_)
      )
        throw Error();
      if (transport === "stdio" && imported?.environmentFields.length) {
        const expected = Object.fromEntries(
          Object.entries(imported.publicCandidates).filter(
            ([key]) => publicFields[key],
          ),
        );
        const actual = draft.launch_env ?? {};
        if (
          Object.keys(expected).length !== Object.keys(actual).length ||
          Object.entries(expected).some(
            ([key, value]) => actual[key] !== value,
          ) ||
          JSON.stringify(
            (draft.env_vars ?? []).map((field) => field.name).sort(),
          ) !==
            JSON.stringify(
              imported.environmentFields
                .filter((key) => !(key in expected))
                .sort(),
            )
        )
          throw Error("Unconfirmed environment configuration");
      }
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
      if (!mounted.current) return;
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
        Add a public HTTPS endpoint or a local command. Commands run on the
        Wright host (GB10 here), not on the Windows desktop. Do not enter
        passwords, tokens, credential arguments or private URLs. Import
        environment names from JSON, then enter private values after setup. Only
        explicitly selected public values are sent with the reviewed plan.
      </p>
      <label>
        Import MCP configuration (JSON)
        <input
          type="file"
          accept=".json,application/json"
          disabled={disabled || uncertain}
          onChange={(event) => void loadConfiguration(event.target.files?.[0])}
        />
      </label>
      {imports.length > 1 && (
        <label>
          Imported connection
          <select
            value={imported?.name ?? ""}
            disabled={disabled || uncertain}
            onChange={(event) => {
              const next = imports.find(
                (item) => item.name === event.target.value,
              );
              if (next) selectImport(next);
            }}
          >
            {imports.map((item) => (
              <option key={item.name}>{item.name}</option>
            ))}
          </select>
        </label>
      )}
      {imported?.environmentFields.length ? (
        <div>
          <p>
            Environment fields: {imported.environmentFields.join(", ")}. Private
            values were discarded; enter them after setup.
          </p>
          {Object.entries(imported.publicCandidates).map(([key, value]) => (
            <label key={key}>
              <input
                type="checkbox"
                checked={!!publicFields[key]}
                disabled={disabled || uncertain}
                onChange={(event) => {
                  setPublicFields((current) => ({
                    ...current,
                    [key]: event.target.checked,
                  }));
                  setPreview(undefined);
                }}
              />
              Include {key} as public:{" "}
              <code className="native-connection-endpoint">{value}</code>
            </label>
          ))}
        </div>
      ) : null}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void prepare();
        }}
      >
        <label htmlFor="wright-custom-connection-type">Connection type</label>
        <select
          id="wright-custom-connection-type"
          value={transport}
          disabled={disabled || uncertain}
          onChange={(event) => {
            setTransport(event.target.value);
            setPreview(undefined);
            setCompletedSetup(false);
            setError("");
          }}
        >
          <option value="https">Public HTTPS endpoint</option>
          <option value="stdio">Local command on Wright host</option>
        </select>
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
        {transport === "https" ? (
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
        ) : (
          <>
            <label>
              Executable on Wright host
              <input
                value={command}
                maxLength={500}
                required
                disabled={disabled || uncertain}
                onChange={(event) => {
                  setCommand(event.target.value);
                  setPreview(undefined);
                  setCompletedSetup(false);
                }}
              />
            </label>
            <label htmlFor="wright-custom-command-arguments">
              Arguments (JSON array)
            </label>
            <textarea
              id="wright-custom-command-arguments"
              value={argumentsText}
              maxLength={70000}
              disabled={disabled || uncertain}
              onChange={(event) => {
                setArgumentsText(event.target.value);
                setPreview(undefined);
                setCompletedSetup(false);
              }}
            />
          </>
        )}
        <button
          disabled={
            disabled ||
            uncertain ||
            !name.trim() ||
            (transport === "https" ? !url : !command.trim())
          }
        >
          Preview connection
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {preview && (
        <section aria-label="Custom connection preview">
          <p>
            {preview.draft.name}:{" "}
            {preview.draft.endpoint || preview.draft.command}
          </p>
          {preview.draft.command && (
            <p className="native-connection-endpoint">
              {JSON.stringify(preview.draft.arguments)}
            </p>
          )}
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
            I independently verified this exact source, its license and any
            required publisher setup.
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

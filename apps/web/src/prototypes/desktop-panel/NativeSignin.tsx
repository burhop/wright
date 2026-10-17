import { useCallback, useEffect, useRef, useState } from "react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
export type SigninCall = (
  name:
    | "wright_connection_signin"
    | "wright_connection_validate"
    | "wright_connection_enable",
  args: Record<string, unknown>,
) => Promise<CallToolResult>;
export function NativeSignin({
  scope,
  call,
  openLink,
}: {
  readonly scope: {
    workspace_id: string;
    session_id: string;
    plan_id: string;
    plan_digest: string;
  };
  readonly call: SigninCall;
  readonly openLink?: (url: string) => Promise<void>;
}) {
  const [pending, setPending] = useState(false);
  const [validated, setValidated] = useState(false);
  const [enableAttempted, setEnableAttempted] = useState(false);
  const [enablePending, setEnablePending] = useState(false);
  const enabling = useRef(false);
  const [attempted, setAttempted] = useState(false);
  const [message, setMessage] = useState("");
  const [url, setUrl] = useState<string>();
  const [callback, setCallback] = useState<string>();
  const started = useRef(false);
  const readGeneration = useRef(0);
  const livePoll = useRef<AbortController | null>(null);
  const read = useCallback(
    async (signal?: AbortSignal) => {
      const generation = ++readGeneration.current;
      const result = await call("wright_connection_signin", {
        workspace_id: scope.workspace_id,
        session_id: scope.session_id,
        plan_id: scope.plan_id,
      });
      const data = result.structuredContent;
      if (
        result.isError ||
        data?.workspace_id !== scope.workspace_id ||
        data?.session_id !== scope.session_id ||
        data?.plan_id !== scope.plan_id
      )
        throw Error("Scope unavailable");
      if (signal?.aborted || generation !== readGeneration.current) return;
      const provider = data.provider_status as {
        installed?: boolean;
        active?: boolean;
        enabled_here?: boolean;
        recorded_validation?: { evidence_id?: string; state?: string } | null;
      } | null | undefined;
      if (provider != null) {
        if (data.plan_digest !== scope.plan_digest ||
            typeof provider.installed !== "boolean" ||
            typeof provider.active !== "boolean" ||
            typeof provider.enabled_here !== "boolean")
          throw Error("Saved provider subject unavailable");
        const passed = provider.installed &&
          provider.recorded_validation?.state === "passed" &&
          typeof provider.recorded_validation.evidence_id === "string" &&
          provider.recorded_validation.evidence_id.length > 0;
        setValidated(passed);
        setEnableAttempted(provider.enabled_here);
        // A fresh saved-state read permits a new explicit grant attempt only.
        // It never retries an uncertain operation itself.
        enabling.current = false;
        if (provider.enabled_here) {
          setMessage("Saved workspace availability is enabled. Individual tool actions and reviews remain separate.");
        } else if (passed) {
          setMessage("Recorded protocol validation passed. Enable will recheck current configuration and evidence; no validation was repeated.");
        } else {
          setMessage("Saved provider check is " + (provider.recorded_validation?.state ?? "not recorded") + ". Workspace enablement requires current passed validation.");
        }
      }
      const privateData = result._meta?.["wright/signin"] as
        { authorization_url?: string; callback_uri?: string } | undefined;
      if (
        data.presentation === "awaiting_user" &&
        privateData?.authorization_url &&
        privateData.callback_uri
      ) {
        const target = new URL(privateData.authorization_url);
        const receiver = new URL(privateData.callback_uri);
        if (
          target.protocol !== "https:" ||
          target.username ||
          target.password ||
          receiver.protocol !== "http:" ||
          receiver.hostname !== "127.0.0.1" ||
          receiver.pathname !== "/oauth/callback"
        )
          throw Error("Unsupported sign-in address");
        setUrl(target.href);
        setCallback(receiver.href);
      } else {
        setUrl(undefined);
        setCallback(undefined);
      }
    },
    [call, scope.workspace_id, scope.session_id, scope.plan_id, scope.plan_digest],
  );
  useEffect(() => {
    if (!pending) return;
    let active = true;
    const controller = new AbortController();
    livePoll.current = controller;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        await read(controller.signal);
      } catch {
        if (active) {
          setUrl(undefined);
          setCallback(undefined);
        }
      }
      if (active) timer = setTimeout(() => void poll(), 1000);
    }
    void poll();
    return () => {
      active = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [pending, read]);
  async function start() {
    if (started.current) return;
    started.current = true;
    setAttempted(true);
    setPending(true);
    setValidated(false);
    setMessage("Checking the installed provider; sign-in may be required.");
    try {
      const result = await call("wright_connection_validate", scope);
      const data = result.structuredContent;
      if (
        result.isError ||
        data?.workspace_id !== scope.workspace_id ||
        data?.session_id !== scope.session_id ||
        data?.plan_id !== scope.plan_id
      )
        throw Error("Unconfirmed validation");
      const validation = data.validation as { state?: string } | undefined;
      setValidated(validation?.state === "passed");
      setMessage(
        validation?.state === "passed"
          ? "Protocol validation passed. Workspace permission is still separate."
          : `Protocol validation: ${validation?.state ?? "unconfirmed"}. Check readiness details.`,
      );
    } catch {
      setValidated(false);
      setMessage(
        "Validation outcome is not confirmed. Check sign-in status and recorded readiness before another attempt; no request was repeated.",
      );
    } finally {
      ++readGeneration.current;
      livePoll.current?.abort();
      setPending(false);
      setUrl(undefined);
      setCallback(undefined);
    }
  }
  async function enable() {
    if (!validated || enabling.current) return;
    enabling.current = true;
    ++readGeneration.current;
    setEnablePending(true);
    setEnableAttempted(true);
    try {
      const result = await call("wright_connection_enable", scope);
      const data = result.structuredContent;
      const enabled = data?.enablement as
        { enabled?: boolean; invocation_approved?: boolean } | undefined;
      if (
        result.isError ||
        data?.workspace_id !== scope.workspace_id ||
        data?.session_id !== scope.session_id ||
        data?.plan_id !== scope.plan_id ||
        enabled?.enabled !== true ||
        enabled.invocation_approved !== false
      )
        throw Error("Unconfirmed workspace availability");
      setMessage(
        "Enabled in this workspace. Individual tool actions and engineering reviews remain separate.",
      );
    } catch {
      setMessage(
        "Workspace availability was not confirmed. Check sign-in status to read saved provider availability; no enable request was repeated.",
      );
    } finally {
      ++readGeneration.current;
      setEnablePending(false);
    }
  }
  return (
    <section aria-label="Provider sign-in">
      <h3>Sign in and check provider</h3>
      <p>
        This checks the installed provider without enabling workflow tools. A
        Windows browser needs a working route to the GB10 callback; remote
        callback forwarding is not yet qualified.
      </p>
      <button disabled={attempted} onClick={() => void start()}>
        Sign in and validate provider
      </button>
      <button
        disabled={enablePending}
        onClick={() =>
          void read().catch(() => {
            setUrl(undefined);
            setCallback(undefined);
            setValidated(false);
            setMessage("Sign-in status unavailable.");
          })
        }
      >
        Check sign-in status
      </button>
      {validated && (
        <button disabled={pending || enableAttempted || enablePending} onClick={() => void enable()}>
          Enable in this workspace
        </button>
      )}
      {message && <p role="status">{message}</p>}
      {url && (
        <button
          disabled={!openLink}
          onClick={() =>
            void openLink?.(url).catch(() =>
              setMessage(
                "The host could not open sign-in. No new login request was started.",
              ),
            )
          }
        >
          Open provider sign-in
        </button>
      )}
      {callback && (
        <details>
          <summary>Remote callback setup</summary>
          <p>
            Forward this loopback address to the same GB10 port before
            completing sign-in: {callback}
          </p>
        </details>
      )}
    </section>
  );
}

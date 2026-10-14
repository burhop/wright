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
    [call, scope.workspace_id, scope.session_id, scope.plan_id],
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
        "Workspace availability was not confirmed. Refresh Connections to read saved status; no enable request was repeated.",
      );
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
        onClick={() =>
          void read().catch(() => {
            setUrl(undefined);
            setCallback(undefined);
            setMessage("Sign-in status unavailable.");
          })
        }
      >
        Check sign-in status
      </button>
      {validated && (
        <button disabled={enableAttempted} onClick={() => void enable()}>
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

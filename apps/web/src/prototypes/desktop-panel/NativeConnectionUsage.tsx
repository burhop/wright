import { useEffect, useRef, useState } from "react";
import type { ConnectionsCall } from "./NativeConnections";

interface Usage {
  scope: "selected-workspace-saved-explicit-bindings";
  scan_complete: boolean;
  matches: {
    path: string;
    title: string;
    source_digest: string;
    steps: { id: string; title: string }[];
  }[];
  unchecked_paths: string[];
}

/** Optional read-only lookup; provider controls never infer an approval from it. */
export function NativeConnectionUsage({
  call,
  scope,
  controlDigest,
}: {
  call: ConnectionsCall;
  scope: {
    workspace_id: string;
    session_id: string;
    capability_id: string;
    server_id: string;
  };
  controlDigest: string;
}) {
  const [usage, setUsage] = useState<Usage>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [shown, setShown] = useState(8);
  const flight = useRef(false);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  async function read() {
    if (flight.current) return;
    flight.current = true;
    setBusy(true);
    setUsage(undefined);
    setShown(8);
    setError("");
    try {
      const result = await call("wright_connection_workflows", scope);
      const text = result.content.find((item) => item.type === "text");
      const data =
        result.structuredContent ??
        (text?.type === "text" ? JSON.parse(text.text) : null);
      const next = data?.usage as Usage | undefined;
      if (
        result.isError ||
        !data ||
        Object.entries(scope).some(([key, value]) => data[key] !== value) ||
        data.control_digest !== controlDigest ||
        next?.scope !== "selected-workspace-saved-explicit-bindings" ||
        typeof next.scan_complete !== "boolean" ||
        !Array.isArray(next.matches) ||
        next.matches.length > 64 ||
        !Array.isArray(next.unchecked_paths) ||
        next.unchecked_paths.length > 64 ||
        next.unchecked_paths.some((path) => typeof path !== "string") ||
        next.matches.some(
          (match) =>
            typeof match.path !== "string" ||
            typeof match.title !== "string" ||
            !/^[a-f0-9]{64}$/.test(match.source_digest) ||
            !Array.isArray(match.steps) ||
            match.steps.some(
              (step) =>
                typeof step.id !== "string" || typeof step.title !== "string",
            ),
        )
      ) {
        throw Error("Unconfirmed workflow usage");
      }
      if (alive.current) setUsage(next);
    } catch {
      if (alive.current)
        setError(
          "Workflow usage could not be confirmed. Refresh provider state before checking again.",
        );
    } finally {
      flight.current = false;
      if (alive.current) setBusy(false);
    }
  }
  return (
    <details>
      <summary>Workflows using this connection</summary>
      <p>
        Check saved workflows in this workspace before changing or removing the
        connection.
      </p>
      <button disabled={busy} onClick={() => void read()}>
        {busy ? "Checking workflows…" : "Check saved workflows"}
      </button>
      {error && <p role="status">{error}</p>}
      {usage && (
        <div role="status">
          {!usage.scan_complete && (
            <p>Some workflows could not be checked. This list is incomplete.</p>
          )}
          {usage.matches.length === 0 && (
            <p>No explicit references found in the workflows checked.</p>
          )}
          <ul>
            {usage.matches.slice(0, shown).map((match) => (
              <li key={match.path}>
                <strong>{match.title}</strong>
                <details>
                  <summary>
                    {match.steps.length} referenced{" "}
                    {match.steps.length === 1 ? "step" : "steps"}
                  </summary>
                  <ul>
                    {match.steps.map((step) => (
                      <li key={step.id}>{step.title}</li>
                    ))}
                  </ul>
                </details>
                <details>
                  <summary>File location</summary>
                  <code>{match.path}</code>
                </details>
              </li>
            ))}
          </ul>
          {shown < usage.matches.length && (
            <button onClick={() => setShown((count) => count + 8)}>
              Show more workflows ({usage.matches.length - shown} remaining)
            </button>
          )}
          {usage.unchecked_paths.length > 0 && (
            <details>
              <summary>Unchecked files</summary>
              <ul>
                {usage.unchecked_paths.map((path) => (
                  <li key={path}>{path}</li>
                ))}
              </ul>
            </details>
          )}
          <p>
            This is a saved-file snapshot. Other workspaces, active runs and
            unsaved edits are not checked. Recheck readiness before running;
            existing workflows are not moved to a replacement connection.
          </p>
        </div>
      )}
    </details>
  );
}

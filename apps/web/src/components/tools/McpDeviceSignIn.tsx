import { useEffect, useState } from "react";
import { mcpService } from "../../services/mcp-service";

type DeviceChallenge = {
  verification_uri: string;
  verification_uri_complete?: string | null;
  user_code: string;
  expires_in: number;
};

/** Presentation only: the existing backend connection check owns authorization. */
export function McpDeviceSignIn({
  serverId,
  active,
}: {
  serverId: string;
  active: boolean;
}) {
  const [challenge, setChallenge] = useState<DeviceChallenge | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    setChallenge(null);
    setError(false);
    if (!active || !serverId) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const result = await mcpService.readDeviceSignIn(serverId);
        if (!stopped) {
          setChallenge(
            result.presentation === "awaiting_user" ? result.device : null,
          );
          setError(false);
        }
      } catch {
        if (!stopped) setError(true);
      }
      if (!stopped) timer = setTimeout(poll, 1000);
    };
    void poll();
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [serverId, active]);
  if (!active) return null;
  if (error)
    return (
      <p role="status">
        Sign-in instructions could not be retrieved. The connection check may
        still be running; do not start another check yet.
      </p>
    );
  if (!challenge) return null;
  return (
    <div
      role="status"
      style={{
        border: "1px solid var(--color-border)",
        padding: "var(--space-md)",
        borderRadius: "var(--radius-lg)",
      }}
    >
      <strong>Approve this connection</strong>
      <p>
        Open the provider’s approval page in your usual browser and enter this
        code:
      </p>
      <p>
        <code style={{ fontSize: "1.5rem", letterSpacing: "0.12em" }}>
          {challenge.user_code}
        </code>
      </p>
      <a
        href={challenge.verification_uri_complete || challenge.verification_uri}
        target="_blank"
        rel="noopener noreferrer"
      >
        Open approval page
      </a>
      <p>
        Keep this connection check open. Wright will report the result after you
        approve.
      </p>
    </div>
  );
}

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { workspaceService } from "../../services/workspace-service";

type GitStatus = Awaited<ReturnType<typeof workspaceService.getGitStatus>>;
type History = Awaited<
  ReturnType<typeof workspaceService.getGitHistory>
>["commits"];
const DEFAULT_LARGE_FILE_THRESHOLD = 10 * 1024 * 1024;
const formatBytes = (bytes: number) => {
  const unit = bytes >= 1024 * 1024 ? "MiB" : bytes >= 1024 ? "KiB" : "B";
  const divisor = unit === "MiB" ? 1024 * 1024 : unit === "KiB" ? 1024 : 1;
  return `${new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(bytes / divisor)} ${unit}`;
};

export function WorkspaceGitPanel({
  sessionId,
  refreshVersion,
  onDiff,
}: {
  sessionId: string | null;
  refreshVersion: number;
  onDiff: (path: string, text: string) => void;
}) {
  const [status, setStatus] = useState<GitStatus | null>(null);
  const [history, setHistory] = useState<History>([]);
  const [remote, setRemote] = useState(false);
  const [largeFileThreshold, setLargeFileThreshold] = useState(
    DEFAULT_LARGE_FILE_THRESHOLD,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [branch, setBranch] = useState("");
  const request = useRef(0);
  const scope = useRef(sessionId);
  useLayoutEffect(() => {
    scope.current = sessionId;
    return () => {
      scope.current = null;
    };
  }, [sessionId]);
  const refresh = useCallback(async () => {
    if (!sessionId || sessionId !== scope.current) return;
    const sequence = ++request.current;
    setBusy(true);
    setError(null);
    try {
      const current = await workspaceService.getGitStatus(sessionId);
      let log: History = [],
        hasRemote = false,
        threshold = DEFAULT_LARGE_FILE_THRESHOLD;
      if (current.is_repository !== false) {
        const [response, config] = await Promise.all([
          workspaceService.getGitHistory(sessionId),
          workspaceService.getWorkspaceConfig(sessionId),
        ]);
        log = response.commits;
        hasRemote = Boolean(config.git_remote_url);
        const configuredThreshold = config.git_large_file_threshold;
        if (
          typeof configuredThreshold === "number" &&
          Number.isFinite(configuredThreshold) &&
          configuredThreshold > 0
        )
          threshold = configuredThreshold;
      }
      if (sequence !== request.current || sessionId !== scope.current) return;
      setStatus(current);
      setHistory(log);
      setRemote(hasRemote);
      setLargeFileThreshold(threshold);
    } catch (e) {
      if (sequence === request.current && sessionId === scope.current)
        setError(e instanceof Error ? e.message : "Could not load Git status.");
    } finally {
      if (sequence === request.current && sessionId === scope.current)
        setBusy(false);
    }
  }, [sessionId]);
  useEffect(() => {
    setStatus(null);
    setHistory([]);
    setRemote(false);
    setError(null);
    setLargeFileThreshold(DEFAULT_LARGE_FILE_THRESHOLD);
    void refresh();
    return () => {
      request.current++;
    };
  }, [refresh, refreshVersion]);
  async function action(work: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await work();
      await refresh();
    } catch (e) {
      if (sessionId === scope.current)
        setError(e instanceof Error ? e.message : "Git action failed.");
    } finally {
      if (sessionId === scope.current) setBusy(false);
    }
  }
  const buttonStyle = {
    padding: "6px 10px",
    cursor: "pointer",
    borderRadius: 4,
    background: "var(--color-surface-elevated)",
    color: "var(--color-primary)",
    border: "1px solid var(--color-border)",
  };
  const inputStyle = {
    width: "100%",
    boxSizing: "border-box" as const,
    padding: 8,
    borderRadius: 4,
    background: "var(--color-neutral)",
    color: "var(--color-primary)",
    border: "1px solid var(--color-border)",
  };
  const isLargeFile = (file: GitStatus["changes"][number]) =>
    typeof file.file_size === "number" &&
    Number.isFinite(file.file_size) &&
    file.file_size > largeFileThreshold;
  const largeFileCount = status?.changes.filter(isLargeFile).length ?? 0;
  return (
    <section
      data-testid="git-panel"
      aria-label="Git Version Control"
      style={{
        padding: 12,
        overflowY: "auto",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <h2 style={{ fontSize: 14, margin: 0 }}>Git Version Control</h2>
      {!sessionId ? (
        <p>No active workspace.</p>
      ) : (
        <>
          <button
            style={buttonStyle}
            disabled={busy}
            onClick={() => void refresh()}
          >
            Refresh Git
          </button>
          {busy && <p role="status">Updating Git…</p>}
          {error && <p role="alert">{error}</p>}
          {status?.is_repository === false ? (
            <>
              <p>This workspace does not have a Git repository.</p>
              <button
                style={buttonStyle}
                disabled={busy}
                onClick={() =>
                  void action(() => workspaceService.initializeGit(sessionId))
                }
              >
                Create repository
              </button>
            </>
          ) : (
            status && (
              <>
                <p>
                  Branch:{" "}
                  <strong>{status.branch_name || "Detached HEAD"}</strong>
                </p>
                {largeFileCount > 0 && (
                  <p
                    role="status"
                    style={{
                      color: "var(--color-warning, #fbbf24)",
                      margin: 0,
                    }}
                  >
                    {largeFileCount} changed{" "}
                    {largeFileCount === 1 ? "file exceeds" : "files exceed"} the{" "}
                    {formatBytes(largeFileThreshold)} warning threshold in
                    Workspace Settings.
                  </p>
                )}
                <h3 style={{ fontSize: 13 }}>
                  Changes ({status.changes.length})
                </h3>
                {status.changes.length === 0 && <p>No changes to commit.</p>}
                {status.changes.map((file) => (
                  <button
                    key={file.path}
                    style={{
                      ...buttonStyle,
                      textAlign: "left",
                      overflowWrap: "anywhere",
                    }}
                    disabled={busy}
                    onClick={() =>
                      void action(async () =>
                        onDiff(
                          file.path,
                          await workspaceService.getGitDiff(
                            sessionId,
                            file.path,
                          ),
                        ),
                      )
                    }
                  >
                    {file.git_status} {file.path}
                    {isLargeFile(file) && (
                      <small
                        style={{
                          display: "block",
                          color: "var(--color-warning, #fbbf24)",
                        }}
                      >
                        Large file · {formatBytes(file.file_size!)}
                      </small>
                    )}
                  </button>
                ))}
                <label>
                  Commit message
                  <input
                    aria-label="Commit message"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    style={inputStyle}
                  />
                </label>
                <button
                  style={buttonStyle}
                  disabled={busy || !message.trim() || !status.changes.length}
                  onClick={() =>
                    void action(async () => {
                      await workspaceService.commitChanges(
                        sessionId,
                        message.trim(),
                      );
                      setMessage("");
                    })
                  }
                >
                  Commit all workspace changes
                </button>
                <label>
                  Branch name
                  <input
                    aria-label="Branch name"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    style={inputStyle}
                  />
                </label>
                <button
                  style={buttonStyle}
                  disabled={busy || !branch.trim()}
                  onClick={() =>
                    void action(() =>
                      workspaceService.checkoutBranch(
                        sessionId,
                        branch.trim(),
                        true,
                      ),
                    )
                  }
                >
                  Create branch
                </button>
                <button
                  style={buttonStyle}
                  disabled={busy || !branch.trim()}
                  onClick={() =>
                    void action(() =>
                      workspaceService.checkoutBranch(sessionId, branch.trim()),
                    )
                  }
                >
                  Switch branch
                </button>
                <button
                  style={buttonStyle}
                  disabled={busy || !remote}
                  onClick={() =>
                    void action(() => workspaceService.pullCommits(sessionId))
                  }
                >
                  Pull
                </button>
                <button
                  style={buttonStyle}
                  disabled={busy || !remote}
                  onClick={() =>
                    void action(() => workspaceService.pushCommits(sessionId))
                  }
                >
                  Push
                </button>
                {!remote && (
                  <p>
                    Configure a remote in Workspace Settings to use Pull and
                    Push.
                  </p>
                )}
                <h3 style={{ fontSize: 13 }}>History</h3>
                {history.length ? (
                  history.map((commit) => (
                    <article key={commit.commit_hash}>
                      <strong>{commit.message}</strong>
                      <small style={{ display: "block" }}>
                        {commit.commit_hash.slice(0, 8)} · {commit.author}
                      </small>
                    </article>
                  ))
                ) : (
                  <p>No commits yet.</p>
                )}
              </>
            )
          )}
        </>
      )}
    </section>
  );
}

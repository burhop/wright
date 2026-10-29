import { useEffect, useRef, useState } from "react";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";
import type { RecordedRun } from "./NativeRecentRuns";

type AttentionItem = {
  checkpoint_id?: string;
  review_id?: string;
  workflow_path: string;
  run_id: string | null;
  path: string;
  source_digest: string | null;
  step_title: string | null;
  state: string;
  action_kind?: string;
  checkpoint_kind?: string | null;
  response_id?: string | null;
  expires_at?: number | null;
};
type Page = { items: AttentionItem[]; next_cursor: string | null };

function attention(item: AttentionItem): string {
  if (item.expires_at && item.expires_at <= Date.now() / 1000)
    return "Review expired — open run for next steps";
  if (item.state === "approved" || item.response_id) return "Ready to continue";
  if (item.checkpoint_kind === "input") return "Provide information";
  if (item.review_id || item.action_kind === "local_review")
    return "Review results";
  return "Review requested action";
}

/** Navigation to durable waits. Opening delegates eligibility to the run owner. */
export function NativePendingWork({
  workspace,
  call,
  titles,
  onOpen,
  disabled,
}: {
  readonly workspace: DesktopWorkspace;
  readonly call: HomeCall;
  readonly titles: Readonly<Record<string, string>>;
  readonly onOpen: (path: string, run: RecordedRun) => Promise<void>;
  readonly disabled?: boolean;
}) {
  const [items, setItems] = useState<AttentionItem[]>([]);
  const [pages, setPages] = useState<{ checkpoints: Page; reviews: Page }>();
  const [loading, setLoading] = useState(true);
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState("");
  const [visible, setVisible] = useState(3);
  const [refresh, setRefresh] = useState(0);
  const [cursor, setCursor] = useState({
    checkpoint_after: "",
    review_after: "",
  });
  const generation = useRef(0);
  useEffect(() => {
    const current = ++generation.current;
    let active = true;
    setLoading(true);
    setError("");
    void call("wright_workspace_pending", {
      workspace_id: workspace.workspace_id,
      session_id: workspace.session_id,
      ...cursor,
    })
      .then((result) => {
        const data = result.structuredContent;
        if (
          result.isError ||
          data?.workspace_id !== workspace.workspace_id ||
          data.session_id !== workspace.session_id
        )
          throw new Error("Attention scope differs");
        const checkpoints = data.checkpoints as Page;
        const reviews = data.reviews as Page;
        if (
          ![checkpoints, reviews].every(
            (page) =>
              page &&
              Array.isArray(page.items) &&
              page.items.length <= 20 &&
              page.items.every(
                (item) =>
                  item &&
                  typeof item.workflow_path === "string" &&
                  typeof item.state === "string",
              ) &&
              (page.next_cursor === null ||
                typeof page.next_cursor === "string"),
          )
        )
          throw new Error("Attention page unavailable");
        if (!active || current !== generation.current) return;
        setPages({ checkpoints, reviews });
        setItems([...checkpoints.items, ...reviews.items]);
        setVisible(3);
      })
      .catch(() => {
        if (active && current === generation.current) {
          setItems([]);
          setPages(undefined);
          setError("Could not check for work needing your attention.");
        }
      })
      .finally(() => {
        if (active && current === generation.current) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [call, workspace.workspace_id, workspace.session_id, cursor, refresh]);

  if (!loading && !error && items.length === 0) return null;
  return (
    <section
      className="native-home__attention"
      aria-label="Needs your attention"
    >
      <h2>Needs your attention</h2>
      {loading && <p role="status">Checking for questions and reviews…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading &&
        items.slice(0, visible).map((item) => (
          <div
            className="native-home__attention-row"
            key={item.checkpoint_id ?? item.review_id}
          >
            <strong>
              {titles[item.workflow_path] ??
                titles["/" + item.workflow_path] ??
                item.workflow_path
                  .split("/")
                  .at(-1)
                  ?.replace(/(?:\.workflow)?\.wflow$/, "")
                  .replace(/[-_]+/g, " ")}
            </strong>
            <span>
              {attention(item)}
              {item.step_title ? ` · ${item.step_title}` : ""}
            </span>
            {item.run_id && item.source_digest && item.path ? (
              <button
                disabled={disabled || opening}
                onClick={() => {
                  setOpening(true);
                  setError("");
                  void onOpen(item.workflow_path, {
                    run_id: item.run_id,
                    path: item.path,
                    status: item.state,
                    source_digest: item.source_digest,
                    started_at: null,
                  })
                    .catch(() =>
                      setError(
                        "This run could not be opened. Refresh to check its current state.",
                      ),
                    )
                    .finally(() => setOpening(false));
                }}
              >
                Open run
              </button>
            ) : (
              <small>Exact run link unavailable.</small>
            )}
          </div>
        ))}
      {!loading && items.length > visible && (
        <button onClick={() => setVisible(items.length)}>Show more</button>
      )}
      {!loading &&
        pages &&
        (pages.checkpoints.next_cursor || pages.reviews.next_cursor) && (
          <button
            disabled={disabled || opening}
            onClick={() =>
              setCursor({
                checkpoint_after:
                  pages.checkpoints.next_cursor ??
                  pages.checkpoints.items.at(-1)?.checkpoint_id ??
                  cursor.checkpoint_after,
                review_after:
                  pages.reviews.next_cursor ??
                  pages.reviews.items.at(-1)?.review_id ??
                  cursor.review_after,
              })
            }
          >
            Next page
          </button>
        )}
      <button
        disabled={loading || disabled || opening}
        onClick={() => {
          setCursor({ checkpoint_after: "", review_after: "" });
          setRefresh((value) => value + 1);
        }}
      >
        Refresh attention list
      </button>
    </section>
  );
}

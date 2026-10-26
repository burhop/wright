import { useCallback, useEffect, useRef, useState } from "react";
import type { McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";
import { NativeFileUpload } from "./NativeFileUpload";
import {
  captureUiReview,
  uiReviewFile,
  type ReviewEvent,
  type ReviewLocation,
  type UiReview,
} from "./native-ui-review";

export function NativeUiReview({
  root,
  host,
  location,
  workspace,
  events,
  call,
  onSaved,
  requestReview,
}: {
  root: () => HTMLElement;
  host: () => McpUiHostContext | undefined;
  location: () => ReviewLocation;
  workspace: () => DesktopWorkspace | undefined;
  events: readonly ReviewEvent[];
  call: HomeCall;
  onSaved?: (scope: DesktopWorkspace, path: string) => void;
  requestReview?: (
    scope: DesktopWorkspace,
    path: string,
  ) => Promise<"sent" | "unsupported">;
}) {
  const [report, setReport] = useState<UiReview>();
  const [scope, setScope] = useState<DesktopWorkspace>();
  const [comment, setComment] = useState("");
  const [picking, setPicking] = useState(false);
  const [prepared, setPrepared] = useState(false);
  const [saved, setSaved] = useState("");
  const [reviewMessage, setReviewMessage] = useState("");
  const [reviewAttempted, setReviewAttempted] = useState(false);
  const reviewGeneration = useRef(0);
  const reviewSent = useRef(false);
  const entry = useRef<HTMLButtonElement>(null);
  const commentBox = useRef<HTMLTextAreaElement>(null);
  const capture = useCallback(
    (target?: Element) => {
      setReport(captureUiReview(root(), host(), location(), events, target));
      setScope(workspace());
      setPrepared(false);
      setSaved("");
      setReviewMessage("");
      setReviewAttempted(false);
      reviewSent.current = false;
      reviewGeneration.current++;
    },
    [root, host, location, events, workspace],
  );
  useEffect(() => {
    if (report && !picking) commentBox.current?.focus();
  }, [report, picking]);
  useEffect(() => {
    if (!picking) return;
    const surface = root();
    const pick = (event: MouseEvent) => {
      if (!(event.target instanceof Element)) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      capture(
        event.target.closest("button,input,select,textarea,[role=tab]") ??
          event.target,
      );
      setPicking(false);
    };
    const cancel = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setPicking(false);
      }
    };
    surface.addEventListener("click", pick, true);
    document.addEventListener("keydown", cancel, true);
    return () => {
      surface.removeEventListener("click", pick, true);
      document.removeEventListener("keydown", cancel, true);
    };
  }, [capture, picking, root]);
  return (
    <aside className="native-ui-review" aria-label="Wright UI feedback">
      <button
        ref={entry}
        onClick={() => {
          setComment("");
          capture();
        }}
      >
        Report UI problem
      </button>
      {picking && (
        <span role="status">
          Click an element in Wright; its normal action is paused. Escape
          cancels.
        </span>
      )}
      {report && !picking && (
        <section
          className="native-ui-review__form"
          aria-label="UI problem report"
        >
          <h2>What is confusing or looks wrong?</h2>
          <p>
            Send this panel’s layout and navigation to the tester. No screenshot
            or form contents are captured. Keep secrets out of your comment.
          </p>
          <label>
            Problem description
            <textarea
              ref={commentBox}
              maxLength={500}
              value={comment}
              disabled={prepared}
              onChange={(event) => setComment(event.target.value)}
            />
          </label>
          <small>
            {report.viewport.width} × {report.viewport.height} ·{" "}
            {report.controls.length} measured controls
            {report.selected_element
              ? ` · selected ${report.selected_element.tag}`
              : ""}
          </small>
          {!prepared && (
            <div>
              <button onClick={() => setPicking(true)}>
                Point to an element
              </button>
            </div>
          )}
          {!scope && (
            <p role="status">
              Choose an available workspace before saving a report.
            </p>
          )}
          {scope && !saved && (
            <NativeFileUpload
              key={report.captured_at}
              call={call}
              workspace={scope}
              preparedFile={() => {
                const file = uiReviewFile(report, comment);
                setPrepared(true);
                return file;
              }}
              actionLabel="Save UI report"
              help="Only this report is saved."
              onUploaded={(path) => {
                setSaved(path);
                onSaved?.(scope, path);
              }}
            />
          )}
          {saved && (
            <>
              <p role="status">
                Report saved for the tester. No copying between chats needed.
              </p>
              {requestReview && scope && (
                <button
                  disabled={reviewAttempted}
                  onClick={async () => {
                    if (reviewSent.current) return;
                    reviewSent.current = true;
                    setReviewAttempted(true);
                    const generation = reviewGeneration.current;
                    try {
                      const result = await requestReview(scope, saved);
                      if (generation === reviewGeneration.current)
                        setReviewMessage(
                          result === "sent"
                            ? "Review request sent to this conversation."
                            : "This host does not support panel-to-chat messages. The report remains saved for the tester.",
                        );
                    } catch {
                      if (generation === reviewGeneration.current)
                        setReviewMessage(
                          "Chat delivery is unconfirmed. The report remains saved; no message was repeated.",
                        );
                    }
                  }}
                >
                  Ask chat to review
                </button>
              )}
              {reviewMessage && <p role="status">{reviewMessage}</p>}
              <details>
                <summary>Report details</summary>
                <code>{saved}</code>
              </details>
            </>
          )}
          <button
            onClick={() => {
              setReport(undefined);
              reviewGeneration.current++;
              setPicking(false);
              entry.current?.focus();
            }}
          >
            Close report
          </button>
        </section>
      )}
    </aside>
  );
}

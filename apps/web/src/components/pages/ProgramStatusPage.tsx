import { useEffect, useRef, useState } from "react";
import {
  fetchProgramStatus,
  fetchProgramStatusPublisher,
  ProgramStatusServiceError,
  type ProgramStatusBundle,
  type ProgramStatusPublisher,
} from "../../services/program-status";
import { AtAGlanceSummary } from "../program-status/AtAGlanceSummary";
import { RefreshState } from "../program-status/RefreshState";
import { ProgramHistory } from "../program-status/ProgramHistory";
import { WorkProgress } from "../program-status/WorkProgress";
import { ActiveAssignments } from "../program-status/ActiveAssignments";
import { UseCaseFunnels } from "../program-status/UseCaseFunnels";
import { DeliveryLanes } from "../program-status/DeliveryLanes";

export function ProgramStatusPage() {
  const [bundle, setBundle] = useState<ProgramStatusBundle | null>(null);
  const [publisher, setPublisher] = useState<ProgramStatusPublisher | null>(
    null,
  );
  const [viewState, setViewState] = useState<
    "loading" | "current" | "stale" | "unavailable"
  >("loading");
  const [message, setMessage] = useState<string | null>(null);
  const etag = useRef<string | undefined>(undefined);
  const hasBundle = useRef(false);

  useEffect(() => {
    let active = true;
    let timer: number | undefined;
    let controller: AbortController | undefined;
    const poll = async () => {
      controller = new AbortController();
      try {
        const [result, publisherResult] = await Promise.allSettled([
          fetchProgramStatus(etag.current, controller.signal),
          fetchProgramStatusPublisher(controller.signal),
        ]);
        if (!active) return;
        if (publisherResult.status === "fulfilled")
          setPublisher(publisherResult.value);
        if (result.status === "rejected") throw result.reason;
        if (result.value.status === 200 && result.value.bundle) {
          setBundle(result.value.bundle);
          hasBundle.current = true;
          etag.current = result.value.etag ?? undefined;
        }
        setViewState("current");
        setMessage(null);
      } catch (error) {
        if (!active) return;
        setViewState((current) =>
          hasBundle.current || current === "current" || current === "stale"
            ? "stale"
            : "unavailable",
        );
        setMessage(
          error instanceof ProgramStatusServiceError
            ? `${error.detail.error_code}: ${error.detail.recovery_class}`
            : "Refresh failed; inspect the local Wright API.",
        );
      } finally {
        if (active) timer = window.setTimeout(poll, 5000);
      }
    };
    void poll();
    return () => {
      active = false;
      if (timer !== undefined) window.clearTimeout(timer);
      controller?.abort();
    };
  }, []);

  return (
    <main
      data-testid="page-program-status"
      className="animate-fade-in-up"
      style={{
        maxWidth: "1400px",
        margin: "0 auto",
        padding: "var(--space-lg)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-lg)",
      }}
    >
      <header
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          gap: "var(--space-md)",
          alignItems: "end",
        }}
      >
        <div>
          <p
            style={{
              margin: 0,
              color: "var(--color-secondary)",
              textTransform: "uppercase",
              letterSpacing: ".08em",
            }}
          >
            Engineering Process Platform
          </p>
          <h1 style={{ margin: "4px 0" }}>Program status</h1>
          <p style={{ margin: 0, color: "var(--color-secondary)" }}>
            A read-only view of committed, validated evidence.
          </p>
        </div>
        <RefreshState
          state={viewState}
          generatedAt={bundle?.generated_at}
          publisher={publisher}
          message={message}
        />
      </header>

      {bundle ? (
        <>
          <AtAGlanceSummary bundle={bundle} />
          <WorkProgress work={bundle.supplement.work} />
          <ActiveAssignments
            assignments={bundle.supplement.work.active_assignments}
          />
          <UseCaseFunnels supplement={bundle.supplement} />
          <DeliveryLanes lanes={bundle.supplement.work.lanes} />
          <section aria-labelledby="readiness-heading">
            <h2 id="readiness-heading">Independent readiness areas</h2>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
                gap: "var(--space-md)",
              }}
            >
              {Object.entries(
                (bundle.dashboard.areas ?? {}) as Record<
                  string,
                  Record<string, unknown>
                >,
              ).map(([id, area]) => (
                <article
                  key={id}
                  style={{
                    border: "1px solid var(--color-border)",
                    borderRadius: "12px",
                    padding: "var(--space-md)",
                  }}
                >
                  <h3 style={{ marginTop: 0 }}>{id.replaceAll("_", " ")}</h3>
                  <strong>{String(area.status ?? "unavailable")}</strong>
                  <p>
                    {String(area.passed_gates ?? 0)}/
                    {String(area.required_gates ?? 0)} gates passed
                  </p>
                </article>
              ))}
            </div>
          </section>
          <ProgramHistory history={bundle.supplement.history} />
          <details>
            <summary>Evidence identity and limitations</summary>
            <dl>
              <dt>Commit</dt>
              <dd>
                <code>{bundle.source.commit}</code>
              </dd>
              <dt>Tree</dt>
              <dd>
                <code>{bundle.source.tree}</code>
              </dd>
              <dt>Program tree</dt>
              <dd>
                <code>{bundle.source.program_tree}</code>
              </dd>
              <dt>Validation transition</dt>
              <dd>{bundle.source.validation_transition}</dd>
              <dt>Evidence index</dt>
              <dd>{bundle.supplement.evidence_index.length} bounded records</dd>
            </dl>
          </details>
        </>
      ) : (
        <section
          aria-labelledby="unavailable-heading"
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: "12px",
            padding: "var(--space-lg)",
          }}
        >
          <h2 id="unavailable-heading">
            No validated program-status bundle is available yet
          </h2>
          <p>
            {message ??
              "The publisher must install one exact committed bundle before this page can show status."}
          </p>
          <p>
            The page will retry automatically every five seconds and will not
            invent readiness or progress.
          </p>
        </section>
      )}
    </main>
  );
}

export default ProgramStatusPage;

import { useEffect, useRef, useState } from "react";
import { MarkdownDocument } from "./documents";

/** JSON recognition is only a presentation hint. The scoped backend resolves the report. */
export function isAssessmentRecord(value: unknown): boolean {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  return record.schema_version === "wright.process-validation/1" &&
    typeof record.id === "string" && typeof record.attempt_id === "string" &&
    !!record.request && !!record.profile && !!record.summary && Array.isArray(record.checks);
}

export function AssessmentReportViewer({
  blob, source, readReport, onReady,
}: {
  blob: Blob;
  source: string;
  readReport?: (signal: AbortSignal) => Promise<Blob>;
  onReady?: () => void;
}) {
  const port = useRef(readReport);
  port.current = readReport;
  const ready = useRef(onReady);
  ready.current = onReady;
  const notified = useRef<Blob | undefined>(undefined);
  const available = Boolean(readReport);
  const [state, setState] = useState<{ blob: Blob; text?: string; error?: string }>();
  useEffect(() => {
    const control = new AbortController();
    let active = true;
    setState(undefined);
    void (async () => {
      if (!port.current) throw new Error("Reader unavailable");
      const report = await port.current(control.signal);
      if (report.type !== "text/markdown" || !report.size || report.size > 2 * 1024 * 1024)
        throw new Error("Unsupported report");
      const text = await report.text();
      if (active) setState({ blob, text });
    })().catch(() => {
      if (active) setState({ blob, error: "The readable assessment is unavailable. The exact recorded file is still available below and through Download exact file." });
    });
    return () => { active = false; control.abort(); };
  }, [blob, available]);
  useEffect(() => {
    if (state?.blob === blob && notified.current !== blob) {
      notified.current = blob;
      ready.current?.();
    }
  }, [blob, state]);
  const current = state?.blob === blob ? state : undefined;
  return <section aria-label="Engineering assessment">
    {current?.text ? <MarkdownDocument text={current.text} />
      : <p role="status">{current?.error || "Opening the recorded assessment…"}</p>}
    <details>
      <summary>Exact assessment record</summary>
      {blob.size <= 1024 * 1024 ? <pre className="wp-text">{source}</pre>
        : <p>The complete record exceeds the text preview limit. Use Download exact file.</p>}
    </details>
  </section>;
}

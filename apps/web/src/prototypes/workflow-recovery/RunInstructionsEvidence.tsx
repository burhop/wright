import { useState } from "react";
import { workspaceService } from "../../services/workspace-service";

type Entry = Record<string, unknown>;
const object = (value: unknown): Entry | null =>
  value && typeof value === "object" && !Array.isArray(value)
    ? (value as Entry)
    : null;
const list = (value: unknown): Entry[] =>
  Array.isArray(value)
    ? value.flatMap((item) => (object(item) ? [object(item)!] : []))
    : [];
const display = (value: unknown) =>
  value === undefined || value === null
    ? ""
    : typeof value === "string"
      ? value
      : JSON.stringify(value);

/** Inspect recorded bytes only. Missing historic evidence is never reconstructed. */
export function recordedInstructionsEvidence(record: unknown) {
  const root = object(record);
  if (!root) throw new Error("The saved run record must be an object.");
  const events = list(root.events);
  const steps = [...list(root.steps), ...list(object(root.result)?.steps)];
  const instructions: Entry[] = [];
  const assumptions: Entry[] = [];
  const invocations: Entry[] = [];
  const append = (owner: Entry) => {
    const resolved = object(owner.instructions);
    if (resolved && typeof resolved.text === "string")
      instructions.push({
        task_id: owner.task_id,
        task_title: owner.task_title,
        ...resolved,
      });
    for (const assumption of list(owner.assumptions))
      assumptions.push({
        task_id: owner.task_id,
        task_title: owner.task_title,
        ...assumption,
      });
  };
  for (const event of events) {
    if (
      event.kind === "instructions_resolved" ||
      event.kind === "step_started" ||
      event.kind === "step_completed"
    )
      append(event);
    if (event.kind === "assumptions_recorded") append(event);
    if (event.kind === "model_invocation" && object(event.invocation))
      invocations.push({
        task_id: event.task_id,
        task_title: event.task_title,
        ...object(event.invocation),
      });
    if (event.kind === "model_invocation_result") {
      for (const invocation of list(event.invocations))
        invocations.push({
          task_id: event.task_id,
          task_title: event.task_title,
          ...invocation,
        });
    }
  }
  for (const step of steps) append(step);
  append(root);
  const distinct = (items: Entry[]) => [
    ...new Map(items.map((item) => [JSON.stringify(item), item])).values(),
  ];
  return {
    instructions: distinct(instructions),
    assumptions: distinct(assumptions),
    invocations: distinct(invocations),
  };
}

type EvidenceProps = {
  sessionId: string;
  runLogPath: string;
  onOpenFile?: (path: string) => void;
};

export function RunInstructionsEvidence(props: EvidenceProps) {
  return (
    <RecordedRunInstructionsEvidence
      key={`${props.sessionId}\u0000${props.runLogPath}`}
      {...props}
    />
  );
}

function RecordedRunInstructionsEvidence({
  sessionId,
  runLogPath,
  onOpenFile,
}: EvidenceProps) {
  const [evidence, setEvidence] = useState<ReturnType<
    typeof recordedInstructionsEvidence
  > | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const load = async () => {
    setBusy(true);
    setError("");
    try {
      const text = await workspaceService.getFileContentText(
        sessionId,
        runLogPath,
      );
      if (new TextEncoder().encode(text).length > 8 * 1024 * 1024)
        throw new Error(
          "This record is too large for inline inspection. Open the saved run log.",
        );
      setEvidence(recordedInstructionsEvidence(JSON.parse(text)));
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Could not load recorded instruction evidence.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <details
      className="recovery-technical-details wright-instruction-editor"
      data-testid="workflow-run-instruction-evidence"
    >
      <summary data-testid="workflow-run-instruction-evidence-toggle">
        Actual instructions and assumptions
      </summary>
      <p>
        This evidence comes from the exact saved run log. Current workflow
        settings and installation defaults do not replace missing historic
        records.
      </p>
      <button
        type="button"
        className="recovery-button recovery-button--secondary"
        disabled={busy}
        onClick={() => void load()}
        data-testid="workflow-run-instruction-evidence-load"
      >
        {busy
          ? "Loading recorded evidence…"
          : "Load recorded instructions and assumptions"}
      </button>
      {onOpenFile && (
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          onClick={() => onOpenFile(runLogPath)}
          data-testid="workflow-run-instruction-evidence-open"
        >
          Open instruction evidence log
        </button>
      )}
      {error && <p role="alert">{error}</p>}
      {evidence && (
        <>
          <h3>Assumptions</h3>
          {evidence.assumptions.length ? (
            <table>
              <thead>
                <tr>
                  <th>Step</th>
                  <th>Parameter</th>
                  <th>Value / units</th>
                  <th>Rationale</th>
                  <th>Affected outputs</th>
                </tr>
              </thead>
              <tbody>
                {evidence.assumptions.map((entry, i) => (
                  <tr key={i}>
                    <td>{display(entry.task_title ?? entry.task_id)}</td>
                    <td>{display(entry.parameter)}</td>
                    <td>
                      {display(entry.value)} {display(entry.units)}
                    </td>
                    <td>{display(entry.rationale)}</td>
                    <td>{display(entry.affected_outputs)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No assumptions were recorded in this run.</p>
          )}
          <h3>Resolved instructions</h3>
          {evidence.instructions.length ? (
            evidence.instructions.map((entry, i) => (
              <details key={i}>
                <summary data-testid={`workflow-run-instructions-${i + 1}`}>
                  {display(entry.task_title ?? entry.task_id ?? entry.role)} ·{" "}
                  {display(entry.role)}
                </summary>
                <p>
                  Origins: {display(entry.origins)} · Policy:{" "}
                  {display(entry.assumption_policy)}
                </p>
                <p>
                  Collection SHA-256: {display(entry.instruction_set_digest)} ·
                  Text SHA-256: {display(entry.text_digest)}
                </p>
                <textarea
                  aria-label={`Recorded instruction text ${i + 1}`}
                  data-testid={`workflow-run-instruction-text-${i + 1}`}
                  rows={8}
                  value={String(entry.text)}
                  readOnly
                />
              </details>
            ))
          ) : (
            <p>
              Resolved instruction text was not recorded for this historic run.
              Its instructions cannot be inferred from current defaults.
            </p>
          )}
          <h3>Actual model requests</h3>
          {evidence.invocations.length ? (
            evidence.invocations.map((entry, i) => (
              <details key={i}>
                <summary data-testid={`workflow-run-invocation-${i + 1}`}>
                  {display(entry.task_title ?? entry.task_id)} ·{" "}
                  {display(entry.operation)} · {display(entry.request_digest)}
                </summary>
                <pre>{JSON.stringify(entry, null, 2)}</pre>
              </details>
            ))
          ) : (
            <p>
              No actual model request records are available in this saved run.
            </p>
          )}
        </>
      )}
    </details>
  );
}

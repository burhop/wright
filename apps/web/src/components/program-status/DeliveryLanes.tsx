import type { ProgramStatusBundle } from "../../services/program-status";

function text(row: Record<string, unknown>, key: string): string | null {
  return typeof row[key] === "string" ? row[key] : null;
}

export function DeliveryLanes({
  lanes,
}: {
  lanes: ProgramStatusBundle["supplement"]["work"]["lanes"];
}) {
  return (
    <section
      aria-labelledby="delivery-lanes-heading"
      data-testid="delivery-lanes"
    >
      <h2 id="delivery-lanes-heading">Delivery lanes</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "var(--space-md)",
        }}
      >
        {lanes.map((lane, index) => {
          const kind = text(lane, "kind") ?? `unavailable-${index}`;
          const next =
            typeof lane.next_action === "object" && lane.next_action !== null
              ? (lane.next_action as Record<string, unknown>)
              : {};
          return (
            <article
              key={kind}
              style={{
                border: "1px solid var(--color-border)",
                borderRadius: 12,
                padding: "var(--space-md)",
              }}
            >
              <h3>{kind.replaceAll("_", " ")}</h3>
              <p>
                <strong>Branch:</strong>{" "}
                <code>{text(lane, "branch") ?? "Unavailable"}</code>
              </p>
              <p>
                <strong>Milestone:</strong>{" "}
                {text(lane, "milestone") ?? "Unavailable"}
              </p>
              <p>
                <strong>Latest evidence-backed progress:</strong>{" "}
                {text(lane, "latest_capability") ?? "Unavailable"}
              </p>
              <p>
                <strong>Blocker:</strong>{" "}
                {text(lane, "blocker") ?? "None recorded"}
              </p>
              <p>
                <strong>Next action:</strong>{" "}
                {text(next, "label") ?? "Unavailable"}
              </p>
              <p>
                <small>
                  Observed{" "}
                  {text(lane, "observed_at")
                    ? new Date(text(lane, "observed_at")!).toLocaleString()
                    : "Unavailable"}
                </small>
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

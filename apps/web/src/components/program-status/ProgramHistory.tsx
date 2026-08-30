import type {
  ProgramStatusSeries,
  ProgramStatusObservation,
} from "../../services/program-status";
import { PlotlyRenderer } from "../../services/surfaces/renderers/plotly-renderer";

function formatValue(value: number, denominator: number | null): string {
  return denominator === null ? String(value) : `${value}/${denominator}`;
}

function HistoryTable({ series }: { series: ProgramStatusSeries }) {
  return (
    <table aria-label={`${series.label} exact committed checkpoints`}>
      <thead>
        <tr>
          <th scope="col">Time</th>
          <th scope="col">Commit</th>
          <th scope="col">Value</th>
          <th scope="col">Change</th>
        </tr>
      </thead>
      <tbody>
        {series.observations.map((point) => (
          <tr key={`${point.commit}-${point.transition_id ?? "none"}`}>
            <td>{new Date(point.observed_at).toLocaleString()}</td>
            <td>
              <code title={point.commit}>{point.commit.slice(0, 8)}</code>
            </td>
            <td>{formatValue(point.value, point.denominator)}</td>
            <td>{point.change_reason ?? "No recorded change reason"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function plot(series: ProgramStatusSeries) {
  return {
    mediaType: "application/vnd.plotly.v1+json" as const,
    encoding: "json" as const,
    data: {
      data: [
        {
          x: series.observations.map((point) => point.observed_at),
          y: series.observations.map((point) => point.value),
          customdata: series.observations.map((point) => [
            point.commit.slice(0, 8),
            point.change_reason ?? "No recorded change reason",
          ]),
          hovertemplate:
            "%{x}<br>%{y}<br>commit %{customdata[0]}<br>%{customdata[1]}<extra></extra>",
          mode: "lines+markers",
          type: "scatter",
          name: series.label,
        },
      ],
      layout: {
        autosize: true,
        margin: { l: 52, r: 20, t: 24, b: 72 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: "#94a3b8" },
        xaxis: { title: "Exact committed checkpoint time", type: "date" },
        yaxis: { title: series.unit, rangemode: "tozero" },
        showlegend: true,
      },
    },
  };
}

function latestPoint(
  series: ProgramStatusSeries,
): ProgramStatusObservation | null {
  return series.observations.at(-1) ?? null;
}

export function ProgramHistory({
  history,
}: {
  history: ProgramStatusSeries[];
}) {
  const visible = history.filter(
    (series) =>
      series.availability === "available" && series.observations.length > 0,
  );
  return (
    <section
      aria-labelledby="program-history-heading"
      data-testid="program-history"
    >
      <h2 id="program-history-heading">Verified progress over time</h2>
      <p style={{ color: "var(--color-secondary)" }}>
        Exact committed checkpoints only. Task trends describe registered scope,
        not total customer-product completion.
      </p>
      {visible.length === 0 ? (
        <p role="status">Historical committed observations are unavailable.</p>
      ) : (
        <div style={{ display: "grid", gap: "var(--space-lg)" }}>
          {visible.map((series) => {
            const latest = latestPoint(series);
            return (
              <article
                key={series.id}
                data-testid={`history-${series.id}`}
                style={{
                  border: "1px solid var(--color-border)",
                  borderRadius: 12,
                  padding: "var(--space-md)",
                }}
              >
                <h3>{series.label}</h3>
                <p>
                  <strong>Meaning:</strong> {series.decision_use}
                </p>
                <p>
                  <strong>Latest verified change:</strong>{" "}
                  {series.latest_change
                    ? `${series.latest_change.from_value ?? "unavailable"} → ${series.latest_change.to_value}: ${series.latest_change.reason}`
                    : latest
                      ? `Current value ${formatValue(latest.value, latest.denominator)}; no change event is recorded.`
                      : "Unavailable"}
                </p>
                <p>
                  <strong>Current limitation:</strong>{" "}
                  {series.current_limitation}
                </p>
                <p>
                  <strong>Next evidence-backed action:</strong>{" "}
                  {series.next_action.label}
                </p>
                <PlotlyRenderer
                  representation={plot(series)}
                  description={`${series.label} over exact committed checkpoints in ${series.unit}.`}
                  fallback={
                    <p>
                      Loading the interactive graph. The exact table remains
                      available below.
                    </p>
                  }
                />
                <details>
                  <summary>Exact checkpoint table</summary>
                  <HistoryTable series={series} />
                </details>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

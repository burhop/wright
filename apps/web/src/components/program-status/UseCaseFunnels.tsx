import type { ProgramStatusBundle } from "../../services/program-status";

export function UseCaseFunnels({
  supplement,
}: {
  supplement: ProgramStatusBundle["supplement"];
}) {
  const all = supplement.use_cases.all;
  const process = supplement.use_cases.process_100;
  return (
    <section
      aria-labelledby="use-case-funnels-heading"
      data-testid="use-case-funnels"
    >
      <h2 id="use-case-funnels-heading">Customer capability funnel</h2>
      <p>
        The proposed story catalog, governed use cases, implemented outcomes,
        tests, and benchmark qualification are separate populations.
      </p>
      <div style={{ overflowX: "auto" }}>
        <table aria-label="All governed use cases and 100-process subset">
          <thead>
            <tr>
              <th scope="col">Population</th>
              <th scope="col">Defined / total</th>
              <th scope="col">In progress</th>
              <th scope="col">Implemented</th>
              <th scope="col">Tested</th>
              <th scope="col">Independently verified</th>
              <th scope="col">Qualified</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">All governed use cases</th>
              <td>{all.total}</td>
              <td>{all.in_progress}</td>
              <td>{all.implemented}</td>
              <td>Unavailable as an aggregate</td>
              <td>{all.independently_verified}</td>
              <td>Not applicable</td>
            </tr>
            <tr>
              <th scope="row">100-process subset</th>
              <td>{process.defined}/100</td>
              <td>{process.in_progress}</td>
              <td>{process.implemented}</td>
              <td>{process.tested}</td>
              <td>{process.independently_verified}</td>
              <td>{process.benchmark_qualified}/100</td>
            </tr>
            <tr>
              <th scope="row">Proposed customer stories</th>
              <td>{supplement.customer_catalog.proposed_total} proposed</td>
              <td>Not counted</td>
              <td>Not counted</td>
              <td>Not counted</td>
              <td>Not counted</td>
              <td>Not counted</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p>
        <strong>Benchmark state:</strong>{" "}
        {supplement.benchmark_context.hold_reason ??
          supplement.benchmark_context.phase}
      </p>
    </section>
  );
}

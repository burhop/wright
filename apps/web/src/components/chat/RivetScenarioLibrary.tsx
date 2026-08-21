import { useCallback, useEffect, useState } from "react";

import {
  workspaceService,
  type EngineeringScenarioEntry,
  type EngineeringScenarioPreflight,
} from "../../services/workspace-service";
import { RivetScenarioReport } from "./RivetScenarioReport";

export function RivetScenarioLibrary({
  sessionId,
  onPrepared,
}: {
  sessionId: string;
  onPrepared: (workflowSlug: string) => void | Promise<void>;
}) {
  const [scenarios, setScenarios] = useState<EngineeringScenarioEntry[]>([]);
  const [preflights, setPreflights] = useState<
    Record<string, EngineeringScenarioPreflight>
  >({});
  const [runs, setRuns] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("Loading deterministic examples...");

  const load = useCallback(async () => {
    try {
      const next = await workspaceService.listEngineeringScenarios();
      setScenarios(next);
      setMessage(
        `${next.length} deterministic engineering scenarios are available.`,
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Engineering scenarios are unavailable.",
      );
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const preflight = async (scenario: EngineeringScenarioEntry) => {
    try {
      const next = await workspaceService.preflightEngineeringScenario(
        sessionId,
        scenario.scenario_id,
      );
      setPreflights((current) => ({
        ...current,
        [scenario.scenario_id]: next,
      }));
      await onPrepared(next.workflow_slug);
      setMessage(
        next.state === "ready"
          ? `Preflight is ready. ${next.workflow_slug} can be started.`
          : `Preflight found ${next.blockers.length} blockers.`,
      );
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Scenario preflight failed.",
      );
    }
  };

  const start = async (
    scenario: EngineeringScenarioEntry,
    exact: EngineeringScenarioPreflight,
  ) => {
    try {
      const result = await workspaceService.startEngineeringScenario(
        sessionId,
        exact,
      );
      setRuns((current) => ({
        ...current,
        [scenario.scenario_id]: result.scenario_run_id,
      }));
      setMessage(`Scenario ${scenario.title} is running.`);
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Scenario could not start.",
      );
    }
  };

  return (
    <section
      aria-labelledby="engineering-scenario-library-title"
      data-testid="engineering-scenario-library"
      style={{ marginTop: "var(--space-lg)" }}
    >
      <h3 id="engineering-scenario-library-title">Engineering scenarios</h3>
      <p>
        Curated Rivet examples call validated workspace capabilities, including
        MCP tools and local engineering models, and check engineering meaning,
        units, provenance, resources, and cleanup. Tier 1 stays local and never
        controls physical equipment.
      </p>
      <p role="status" aria-live="polite">
        {message}
      </p>
      {scenarios.map((scenario) => {
        const exact = preflights[scenario.scenario_id];
        const scenarioRunId = runs[scenario.scenario_id];
        const firstBlocker = exact?.blockers[0];
        const blockerOrigin = firstBlocker
          ? /credential|license|host|tier|resource/i.test(firstBlocker.code)
            ? "optional external prerequisite"
            : "local workspace state"
          : null;
        const nextAction = scenarioRunId
          ? "Review the terminal evidence, cleanup, and recovery below."
          : !exact
            ? "Check and prepare. This is read-only and does not run providers."
            : exact.state !== "ready"
              ? `Resolve the blocker from ${blockerOrigin}, then create a fresh preflight.`
              : "Run the prepared scenario. This starts only the displayed Tier 1 provider fixtures.";
        return (
          <article
            key={scenario.scenario_id}
            data-testid={`engineering-scenario-${scenario.scenario_id}`}
            style={{
              borderTop: "1px solid var(--color-border)",
              marginTop: "var(--space-sm)",
              paddingTop: "var(--space-sm)",
            }}
          >
            <h4>{scenario.title}</h4>
            <p>{scenario.summary}</p>
            <p>
              <strong>{scenario.tier.toUpperCase()}</strong> /{" "}
              {scenario.resource_class} / about{" "}
              {scenario.expected_duration_seconds} seconds
            </p>
            <p>Domains: {scenario.domains.join(", ")}</p>
            <p>
              Optional dependencies:{" "}
              {scenario.tier === "tier1"
                ? "none for the deterministic local run"
                : "shown and guarded during preflight"}
              .
            </p>
            <p>Safety: static engineering evidence; no physical actuation.</p>
            <p data-testid={`scenario-next-action-${scenario.scenario_id}`}>
              <strong>Next action:</strong> {nextAction}
              {firstBlocker ? ` ${firstBlocker.message}` : ""}
            </p>
            <button
              data-testid={`scenario-preflight-${scenario.scenario_id}`}
              type="button"
              onClick={() => void preflight(scenario)}
            >
              Check and prepare
            </button>{" "}
            <button
              data-testid={`scenario-start-${scenario.scenario_id}`}
              type="button"
              disabled={!exact || exact.state !== "ready"}
              onClick={() => (exact ? void start(scenario, exact) : undefined)}
            >
              Run scenario
            </button>
            {exact ? (
              <div
                data-testid={`scenario-preflight-result-${scenario.scenario_id}`}
              >
                <p>
                  Preflight: <strong>{exact.state}</strong>. Prepared workflow:{" "}
                  {exact.workflow_slug}.
                </p>
                {exact.blockers.map((blocker) => (
                  <p key={blocker.code} role="alert">
                    {blocker.message} <strong>Recovery:</strong>{" "}
                    {blocker.recovery}
                  </p>
                ))}
                {exact.capabilities.map((capability) => (
                  <div key={capability.node_id}>
                    <p>
                      {capability.node_id}:{" "}
                      {capability.selected_tool || "not bound"}
                    </p>
                    {capability.provider ? (
                      <p>
                        Provider:{" "}
                        {capability.provider.provider_kind === "mcp"
                          ? "MCP"
                          : "local engineering model"}{" "}
                        / {capability.provider.provider_id} / resource{" "}
                        {capability.provider.resource_class}. Evidence{" "}
                        {capability.provider_evidence_digest || "not recorded"}.
                      </p>
                    ) : (
                      <p>Provider evidence is not ready.</p>
                    )}
                  </div>
                ))}
              </div>
            ) : null}
            {scenarioRunId ? (
              <RivetScenarioReport
                sessionId={sessionId}
                scenarioRunId={scenarioRunId}
              />
            ) : null}
          </article>
        );
      })}
    </section>
  );
}

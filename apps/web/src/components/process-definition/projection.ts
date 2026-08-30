import type {
  ProcessDefinition,
  ProcessDefinitionAction,
  ProcessDefinitionArtifact,
  ProcessDefinitionFeedbackPath,
  ProcessDefinitionGate,
  ProcessDefinitionPhase,
  ProcessDefinitionPort,
} from "../../services/process-definition";

export interface ProcessActionProjection {
  action: ProcessDefinitionAction;
  inputs: ProcessDefinitionPort[];
  outputs: ProcessDefinitionPort[];
  gates: ProcessDefinitionGate[];
  feedbackPaths: ProcessDefinitionFeedbackPath[];
  artifacts: ProcessDefinitionArtifact[];
}

export interface ProcessPhaseProjection {
  phase: ProcessDefinitionPhase;
  actions: ProcessActionProjection[];
}

function required<T>(registry: Map<string, T>, id: string): T {
  const value = registry.get(id);
  if (value === undefined) throw new Error(`PROCESS_REFERENCE_UNRESOLVED:${id}`);
  return value;
}

export function buildProcessProjection(
  definition: ProcessDefinition,
): ProcessPhaseProjection[] {
  const actions = new Map(definition.actions.map((item) => [item.id, item]));
  const ports = new Map(definition.ports.map((item) => [item.id, item]));
  const gates = new Map(definition.gates.map((item) => [item.id, item]));
  const feedback = new Map(
    definition.feedback_paths.map((item) => [item.id, item]),
  );
  const artifacts = new Map(
    definition.artifacts.map((item) => [item.id, item]),
  );

  return definition.phases.map((phase) => ({
    phase,
    actions: phase.action_ids.map((actionId) => {
      const action = required(actions, actionId);
      return {
        action,
        inputs: action.input_port_ids.map((id) => required(ports, id)),
        outputs: action.output_port_ids.map((id) => required(ports, id)),
        gates: action.gate_ids.map((id) => required(gates, id)),
        feedbackPaths: action.feedback_path_ids.map((id) =>
          required(feedback, id),
        ),
        artifacts: action.expected_artifact_ids.map((id) =>
          required(artifacts, id),
        ),
      };
    }),
  }));
}

export function processSemanticIds(definition: ProcessDefinition): string[] {
  return [
    definition.process_id,
    ...definition.phases.map((item) => item.id),
    ...definition.actions.map((item) => item.id),
    ...definition.ports.map((item) => item.id),
    ...definition.gates.map((item) => item.id),
    ...definition.feedback_paths.map((item) => item.id),
    ...definition.artifacts.map((item) => item.id),
  ];
}

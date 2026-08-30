import type {
  ProcessDefinition,
  ProcessDefinitionArtifact,
  ProcessDefinitionFeedbackPath,
  ProcessDefinitionGate,
  ProcessDefinitionPort,
} from "../../services/process-definition";
import { buildProcessProjection } from "./projection";

function EmptyOrList({
  items,
  children,
}: {
  items: { id: string }[];
  children: (item: { id: string }) => React.ReactNode;
}) {
  return items.length === 0 ? (
    <p className="process-definition__none">None declared.</p>
  ) : (
    <ul>{items.map((item) => children(item))}</ul>
  );
}

function PortItem({ port }: { port: ProcessDefinitionPort }) {
  return (
    <li data-semantic-id={port.id}>
      <strong>{port.name}</strong> <code>{port.id}</code>
      <p>
        {port.direction === "input" ? "Input" : "Output"} · {port.value_type}
        {" — "}
        {port.description}
      </p>
      <p>
        Owner: <code>{port.owner_action_id}</code>. Source: {" "}
        {port.source_port_id ? <code>{port.source_port_id}</code> : "None declared."}
      </p>
    </li>
  );
}

function GateItem({ gate }: { gate: ProcessDefinitionGate }) {
  return (
    <li data-semantic-id={gate.id}>
      <strong>{gate.title}</strong> <code>{gate.id}</code>
      <p>{gate.condition}</p>
      <p>
        Pass → <code>{gate.pass_target_id}</code>. Fail → {" "}
        <code>{gate.fail_target_id}</code>.
      </p>
    </li>
  );
}

function FeedbackItem({ path }: { path: ProcessDefinitionFeedbackPath }) {
  return (
    <li data-semantic-id={path.id}>
      <strong>Feedback →</strong> <code>{path.id}</code>
      <p>
        From <code>{path.from_id}</code> to <code>{path.to_id}</code>: {path.reason}
      </p>
    </li>
  );
}

function ArtifactItem({ artifact }: { artifact: ProcessDefinitionArtifact }) {
  return (
    <li data-semantic-id={artifact.id}>
      <strong>{artifact.name}</strong> <code>{artifact.id}</code>
      <p>
        Expected artifact · {artifact.artifact_type} — {artifact.purpose}
      </p>
      <p>
        Produced by <code>{artifact.produced_by_action_id}</code>.
      </p>
    </li>
  );
}

export function ProcessDefinitionText({
  definition,
}: {
  definition: ProcessDefinition;
}) {
  const phases = buildProcessProjection(definition);

  return (
    <section
      className="process-definition__projection process-definition__text"
      data-testid="process-definition-text"
      aria-labelledby="process-definition-text-heading"
    >
      <header data-semantic-id={definition.process_id}>
        <p className="process-definition__eyebrow">Complete text authority</p>
        <h2 id="process-definition-text-heading">Process details</h2>
        <p>
          Process ID: <code>{definition.process_id}</code>
        </p>
        <p>{definition.purpose}</p>
      </header>

      {phases.map(({ phase, actions }, phaseIndex) => (
        <section
          className="process-definition__phase"
          data-semantic-id={phase.id}
          aria-labelledby={`text-phase-${phase.id}`}
          key={phase.id}
        >
          <p className="process-definition__step">Phase {phaseIndex + 1}</p>
          <h3 id={`text-phase-${phase.id}`}>
            {phase.title} <code>{phase.id}</code>
          </h3>
          <p>{phase.purpose}</p>

          {actions.map(
            ({ action, inputs, outputs, gates, feedbackPaths, artifacts }) => (
              <article
                className="process-definition__action"
                data-semantic-id={action.id}
                key={action.id}
              >
                <h4>
                  {action.title} <code>{action.id}</code>
                </h4>
                <p>{action.purpose}</p>

                <section aria-label={`${action.title} inputs`}>
                  <h5>Inputs</h5>
                  <EmptyOrList items={inputs}>
                    {(item) => <PortItem key={item.id} port={item as ProcessDefinitionPort} />}
                  </EmptyOrList>
                </section>
                <section aria-label={`${action.title} outputs`}>
                  <h5>Outputs</h5>
                  <EmptyOrList items={outputs}>
                    {(item) => <PortItem key={item.id} port={item as ProcessDefinitionPort} />}
                  </EmptyOrList>
                </section>
                <section aria-label={`${action.title} gates`}>
                  <h5>Gates</h5>
                  <EmptyOrList items={gates}>
                    {(item) => <GateItem key={item.id} gate={item as ProcessDefinitionGate} />}
                  </EmptyOrList>
                </section>
                <section aria-label={`${action.title} feedback paths`}>
                  <h5>Feedback paths</h5>
                  <EmptyOrList items={feedbackPaths}>
                    {(item) => (
                      <FeedbackItem
                        key={item.id}
                        path={item as ProcessDefinitionFeedbackPath}
                      />
                    )}
                  </EmptyOrList>
                </section>
                <section aria-label={`${action.title} expected artifacts`}>
                  <h5>Expected artifacts</h5>
                  <EmptyOrList items={artifacts}>
                    {(item) => (
                      <ArtifactItem
                        key={item.id}
                        artifact={item as ProcessDefinitionArtifact}
                      />
                    )}
                  </EmptyOrList>
                </section>
              </article>
            ),
          )}
        </section>
      ))}
    </section>
  );
}

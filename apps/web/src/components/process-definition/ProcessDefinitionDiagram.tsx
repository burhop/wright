import type { ProcessDefinition } from "../../services/process-definition";
import { buildProcessProjection } from "./projection";

export function ProcessDefinitionDiagram({
  definition,
}: {
  definition: ProcessDefinition;
}) {
  const phases = buildProcessProjection(definition);

  return (
    <figure
      className="process-definition__projection process-definition__diagram"
      data-testid="process-definition-diagram"
      aria-labelledby="process-definition-diagram-heading"
    >
      <figcaption data-semantic-id={definition.process_id}>
        <p className="process-definition__eyebrow">Matching derived diagram</p>
        <h2 id="process-definition-diagram-heading">Process flow</h2>
        <p>
          Process ID: <code>{definition.process_id}</code>
        </p>
        <p>
          Read top to bottom. Words and arrows carry every relationship; color
          is supplementary.
        </p>
      </figcaption>

      <ol className="process-definition__flow">
        {phases.map(({ phase, actions }, phaseIndex) => (
          <li className="process-definition__phase-card" key={phase.id}>
            <section
              data-semantic-id={phase.id}
              aria-labelledby={`diagram-phase-${phase.id}`}
            >
              <p className="process-definition__step">Phase {phaseIndex + 1}</p>
              <h3 id={`diagram-phase-${phase.id}`}>
                {phase.title} <code>{phase.id}</code>
              </h3>
              <p>{phase.purpose}</p>
            </section>

            <ol className="process-definition__action-flow">
              {actions.map(
                ({
                  action,
                  inputs,
                  outputs,
                  gates,
                  feedbackPaths,
                  artifacts,
                }) => (
                  <li
                    className="process-definition__action-card"
                    key={action.id}
                  >
                    <section data-semantic-id={action.id}>
                      <h4>
                        {action.title} <code>{action.id}</code>
                      </h4>
                      <p>{action.purpose}</p>
                    </section>

                    <div className="process-definition__diagram-groups">
                      <section aria-label={`${action.title} diagram inputs`}>
                        <h5>Inputs</h5>
                        {inputs.length === 0 ? (
                          <p>None declared.</p>
                        ) : (
                          inputs.map((port) => (
                            <article data-semantic-id={port.id} key={port.id}>
                              <strong>Input:</strong> {port.name}{" "}
                              <code>{port.id}</code>
                              <p>
                                {port.value_type}; source{" "}
                                {port.source_port_id ?? "None declared."}
                              </p>
                            </article>
                          ))
                        )}
                      </section>
                      <section aria-label={`${action.title} diagram outputs`}>
                        <h5>Outputs</h5>
                        {outputs.length === 0 ? (
                          <p>None declared.</p>
                        ) : (
                          outputs.map((port) => (
                            <article data-semantic-id={port.id} key={port.id}>
                              <strong>Output:</strong> {port.name}{" "}
                              <code>{port.id}</code>
                              <p>{port.value_type}</p>
                            </article>
                          ))
                        )}
                      </section>
                      <section aria-label={`${action.title} diagram gates`}>
                        <h5>Gates</h5>
                        {gates.length === 0 ? (
                          <p>None declared.</p>
                        ) : (
                          gates.map((gate) => (
                            <article data-semantic-id={gate.id} key={gate.id}>
                              <strong>{gate.title}</strong>{" "}
                              <code>{gate.id}</code>
                              <p>{gate.condition}</p>
                              <p>
                                Pass → {gate.pass_target_id}; Fail →{" "}
                                {gate.fail_target_id}
                              </p>
                            </article>
                          ))
                        )}
                      </section>
                      <section aria-label={`${action.title} diagram feedback`}>
                        <h5>Feedback paths</h5>
                        {feedbackPaths.length === 0 ? (
                          <p>None declared.</p>
                        ) : (
                          feedbackPaths.map((path) => (
                            <article data-semantic-id={path.id} key={path.id}>
                              <strong>Feedback →</strong> <code>{path.id}</code>
                              <p>
                                {path.from_id} → {path.to_id}: {path.reason}
                              </p>
                            </article>
                          ))
                        )}
                      </section>
                      <section aria-label={`${action.title} diagram artifacts`}>
                        <h5>Expected artifacts</h5>
                        {artifacts.length === 0 ? (
                          <p>None declared.</p>
                        ) : (
                          artifacts.map((artifact) => (
                            <article
                              data-semantic-id={artifact.id}
                              key={artifact.id}
                            >
                              <strong>Expected artifact:</strong>{" "}
                              {artifact.name} <code>{artifact.id}</code>
                              <p>{artifact.artifact_type}</p>
                            </article>
                          ))
                        )}
                      </section>
                    </div>
                  </li>
                ),
              )}
            </ol>
          </li>
        ))}
      </ol>
    </figure>
  );
}

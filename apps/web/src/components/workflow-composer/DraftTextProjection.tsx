import type { DraftProjection } from "./draft-projection";

interface DraftTextProjectionProps {
  readonly projection: Readonly<DraftProjection>;
}

function Id({ children }: { readonly children: string }): React.ReactNode {
  return <code>{children}</code>;
}

function IdList({ ids }: { readonly ids: readonly string[] }): React.ReactNode {
  return ids.length > 0 ? (
    ids.map((id, index) => (
      <span key={id}>
        {index > 0 ? ", " : ""}
        <Id>{id}</Id>
      </span>
    ))
  ) : (
    <span className="workflow-composer__none">None declared</span>
  );
}

export function DraftTextProjection({
  projection,
}: DraftTextProjectionProps): React.ReactNode {
  return (
    <article
      className="workflow-composer__text"
      data-testid="workflow-composer-text"
    >
      <header>
        <p className="workflow-composer__eyebrow">Canonical text projection</p>
        <h2>{projection.title}</h2>
        <p>{projection.purpose}</p>
      </header>

      {projection.phases.map((phase) => (
        <section
          className="workflow-composer__text-phase"
          data-semantic-id={phase.semanticId}
          key={phase.semanticId}
        >
          <div>
            <p className="workflow-composer__kind">Phase {phase.order + 1}</p>
            <h3>{phase.name}</h3>
            <Id>{phase.semanticId}</Id>
            <p>{phase.purpose}</p>
            <p>
              <strong>Blocks:</strong> <IdList ids={phase.block_ids} />
            </p>
          </div>

          {phase.blocks.map((block) => (
            <article
              className="workflow-composer__text-block"
              data-semantic-id={block.semanticId}
              key={block.semanticId}
            >
              <p className="workflow-composer__kind">{block.role} block</p>
              <h4>{block.title}</h4>
              <Id>{block.semanticId}</Id>
              <p>{block.purpose}</p>
              <dl>
                <dt>Phase</dt>
                <dd>
                  <Id>{block.phase_id}</Id>
                </dd>
                <dt>Input ports</dt>
                <dd>
                  <IdList ids={block.input_port_ids} />
                </dd>
                <dt>Output ports</dt>
                <dd>
                  <IdList ids={block.output_port_ids} />
                </dd>
                <dt>Gates</dt>
                <dd>
                  <IdList ids={block.gate_ids} />
                </dd>
                <dt>Intended artifacts</dt>
                <dd>
                  <IdList ids={block.intended_artifact_ids} />
                </dd>
              </dl>

              {[...block.inputs, ...block.outputs].map((port) => (
                <section
                  className="workflow-composer__relationship"
                  data-semantic-id={port.semanticId}
                  key={port.semanticId}
                >
                  <strong>
                    {port.direction === "input" ? "Input" : "Output"}:{" "}
                    {port.name}
                  </strong>
                  <Id>{port.semanticId}</Id>
                  <span>
                    Owner <Id>{port.owner_block_id}</Id> · Type{" "}
                    <Id>{port.value_type_id}</Id> · {port.cardinality}
                    {port.required ? " · required" : " · optional"}
                  </span>
                </section>
              ))}

              {block.gates.map((gate) => (
                <section
                  className="workflow-composer__relationship"
                  data-semantic-id={gate.semanticId}
                  key={gate.semanticId}
                >
                  <strong>Gate</strong> <Id>{gate.semanticId}</Id>
                  <span>{gate.condition}</span>
                  <span>
                    Owner <Id>{gate.owner_block_id}</Id> · Proceed →{" "}
                    <Id>{gate.proceed_target_block_id}</Id> · Revise →{" "}
                    <Id>{gate.revise_target_block_id}</Id> · Feedback{" "}
                    <Id>{gate.feedback_path_id}</Id>
                  </span>
                </section>
              ))}

              {block.artifacts.map((artifact) => (
                <section
                  className="workflow-composer__relationship"
                  data-semantic-id={artifact.semanticId}
                  key={artifact.semanticId}
                >
                  <strong>Intended artifact: {artifact.title}</strong>{" "}
                  <Id>{artifact.semanticId}</Id>
                  <span>{artifact.description}</span>
                  <span>
                    Type <Id>{artifact.artifact_type_id}</Id> · Produced by{" "}
                    <Id>{artifact.produced_by_block_id}</Id>
                  </span>
                </section>
              ))}
            </article>
          ))}
        </section>
      ))}

      <section className="workflow-composer__text-group">
        <h3>Connections</h3>
        {projection.connections.map((connection) => (
          <p
            className="workflow-composer__relationship"
            data-semantic-id={connection.semanticId}
            key={connection.semanticId}
          >
            <Id>{connection.semanticId}</Id>
            <span>
              <Id>{connection.source_port_id}</Id> →{" "}
              <Id>{connection.target_port_id}</Id>
            </span>
            <span>
              Blocks <Id>{connection.sourceBlockId}</Id> →{" "}
              <Id>{connection.targetBlockId}</Id>
            </span>
          </p>
        ))}
      </section>

      <section className="workflow-composer__text-group">
        <h3>Feedback paths</h3>
        {projection.feedbackPaths.map((feedback) => (
          <p
            className="workflow-composer__relationship"
            data-semantic-id={feedback.semanticId}
            key={feedback.semanticId}
          >
            <Id>{feedback.semanticId}</Id>
            <span>
              <Id>{feedback.from_gate_id}</Id> → <Id>{feedback.to_block_id}</Id>
            </span>
            <span>{feedback.reason}</span>
          </p>
        ))}
      </section>
    </article>
  );
}

import type { ProcessDefinitionEnvelope } from "../../services/process-definition";

export function ProcessDefinitionDetails({
  envelope,
}: {
  envelope: ProcessDefinitionEnvelope;
}) {
  return (
    <details
      className="process-definition__source"
      data-testid="process-definition-source-details"
    >
      <summary data-testid="process-definition-source-toggle">
        Validated source identity
      </summary>
      <p>
        Package-relative identity only; not a filesystem path or external URL.
      </p>
      <dl>
        <dt>Internal logical source</dt>
        <dd>
          <code>{envelope.source_id}</code>
        </dd>
        <dt>Source kind</dt>
        <dd>{envelope.source_kind}</dd>
        <dt>Source available</dt>
        <dd>{envelope.source_available ? "Yes" : "No"}</dd>
        <dt>Schema version</dt>
        <dd>{envelope.definition.schema_version}</dd>
        <dt>Supported schema versions</dt>
        <dd>{envelope.supported_schema_versions.join(", ")}</dd>
        <dt>Revision</dt>
        <dd>{String(envelope.definition.revision)}</dd>
        <dt>Definition content SHA-256</dt>
        <dd>
          <code>{envelope.definition.content_sha256}</code>
        </dd>
        <dt>Source SHA-256</dt>
        <dd>
          <code>{envelope.source_sha256}</code>
        </dd>
        <dt>Envelope ETag</dt>
        <dd>
          <code>{envelope.etag}</code>
        </dd>
      </dl>
    </details>
  );
}

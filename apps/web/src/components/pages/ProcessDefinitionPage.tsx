import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchProcessDefinition,
  PROCESS_DEFINITION_SCHEMA_VERSION,
  PROCESS_DEFINITION_SOURCE_ID,
  ProcessDefinitionDecodeError,
  ProcessDefinitionServiceError,
  type ProcessDefinitionErrorCode,
  type ProcessDefinitionEnvelope,
} from "../../services/process-definition";
import { ProcessDefinitionDetails } from "../process-definition/ProcessDefinitionDetails";
import { ProcessDefinitionDiagram } from "../process-definition/ProcessDefinitionDiagram";
import { ProcessDefinitionLoading } from "../process-definition/ProcessDefinitionLoading";
import { ProcessDefinitionText } from "../process-definition/ProcessDefinitionText";
import "../process-definition/process-definition.css";

type ViewState =
  | { state: "loading" }
  | { state: "ready"; envelope: ProcessDefinitionEnvelope }
  | { state: "failure"; diagnostic: FailureDiagnostic };

interface FailureDiagnostic {
  code: ProcessDefinitionErrorCode;
  title: string;
  explanation: string;
  recovery: string;
  traceId?: string;
  supportedVersions?: readonly string[];
}

const FAILURE_COPY: Readonly<
  Record<
    ProcessDefinitionErrorCode,
    Pick<FailureDiagnostic, "title" | "explanation" | "recovery">
  >
> = {
  PROCESS_DEFINITION_UNAVAILABLE: {
    title: "The validated process definition is unavailable",
    explanation:
      "Wright could not find the one validated local definition required by this page.",
    recovery:
      "Enable the process-definition data or reinstall this Wright build.",
  },
  PROCESS_DEFINITION_IDENTITY_MISMATCH: {
    title: "The process definition identity does not match",
    explanation:
      "Wright rejected content that did not match its validated definition identity.",
    recovery:
      "Reinstall the exact Wright artifact that supplied this process definition.",
  },
  PROCESS_DEFINITION_INVALID: {
    title: "The process definition is invalid",
    explanation:
      "Wright rejected local definition data that did not satisfy the closed process contract.",
    recovery:
      "Replace the local definition with a validated Wright process-definition artifact.",
  },
  PROCESS_DEFINITION_UNSUPPORTED_VERSION: {
    title: "A compatible process definition is required",
    explanation:
      "Wright rejected a process-definition schema version that this build does not support.",
    recovery:
      "Install a compatible Wright version before opening this definition.",
  },
  PROCESS_DEFINITION_READ_FAILED: {
    title: "The process definition could not be read",
    explanation:
      "Wright could not safely read validated local process-definition evidence.",
    recovery:
      "Inspect the configured local Wright data root and service health.",
  },
};

const IDENTITY_DECODE_CODES = new Set([
  "CONTENT_IDENTITY_MISMATCH",
  "ENVELOPE_IDENTITY_MISMATCH",
  "ETAG_IDENTITY_MISMATCH",
  "NOT_MODIFIED_IDENTITY_MISMATCH",
]);

function safeTraceId(value: string): string | undefined {
  return /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(value) &&
    value !== "unavailable"
    ? value
    : undefined;
}

function failureDiagnostic(error: unknown): FailureDiagnostic {
  let code: ProcessDefinitionErrorCode = "PROCESS_DEFINITION_READ_FAILED";
  let traceId: string | undefined;
  let supportedVersions: readonly string[] | undefined;

  if (error instanceof ProcessDefinitionServiceError) {
    code = error.detail.error_code;
    traceId = safeTraceId(error.detail.trace_id);
    supportedVersions = error.detail.supported_schema_versions;
  } else if (error instanceof ProcessDefinitionDecodeError) {
    if (IDENTITY_DECODE_CODES.has(error.code)) {
      code = "PROCESS_DEFINITION_IDENTITY_MISMATCH";
    } else if (
      error.code === "ENUM_INVALID" &&
      error.path === "/definition/schema_version"
    ) {
      code = "PROCESS_DEFINITION_UNSUPPORTED_VERSION";
      supportedVersions = [PROCESS_DEFINITION_SCHEMA_VERSION];
    } else {
      code = "PROCESS_DEFINITION_INVALID";
    }
  }

  return {
    code,
    ...FAILURE_COPY[code],
    ...(traceId === undefined ? {} : { traceId }),
    ...(code !== "PROCESS_DEFINITION_UNSUPPORTED_VERSION"
      ? {}
      : {
          supportedVersions: supportedVersions ?? [
            PROCESS_DEFINITION_SCHEMA_VERSION,
          ],
        }),
  };
}

export function ProcessDefinitionPage() {
  const [view, setView] = useState<ViewState>({ state: "loading" });

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const load = async () => {
      try {
        const result = await fetchProcessDefinition(
          undefined,
          controller.signal,
        );
        if (!active) return;
        if (result.state !== "current") throw new Error("INITIAL_304_INVALID");
        setView({ state: "ready", envelope: result.envelope });
      } catch (error) {
        if (active && !controller.signal.aborted) {
          setView({ state: "failure", diagnostic: failureDiagnostic(error) });
        }
      }
    };
    void load();
    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  return (
    <section
      className="process-definition"
      data-testid="page-process-definition"
      aria-labelledby="process-definition-title"
    >
      <header className="process-definition__header">
        <p className="process-definition__eyebrow">
          Engineering process definition
        </p>
        <h1
          id="process-definition-title"
          data-testid="process-definition-title"
        >
          {view.state === "ready"
            ? view.envelope.definition.title
            : "Product definition process"}
        </h1>
        {view.state === "ready" ? (
          <>
            <p>{view.envelope.definition.purpose}</p>
            <p className="process-definition__version">
              Version {view.envelope.definition.schema_version} · revision{" "}
              {String(view.envelope.definition.revision)}
            </p>
          </>
        ) : null}
      </header>

      {view.state === "loading" ? <ProcessDefinitionLoading /> : null}
      {view.state === "failure" ? (
        <section
          className="process-definition__state"
          data-testid="process-definition-failure"
          role="alert"
          aria-labelledby="process-definition-failure-title"
        >
          <h2 id="process-definition-failure-title">{view.diagnostic.title}</h2>
          <p>{view.diagnostic.explanation}</p>
          <p>Wright did not display partial or unverified process content.</p>
          <dl>
            <dt>Error code</dt>
            <dd data-testid="process-definition-failure-code">
              <code>{view.diagnostic.code}</code>
            </dd>
            <dt>Safe logical source</dt>
            <dd>
              <code>{PROCESS_DEFINITION_SOURCE_ID}</code>
            </dd>
            {view.diagnostic.supportedVersions === undefined ? null : (
              <>
                <dt>Supported schema versions</dt>
                <dd data-testid="process-definition-supported-versions">
                  {view.diagnostic.supportedVersions.join(", ")}
                </dd>
              </>
            )}
            {view.diagnostic.traceId === undefined ? null : (
              <>
                <dt>Support trace</dt>
                <dd data-testid="process-definition-trace-id">
                  <code>{view.diagnostic.traceId}</code>
                </dd>
              </>
            )}
          </dl>
          <p data-testid="process-definition-recovery">
            <strong>Recovery:</strong> {view.diagnostic.recovery}
          </p>
          <Link to="/" data-testid="process-definition-return-dashboard">
            Return to Dashboard
          </Link>
        </section>
      ) : null}
      {view.state === "ready" ? (
        <>
          <aside
            className="process-definition__boundary"
            role="note"
            aria-label="Read-only definition boundary"
          >
            <strong>
              Definition only — not evidence that a process ran or an artifact
              exists
            </strong>
            <p>
              This page explains validated declarations. It cannot edit, apply,
              execute, invoke tools, or persist process data.
            </p>
          </aside>
          <div className="process-definition__projections">
            <ProcessDefinitionText definition={view.envelope.definition} />
            <ProcessDefinitionDiagram definition={view.envelope.definition} />
          </div>
          <ProcessDefinitionDetails envelope={view.envelope} />
        </>
      ) : null}
    </section>
  );
}

export default ProcessDefinitionPage;

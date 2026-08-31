import { useEffect, useState } from "react";
import {
  fetchProcessDefinition,
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
  | { state: "unavailable" };

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
      } catch {
        if (active && !controller.signal.aborted) {
          setView({ state: "unavailable" });
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
      {view.state === "unavailable" ? (
        <section
          className="process-definition__state"
          role="alert"
          aria-labelledby="process-definition-unavailable-title"
        >
          <h2 id="process-definition-unavailable-title">
            The validated process definition is unavailable
          </h2>
          <p>
            Wright did not display partial or unverified process content.
            Inspect the local Wright service and try again.
          </p>
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

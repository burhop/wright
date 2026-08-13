import { useCallback, useEffect, useMemo, useState } from "react";
import {
  engineeringModelService,
  type EngineeringModelCatalogResponse,
  type EngineeringModelView,
} from "../../services/engineering-model-service";
import {
  ModelEvidenceGrid,
  ModelReadinessBadge,
  ModelResourceSummary,
} from "../models/ModelTrustPrimitives";
import { EngineeringModelInstallFlow } from "../models/EngineeringModelInstallFlow";
import { EngineeringModelRuntimePanel } from "../models/EngineeringModelRuntimePanel";

function DetailPanel({
  model,
  onClose,
  workspaceId,
}: {
  model: EngineeringModelView;
  onClose: () => void;
  workspaceId: string;
}) {
  const [installations, setInstallations] = useState<Record<string, string>>(
    {},
  );
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="engineering-model-detail-title"
      data-testid="engineering-model-detail"
      style={{
        position: "fixed",
        inset: "var(--space-xl)",
        zIndex: 20,
        overflowY: "auto",
        padding: "var(--space-xl)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        background: "var(--color-neutral)",
        boxShadow: "var(--shadow-lg)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: "var(--space-lg)",
        }}
      >
        <div>
          <h2 id="engineering-model-detail-title">{model.display_name}</h2>
          <ModelReadinessBadge readiness={model.readiness} />
        </div>
        <button
          type="button"
          data-testid="model-detail-close"
          aria-label="Close model details"
          onClick={onClose}
        >
          Close
        </button>
      </div>

      <p>{model.description}</p>
      <section>
        <h3>Source and license</h3>
        <p>{model.source.uri}</p>
        <p>Immutable revision: {model.source.immutable_revision}</p>
        <p>
          {model.license.expression} · {model.license.redistribution}
        </p>
        <p>{model.license.attribution}</p>
      </section>

      {model.generator ? (
        <section data-testid="model-generator-evidence">
          <h3>Generated fixture recipe</h3>
          <p>{model.generator.recipe}</p>
          <p>Inputs: {JSON.stringify(model.generator.inputs)}</p>
          <ul>
            {model.generator.constraints.map((constraint) => (
              <li key={constraint}>{constraint}</li>
            ))}
          </ul>
          <p>Manifest digest: {model.generator.manifest_digest}</p>
          <p>Artifact-set digest: {model.generator.artifact_set_digest}</p>
        </section>
      ) : null}

      <section>
        <h3>Evidence</h3>
        <ModelEvidenceGrid evidence={model.evidence} />
      </section>

      <section>
        <h3>Variants and resources</h3>
        {model.variants.length ? (
          model.variants.map((variant) => (
            <article key={variant.variant_id}>
              <h4>{variant.variant_id}</h4>
              <p>
                {variant.format} · {variant.accelerator ?? "unspecified"}
              </p>
              <ModelResourceSummary variant={variant} />
              {model.readiness === "approved" &&
              model.blockers.length === 0 &&
              variant.compatibility?.state !== "incompatible" ? (
                <EngineeringModelInstallFlow
                  modelId={model.model_id}
                  variantId={variant.variant_id}
                  onInstalled={(installationId) =>
                    setInstallations((current) => ({
                      ...current,
                      [variant.variant_id]: installationId,
                    }))
                  }
                />
              ) : null}
              {installations[variant.variant_id] ? (
                workspaceId ? (
                  <EngineeringModelRuntimePanel
                    installationId={installations[variant.variant_id]}
                    taskId={model.tasks[0]}
                    workspaceId={workspaceId}
                  />
                ) : (
                  <p role="status">
                    Enter the target workspace identity below before enabling
                    this tested capability.
                  </p>
                )
              ) : null}
            </article>
          ))
        ) : (
          <p>No installable variant has been approved.</p>
        )}
      </section>

      <section>
        <h3>Limitations</h3>
        <ul>
          {model.limitations.map((limitation) => (
            <li key={limitation.limitation_id}>{limitation.description}</li>
          ))}
        </ul>
      </section>

      {model.blockers.length ? (
        <section>
          <h3>What blocks readiness</h3>
          {model.blockers.map((blocker) => (
            <article key={blocker.category}>
              <h4>{blocker.category.replaceAll("_", " ")}</h4>
              <p>{blocker.message}</p>
              <p>Recovery: {blocker.recovery}</p>
            </article>
          ))}
        </section>
      ) : null}
    </div>
  );
}

export function EngineeringModelLibraryPage() {
  const [catalog, setCatalog] =
    useState<EngineeringModelCatalogResponse | null>(null);
  const [search, setSearch] = useState("");
  const [task, setTask] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<EngineeringModelView | null>(null);
  const [workspaceId, setWorkspaceId] = useState("");

  const loadCatalog = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setCatalog(
        await engineeringModelService.listCatalog({
          search: search || undefined,
          task: task || undefined,
          limit: 100,
        }),
      );
    } catch {
      setError(
        "The engineering model catalog could not be loaded. Retry the bundled offline snapshot.",
      );
    } finally {
      setLoading(false);
    }
  }, [search, task]);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  const tasks = useMemo(
    () =>
      Array.from(
        new Set((catalog?.models ?? []).flatMap((model) => model.tasks)),
      ).sort(),
    [catalog],
  );

  const inspect = async (model: EngineeringModelView) => {
    setError(null);
    try {
      setSelected(
        await engineeringModelService.getCatalogModel(model.model_id),
      );
    } catch {
      setError(
        "The model detail could not be loaded from the offline snapshot.",
      );
    }
  };

  return (
    <main
      data-testid="page-engineering-models"
      style={{
        height: "100%",
        overflowY: "auto",
        padding: "var(--space-xl)",
        background: "var(--color-neutral)",
        color: "var(--color-primary)",
      }}
    >
      <header>
        <h1>Engineering Models</h1>
        <p>
          Evaluate specialized engineering models, trust evidence, hardware,
          licensing, and limitations. Conversational provider configuration
          remains in Model Setup.
        </p>
        <p data-testid="model-snapshot-state" aria-live="polite">
          {catalog?.snapshot.offline ? "Offline snapshot" : "Catalog snapshot"}
          {catalog ? ` · ${catalog.total} models` : ""}
        </p>
      </header>

      <section
        aria-label="Engineering model filters"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "var(--space-md)",
          marginBlock: "var(--space-lg)",
        }}
      >
        <label>
          Search engineering models
          <input
            data-testid="model-search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        <label>
          Target workspace identity
          <input
            data-testid="model-workspace-id"
            value={workspaceId}
            maxLength={128}
            onChange={(event) => setWorkspaceId(event.target.value.trim())}
            placeholder="Choose the workspace that may use this model"
          />
        </label>
        <label>
          Engineering task
          <select
            data-testid="model-task-filter"
            value={task}
            onChange={(event) => setTask(event.target.value)}
          >
            <option value="">All tasks</option>
            {tasks.map((item) => (
              <option key={item} value={item}>
                {item.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error ? (
        <div role="alert">
          <p>{error}</p>
          <button
            type="button"
            data-testid="model-catalog-retry"
            onClick={() => void loadCatalog()}
          >
            Retry offline catalog
          </button>
        </div>
      ) : null}

      {loading ? <p aria-live="polite">Loading engineering models…</p> : null}

      <section
        data-testid="model-library-grid"
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(min(100%, 20rem), 1fr))",
          gap: "var(--space-lg)",
        }}
      >
        {(catalog?.models ?? []).map((model) => (
          <article
            key={model.model_id}
            data-testid={`model-card-${model.model_id}`}
            style={{
              padding: "var(--space-lg)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-lg)",
              background: "var(--color-surface-subtle)",
            }}
          >
            <ModelReadinessBadge readiness={model.readiness} />
            <h2>{model.display_name}</h2>
            <p>{model.description}</p>
            <p>Tasks: {model.tasks.join(", ")}</p>
            <p>
              License: {model.license.expression} · Compatibility:{" "}
              {model.compatibility.state}
            </p>
            <button
              type="button"
              data-testid={`model-inspect-${model.model_id}`}
              onClick={() => void inspect(model)}
              aria-label={`Inspect ${model.display_name}`}
            >
              Inspect evidence
            </button>
          </article>
        ))}
      </section>

      {selected ? (
        <DetailPanel
          model={selected}
          workspaceId={workspaceId}
          onClose={() => setSelected(null)}
        />
      ) : null}
    </main>
  );
}

export default EngineeringModelLibraryPage;

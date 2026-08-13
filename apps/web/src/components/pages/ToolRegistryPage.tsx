import { useCallback, useEffect, useState } from "react";
import useLogger from "../../hooks/useLogger";
import type { MissingCapabilitySearchContext } from "../../services/mcp-service";
import { useTools } from "../../store/tools";
import { CapabilityLibrary } from "../tools/CapabilityLibrary";
import { CatalogUpdatePanel } from "../tools/CatalogUpdatePanel";
import {
  OnboardingWizard,
  type CapabilityOnboardingHandoff,
} from "../tools/OnboardingWizard";
import { MissingCapabilityForm } from "../tools/MissingCapabilityForm";

export function ToolRegistryPage() {
  const logger = useLogger("ToolRegistryPage");
  const { fetchServersAndTools } = useTools();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [refreshToken, setRefreshToken] = useState(0);
  const [initialCapabilityId, setInitialCapabilityId] = useState("");
  const [handoff, setHandoff] = useState<CapabilityOnboardingHandoff | null>(
    () => {
      try {
        const value = window.localStorage.getItem(
          "wright.capability-workspace-handoff.v1",
        );
        if (!value) return null;
        const parsed = JSON.parse(
          value,
        ) as Partial<CapabilityOnboardingHandoff>;
        return parsed.state === "workspace-enabled" &&
          typeof parsed.capabilityId === "string" &&
          typeof parsed.workspaceId === "string"
          ? (parsed as CapabilityOnboardingHandoff)
          : null;
      } catch {
        return null;
      }
    },
  );
  const [reportContext, setReportContext] =
    useState<MissingCapabilitySearchContext>({
      query: "",
      filters: {},
    });

  useEffect(() => {
    logger.info("Capability Library loaded");
  }, [logger]);

  const handleSearchContext = useCallback(
    (context: MissingCapabilitySearchContext) => setReportContext(context),
    [],
  );

  const openReport = useCallback((context: MissingCapabilitySearchContext) => {
    setReportContext(context);
    setIsReportOpen(true);
  }, []);

  return (
    <div
      data-testid="page-tool-registry"
      className="animate-fade-in-up"
      style={{
        height: "100%",
        overflowY: "auto",
        background: "var(--color-neutral)",
        color: "var(--color-primary)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: "var(--space-sm)",
          padding: "var(--space-lg) var(--space-xxl) 0",
          flexWrap: "wrap",
        }}
      >
        <button
          type="button"
          onClick={() => {
            setInitialCapabilityId("");
            setIsModalOpen(true);
          }}
          data-testid="tool-registry-register-btn"
          style={{
            padding: "var(--space-sm) var(--space-lg)",
            background: "var(--color-secondary)",
            color: "var(--color-surface-subtle)",
            border: 0,
            borderRadius: "var(--radius-lg)",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Add capability
        </button>
        <button
          type="button"
          onClick={() => setIsReportOpen(true)}
          data-testid="server-card-report-missing-mcp"
          style={{
            padding: "var(--space-sm) var(--space-lg)",
            background: "var(--color-surface-subtle)",
            color: "var(--color-secondary)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Report missing MCP
        </button>
      </div>
      <main
        style={{
          padding: "var(--space-xl) var(--space-xxl) var(--space-xxl)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-xl)",
        }}
      >
        {handoff ? (
          <section
            aria-labelledby="capability-handoff-title"
            data-testid="capability-handoff-restored"
          >
            <h2 id="capability-handoff-title">Workspace handoff restored</h2>
            <p>
              {handoff.capabilityId} remains available to workspace{" "}
              {handoff.workspaceId}. No install, enable, or workflow action was
              replayed after refresh.
            </p>
            <a href={`/workspace/${encodeURIComponent(handoff.workspaceId)}`}>
              Open the workspace and prepare Rivet
            </a>
          </section>
        ) : null}
        <CatalogUpdatePanel
          onCatalogChanged={() => setRefreshToken((value) => value + 1)}
        />
        <CapabilityLibrary
          refreshToken={refreshToken}
          onSearchContextChange={handleSearchContext}
          onReportMissing={openReport}
          onPlanOnboarding={(capabilityId) => {
            setInitialCapabilityId(capabilityId);
            setIsModalOpen(true);
          }}
        />
      </main>
      <OnboardingWizard
        isOpen={isModalOpen}
        initialCapabilityId={initialCapabilityId}
        onClose={() => setIsModalOpen(false)}
        onCompleted={(completedHandoff) => {
          try {
            window.localStorage.setItem(
              "wright.capability-workspace-handoff.v1",
              JSON.stringify(completedHandoff),
            );
          } catch {
            // Opaque or sandboxed documents can deny storage. The in-memory
            // handoff still completes and no capability action is replayed.
          }
          setHandoff(completedHandoff);
          void fetchServersAndTools();
          setRefreshToken((value) => value + 1);
        }}
      />
      <MissingCapabilityForm
        isOpen={isReportOpen}
        searchContext={reportContext}
        onClose={() => setIsReportOpen(false)}
      />
    </div>
  );
}

export default ToolRegistryPage;

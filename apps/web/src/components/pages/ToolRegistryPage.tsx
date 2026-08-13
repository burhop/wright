import { useCallback, useEffect, useState } from "react";
import useLogger from "../../hooks/useLogger";
import type { MissingCapabilitySearchContext } from "../../services/mcp-service";
import { useTools } from "../../store/tools";
import { CapabilityLibrary } from "../tools/CapabilityLibrary";
import { CatalogUpdatePanel } from "../tools/CatalogUpdatePanel";
import { OnboardingWizard } from "../tools/OnboardingWizard";
import { MissingCapabilityForm } from "../tools/MissingCapabilityForm";

export function ToolRegistryPage() {
  const logger = useLogger("ToolRegistryPage");
  const { fetchServersAndTools } = useTools();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [refreshToken, setRefreshToken] = useState(0);
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
          onClick={() => setIsModalOpen(true)}
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
        <CatalogUpdatePanel
          onCatalogChanged={() => setRefreshToken((value) => value + 1)}
        />
        <CapabilityLibrary
          refreshToken={refreshToken}
          onSearchContextChange={handleSearchContext}
          onReportMissing={openReport}
        />
      </main>
      <OnboardingWizard
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCompleted={() => {
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

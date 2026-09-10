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
  const [initialCapabilityId, setInitialCapabilityId] = useState("");
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
          onAddCapability={() => {
            setInitialCapabilityId("");
            setIsModalOpen(true);
          }}
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

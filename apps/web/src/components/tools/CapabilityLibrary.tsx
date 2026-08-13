import { useEffect, useMemo, useState } from "react";
import {
  mcpService,
  type CapabilityListResponse,
  type CapabilityView,
  type MissingCapabilitySearchContext,
} from "../../services/mcp-service";
import { CapabilityCard } from "./CapabilityCard";
import { CapabilityDetails } from "./CapabilityDetails";
import {
  CapabilityFilters,
  readCapabilityFilters,
  type CapabilityFilterState,
} from "./CapabilityFilters";

export function CapabilityLibrary({
  refreshToken = 0,
  onSearchContextChange,
  onReportMissing,
  onPlanOnboarding,
}: {
  refreshToken?: number;
  onSearchContextChange?: (context: MissingCapabilitySearchContext) => void;
  onReportMissing?: (context: MissingCapabilitySearchContext) => void;
  onPlanOnboarding?: (capabilityId: string) => void;
}) {
  const [filters, setFilters] = useState<CapabilityFilterState>(() =>
    readCapabilityFilters(),
  );
  const [result, setResult] = useState<CapabilityListResponse | null>(null);
  const [selected, setSelected] = useState<CapabilityView | null>(null);
  const [loading, setLoading] = useState(true);
  const [observing, setObserving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryToken, setRetryToken] = useState(0);

  const query = useMemo(
    () => ({
      search: filters.search || undefined,
      domain: filters.domain ? [filters.domain] : undefined,
      lifecycle_stage: filters.lifecycleStage
        ? [filters.lifecycleStage]
        : undefined,
      platform: filters.platform ? [filters.platform] : undefined,
      maturity: filters.maturity ? [filters.maturity] : undefined,
      evidence_class: filters.evidenceClass
        ? [filters.evidenceClass]
        : undefined,
      compatibility: filters.compatibility
        ? [filters.compatibility]
        : undefined,
      risk: filters.risk ? [filters.risk] : undefined,
      locality: filters.locality ? [filters.locality] : undefined,
      host: filters.host ? [filters.host] : undefined,
      validation: filters.validation ? [filters.validation] : undefined,
      installed:
        filters.installed === "" ? undefined : filters.installed === "true",
      limit: 200,
    }),
    [filters],
  );

  const searchContext = useMemo<MissingCapabilitySearchContext>(
    () => ({
      query: filters.search,
      filters: {
        domain: filters.domain,
        lifecycle_stage: filters.lifecycleStage,
        platform: filters.platform,
        maturity: filters.maturity,
        evidence_class: filters.evidenceClass,
        compatibility: filters.compatibility,
        risk: filters.risk,
        locality: filters.locality,
        host: filters.host,
        validation: filters.validation,
        installed: filters.installed,
      },
    }),
    [filters],
  );

  useEffect(() => {
    onSearchContextChange?.(searchContext);
  }, [onSearchContextChange, searchContext]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    mcpService
      .getCapabilities(query)
      .then((value) => {
        if (active) setResult(value);
      })
      .catch(() => {
        if (active)
          setError("The bundled Capability Library could not be loaded.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [query, refreshToken, retryToken]);

  const firstMatch = result?.capabilities[0] || null;
  const blockerOrigin = firstMatch?.compatibility.reasons[0]?.source
    ? firstMatch.compatibility.reasons[0].source.startsWith("machine.")
      ? "this machine"
      : firstMatch.compatibility.reasons[0].source.startsWith("policy.")
        ? "local Wright policy"
        : "recorded capability evidence"
    : null;
  const primaryAction = firstMatch
    ? firstMatch.compatibility.status === "incompatible"
      ? {
          label: "Review the incompatibility",
          consequence:
            "This opens evidence and alternatives; it does not install or enable anything.",
        }
      : firstMatch.compatibility.status === "uncertain"
        ? {
            label: "Review compatibility evidence",
            consequence:
              "This explains what is known before you create an onboarding plan; it does not install anything.",
          }
        : firstMatch.user_state?.active
          ? {
              label: "Review workspace availability",
              consequence:
                "This confirms the scope before you prepare a Rivet workflow.",
            }
          : {
              label: "Review and plan onboarding",
              consequence:
                "You will review an exact plan before Wright changes anything.",
            }
    : null;

  const observeSelected = async () => {
    if (!selected) return;
    setObserving(true);
    try {
      const observed = await mcpService.observeCapability(
        selected.capability_id,
      );
      const updated = { ...selected, compatibility: observed.compatibility };
      setSelected(updated);
      setResult((current) =>
        current
          ? {
              ...current,
              capabilities: current.capabilities.map((capability) =>
                capability.capability_id === updated.capability_id
                  ? updated
                  : capability,
              ),
            }
          : current,
      );
    } finally {
      setObserving(false);
    }
  };

  return (
    <section
      aria-labelledby="capability-library-title"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-lg)",
      }}
    >
      <div>
        <h1
          id="capability-library-title"
          style={{ marginBottom: "var(--space-xs)" }}
        >
          Engineering Capability Library
        </h1>
        <p style={{ color: "var(--color-text-muted)", margin: 0 }}>
          Find MCP servers and engineering integrations with honest evidence,
          machine compatibility, and prerequisites before anything is installed.
        </p>
      </div>

      <CapabilityFilters value={filters} onChange={setFilters} />

      {result?.snapshot.offline && (
        <div
          role="status"
          data-testid="capability-offline-source"
          style={{ color: "var(--color-text-muted)", fontSize: "0.82rem" }}
        >
          Using the complete bundled catalog · {result.total} matching
          capabilities
        </div>
      )}
      {loading && <div role="status">Loading capabilities…</div>}
      {error && (
        <div role="alert">
          <p>{error}</p>
          <button
            type="button"
            onClick={() => setRetryToken((value) => value + 1)}
          >
            Try loading again
          </button>
        </div>
      )}
      {!loading && !error && firstMatch && primaryAction ? (
        <aside
          aria-labelledby="capability-next-action-title"
          data-testid="capability-next-action"
        >
          <h2 id="capability-next-action-title">Next action</h2>
          <p>
            <strong>{primaryAction.label}.</strong> {primaryAction.consequence}
          </p>
          {blockerOrigin && firstMatch.compatibility.status !== "compatible" ? (
            <p>
              Blocker origin: <strong>{blockerOrigin}</strong>.{" "}
              {firstMatch.compatibility.reasons[0]?.message}
            </p>
          ) : null}
          <button
            type="button"
            data-testid="capability-primary-next-action"
            onClick={() => {
              setSelected(firstMatch);
              if (
                onPlanOnboarding &&
                firstMatch.compatibility.status === "compatible" &&
                !firstMatch.user_state?.active
              ) {
                onPlanOnboarding(firstMatch.capability_id);
              }
            }}
          >
            {primaryAction.label}
          </button>
        </aside>
      ) : null}
      {!loading && !error && result?.capabilities.length === 0 && (
        <div data-testid="capability-empty-state">
          <h2>No capabilities match these filters</h2>
          <p>Clear one or more filters, or report a missing MCP candidate.</p>
          {onReportMissing && (
            <button
              type="button"
              data-testid="capability-report-empty-result"
              onClick={() => onReportMissing(searchContext)}
            >
              Report this missing capability
            </button>
          )}
        </div>
      )}
      {!loading && !error && result && result.capabilities.length > 0 && (
        <div
          data-testid="capability-results"
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(min(100%, 320px), 1fr))",
            gap: "var(--space-lg)",
          }}
        >
          {result.capabilities.map((capability) => (
            <CapabilityCard
              key={capability.capability_id}
              capability={capability}
              onOpen={setSelected}
            />
          ))}
        </div>
      )}
      {selected && (
        <CapabilityDetails
          capability={selected}
          observing={observing}
          onObserve={observeSelected}
          onClose={() => setSelected(null)}
        />
      )}
    </section>
  );
}

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
  matchesCapabilityFilters,
  type CapabilityFilterState,
} from "./CapabilityFilters";

// Share an in-flight request across React StrictMode mounts. Filters run locally.
const pendingCatalogs = new Map<string, Promise<CapabilityListResponse>>();
function loadCatalog(refreshKey: string) {
  const existing = pendingCatalogs.get(refreshKey);
  if (existing) return existing;
  const pending = (async () => {
    const first = await mcpService.getCapabilities({ limit: 200 });
    const capabilities = [...first.capabilities];
    let cursor = first.next_cursor;
    const seen = new Set<string>();
    while (cursor) {
      if (seen.has(cursor))
        throw new Error("Catalog pagination did not advance");
      seen.add(cursor);
      const page = await mcpService.getCapabilities({ limit: 200, cursor });
      if (page.snapshot.snapshot_id !== first.snapshot.snapshot_id)
        throw new Error("Catalog changed while loading");
      capabilities.push(...page.capabilities);
      cursor = page.next_cursor;
    }
    return { ...first, capabilities, next_cursor: null };
  })().finally(() => {
    pendingCatalogs.delete(refreshKey);
  });
  pendingCatalogs.set(refreshKey, pending);
  return pending;
}

export function CapabilityLibrary({
  refreshToken = 0,
  onAddCapability,
  onSearchContextChange,
  onReportMissing,
  onPlanOnboarding,
}: {
  refreshToken?: number;
  onAddCapability?: () => void;
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

  const searchContext = useMemo<MissingCapabilitySearchContext>(
    () => ({
      query: filters.search,
      filters: {
        platform: filters.platform,
        installed: filters.installed,
        commercial: String(filters.commercial),
        open_source: String(filters.openSource),
      },
    }),
    [filters],
  );
  const matches = useMemo(
    () =>
      result?.capabilities.filter((capability) =>
        matchesCapabilityFilters(capability, filters),
      ) || [],
    [result, filters],
  );

  useEffect(() => {
    onSearchContextChange?.(searchContext);
  }, [onSearchContextChange, searchContext]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    loadCatalog(`${refreshToken}:${retryToken}`)
      .then((value) => {
        if (active) setResult(value);
      })
      .catch(() => {
        if (active)
          setError("The bundled MCP Server Library could not be loaded.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshToken, retryToken]);

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
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "var(--space-lg)",
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: "1 1 440px" }}>
          <h1
            id="capability-library-title"
            style={{ marginBottom: "var(--space-xs)" }}
          >
            Engineering MCP Server Library
          </h1>
          <p style={{ color: "var(--color-text-muted)", margin: 0 }}>
            Find and install MCP servers for engineering applications.
          </p>
        </div>
        <div
          style={{ display: "flex", gap: "var(--space-sm)", flexWrap: "wrap" }}
        >
          {onAddCapability ? (
            <button
              type="button"
              onClick={onAddCapability}
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
              Add custom MCP server
            </button>
          ) : null}
          {onReportMissing ? (
            <button
              type="button"
              onClick={() => onReportMissing(searchContext)}
              data-testid="server-card-report-missing-mcp"
            >
              Report missing MCP
            </button>
          ) : null}
        </div>
      </div>

      <CapabilityFilters value={filters} onChange={setFilters} />

      {result?.snapshot.offline && (
        <div
          role="status"
          data-testid="capability-offline-source"
          style={{ color: "var(--color-text-muted)", fontSize: "0.82rem" }}
        >
          {matches.length} matching MCP servers
        </div>
      )}
      {loading && (
        <div role="status">
          {result ? "Refreshing MCP servers…" : "Loading MCP servers…"}
        </div>
      )}
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
      {!loading && result && matches.length === 0 && (
        <div data-testid="capability-empty-state">
          <h2>No MCP servers match these filters</h2>
          <p>Clear one or more filters, or report a missing MCP candidate.</p>
          {onReportMissing && (
            <button
              type="button"
              data-testid="capability-report-empty-result"
              onClick={() => onReportMissing(searchContext)}
            >
              Report this missing MCP server
            </button>
          )}
        </div>
      )}
      {result && matches.length > 0 && (
        <div
          data-testid="capability-results"
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(min(100%, 320px), 1fr))",
            gap: "var(--space-lg)",
          }}
        >
          {matches.map((capability) => (
            <CapabilityCard
              key={capability.capability_id}
              capability={capability}
              onOpen={setSelected}
              onInstall={onPlanOnboarding}
            />
          ))}
        </div>
      )}
      {selected && (
        <CapabilityDetails
          capability={selected}
          observing={observing}
          onObserve={observeSelected}
          onPlan={
            onPlanOnboarding
              ? () => {
                  const capabilityId = selected.capability_id;
                  setSelected(null);
                  onPlanOnboarding(capabilityId);
                }
              : undefined
          }
          onClose={() => setSelected(null)}
        />
      )}
    </section>
  );
}

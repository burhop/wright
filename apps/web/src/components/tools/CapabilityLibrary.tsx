import { useEffect, useMemo, useState } from "react";
import {
  mcpService,
  type CapabilityListResponse,
  type CapabilityView,
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
}: {
  refreshToken?: number;
}) {
  const [filters, setFilters] = useState<CapabilityFilterState>(() =>
    readCapabilityFilters(),
  );
  const [result, setResult] = useState<CapabilityListResponse | null>(null);
  const [selected, setSelected] = useState<CapabilityView | null>(null);
  const [loading, setLoading] = useState(true);
  const [observing, setObserving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useMemo(
    () => ({
      search: filters.search || undefined,
      domain: filters.domain ? [filters.domain] : undefined,
      evidence_class: filters.evidenceClass
        ? [filters.evidenceClass]
        : undefined,
      compatibility: filters.compatibility
        ? [filters.compatibility]
        : undefined,
      limit: 200,
    }),
    [filters],
  );

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
  }, [query, refreshToken]);

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
      {error && <div role="alert">{error}</div>}
      {!loading && !error && result?.capabilities.length === 0 && (
        <div data-testid="capability-empty-state">
          <h2>No capabilities match these filters</h2>
          <p>Clear one or more filters, or report a missing MCP candidate.</p>
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

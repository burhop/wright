import type {
  CompatibilityStatus,
  EvidenceClass,
} from "../../services/mcp-service";

export interface CapabilityFilterState {
  search: string;
  domain: string;
  evidenceClass: EvidenceClass | "";
  compatibility: CompatibilityStatus | "";
}

export const emptyCapabilityFilters: CapabilityFilterState = {
  search: "",
  domain: "",
  evidenceClass: "",
  compatibility: "",
};

export function readCapabilityFilters(
  search = window.location.search,
): CapabilityFilterState {
  const parameters = new URLSearchParams(search);
  return {
    search: parameters.get("search") || "",
    domain: parameters.get("domain") || "",
    evidenceClass: (parameters.get("evidence_class") || "") as
      EvidenceClass | "",
    compatibility: (parameters.get("compatibility") || "") as
      CompatibilityStatus | "",
  };
}

export function writeCapabilityFilters(value: CapabilityFilterState) {
  const parameters = new URLSearchParams();
  if (value.search) parameters.set("search", value.search);
  if (value.domain) parameters.set("domain", value.domain);
  if (value.evidenceClass)
    parameters.set("evidence_class", value.evidenceClass);
  if (value.compatibility) parameters.set("compatibility", value.compatibility);
  const query = parameters.toString();
  window.history.replaceState(
    null,
    "",
    `${window.location.pathname}${query ? `?${query}` : ""}`,
  );
}

export function CapabilityFilters({
  value,
  onChange,
}: {
  value: CapabilityFilterState;
  onChange: (value: CapabilityFilterState) => void;
}) {
  const update = (next: Partial<CapabilityFilterState>) => {
    const merged = { ...value, ...next };
    writeCapabilityFilters(merged);
    onChange(merged);
  };
  const controlStyle = {
    minHeight: "40px",
    borderRadius: "var(--radius-lg)",
    border: "1px solid var(--color-border)",
    background: "var(--color-surface-subtle)",
    color: "var(--color-primary)",
    padding: "0 var(--space-md)",
  } as const;

  return (
    <form
      aria-label="Capability filters"
      onSubmit={(event) => event.preventDefault()}
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 180px), 1fr))",
        gap: "var(--space-sm)",
      }}
    >
      <label>
        <span className="sr-only">Search capabilities</span>
        <input
          aria-label="Search capabilities"
          data-testid="capability-search"
          type="search"
          value={value.search}
          placeholder="Search CAD, FEA, applications, or tasks"
          onChange={(event) => update({ search: event.target.value })}
          style={{ ...controlStyle, width: "100%" }}
        />
      </label>
      <label>
        <span className="sr-only">Engineering domain</span>
        <select
          aria-label="Engineering domain"
          value={value.domain}
          onChange={(event) => update({ domain: event.target.value })}
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">All domains</option>
          <option value="cad">CAD</option>
          <option value="ecad">ECAD</option>
          <option value="fea">FEA</option>
          <option value="cfd">CFD</option>
          <option value="cam">CAM</option>
          <option value="manufacturing">Manufacturing</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Evidence class</span>
        <select
          aria-label="Evidence class"
          value={value.evidenceClass}
          onChange={(event) =>
            update({ evidenceClass: event.target.value as EvidenceClass | "" })
          }
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">All evidence</option>
          <option value="official_production">Official</option>
          <option value="official_preview">Official preview</option>
          <option value="verified_community">Verified community</option>
          <option value="api_wrapper_candidate">API candidates</option>
          <option value="user_reported_source_needed">Source needed</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Compatibility</span>
        <select
          aria-label="Compatibility"
          value={value.compatibility}
          onChange={(event) =>
            update({
              compatibility: event.target.value as CompatibilityStatus | "",
            })
          }
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">All compatibility</option>
          <option value="compatible">Compatible</option>
          <option value="uncertain">Uncertain</option>
          <option value="incompatible">Incompatible</option>
          <option value="blocked">Blocked</option>
        </select>
      </label>
    </form>
  );
}

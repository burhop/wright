import type {
  CompatibilityStatus,
  EvidenceClass,
  RiskLevel,
} from "../../services/mcp-service";

export interface CapabilityFilterState {
  search: string;
  domain: string;
  lifecycleStage: string;
  platform: string;
  maturity: string;
  evidenceClass: EvidenceClass | "";
  compatibility: CompatibilityStatus | "";
  risk: RiskLevel | "";
  locality: "local" | "remote" | "";
  host: string;
  validation: string;
  installed: "" | "true" | "false";
}

const ENGINEERING_DOMAINS = [
  "ai-3d",
  "analysis",
  "animation",
  "bim",
  "browser-automation",
  "cad",
  "cae",
  "cam",
  "cfd",
  "cloud-cad",
  "cloud-cae",
  "code-cad",
  "computation",
  "digital-twin",
  "drafting",
  "fea",
  "hpc",
  "iot",
  "manufacturing-data",
  "mesh",
  "meshing",
  "model-based-design",
  "multiphysics",
  "plm",
  "rendering",
  "robotics",
  "simulation",
  "tolerance",
  "usd",
  "utilities",
  "visualization",
];

export const emptyCapabilityFilters: CapabilityFilterState = {
  search: "",
  domain: "",
  lifecycleStage: "",
  platform: "",
  maturity: "",
  evidenceClass: "",
  compatibility: "",
  risk: "",
  locality: "",
  host: "",
  validation: "",
  installed: "",
};

export function readCapabilityFilters(
  search = window.location.search,
): CapabilityFilterState {
  const parameters = new URLSearchParams(search);
  return {
    search: parameters.get("search") || "",
    domain: parameters.get("domain") || "",
    lifecycleStage: parameters.get("lifecycle_stage") || "",
    platform: parameters.get("platform") || "",
    maturity: parameters.get("maturity") || "",
    evidenceClass: (parameters.get("evidence_class") || "") as
      EvidenceClass | "",
    compatibility: (parameters.get("compatibility") || "") as
      CompatibilityStatus | "",
    risk: (parameters.get("risk") || "") as RiskLevel | "",
    locality: (parameters.get("locality") || "") as "local" | "remote" | "",
    host: parameters.get("host") || "",
    validation: parameters.get("validation") || "",
    installed: (parameters.get("installed") || "") as "" | "true" | "false",
  };
}

export function writeCapabilityFilters(value: CapabilityFilterState) {
  const parameters = new URLSearchParams();
  if (value.search) parameters.set("search", value.search);
  if (value.domain) parameters.set("domain", value.domain);
  if (value.lifecycleStage)
    parameters.set("lifecycle_stage", value.lifecycleStage);
  if (value.platform) parameters.set("platform", value.platform);
  if (value.maturity) parameters.set("maturity", value.maturity);
  if (value.evidenceClass)
    parameters.set("evidence_class", value.evidenceClass);
  if (value.compatibility) parameters.set("compatibility", value.compatibility);
  if (value.risk) parameters.set("risk", value.risk);
  if (value.locality) parameters.set("locality", value.locality);
  if (value.host) parameters.set("host", value.host);
  if (value.validation) parameters.set("validation", value.validation);
  if (value.installed) parameters.set("installed", value.installed);
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
      aria-label="MCP server filters"
      onSubmit={(event) => event.preventDefault()}
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 180px), 1fr))",
        gap: "var(--space-sm)",
      }}
    >
      <label>
        <span className="sr-only">Search MCP servers</span>
        <input
          aria-label="Search MCP servers"
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
          data-testid="capability-filter-domain"
          value={value.domain}
          onChange={(event) => update({ domain: event.target.value })}
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">All domains</option>
          {ENGINEERING_DOMAINS.map((domain) => (
            <option key={domain} value={domain}>
              {domain.toUpperCase()}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span className="sr-only">Lifecycle stage</span>
        <select
          aria-label="Lifecycle stage"
          data-testid="capability-filter-lifecycle"
          value={value.lifecycleStage}
          onChange={(event) => update({ lifecycleStage: event.target.value })}
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">All lifecycle stages</option>
          <option value="verified_mcp">Verified MCP</option>
          <option value="community_mcp">Community MCP</option>
          <option value="verified_docs_mcp">Documentation MCP</option>
          <option value="verified_api_wrapper_candidate">API candidate</option>
          <option value="watchlist">Watchlist</option>
          <option value="user_reported_url_needed">Source needed</option>
          <option value="capability_alias">Integration listing</option>
          <option value="ui_or_web_standard">UI or web standard</option>
          <option value="excluded">Excluded</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Current platform and architecture</span>
        <select
          aria-label="Current platform and architecture"
          data-testid="capability-filter-platform"
          value={value.platform}
          onChange={(event) => update({ platform: event.target.value })}
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">Current platform: any result</option>
          <option value="windows_11_x64">Windows 11 x64</option>
          <option value="linux_x64">Linux x64</option>
          <option value="linux_arm64">Linux ARM64</option>
          <option value="macos_x64">macOS x64</option>
          <option value="macos_arm64">macOS ARM64</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Maturity</span>
        <select
          aria-label="Maturity"
          data-testid="capability-filter-maturity"
          value={value.maturity}
          onChange={(event) => update({ maturity: event.target.value })}
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">All maturity levels</option>
          <option value="official">Official</option>
          <option value="reference">Reference</option>
          <option value="community">Community</option>
          <option value="experimental">Experimental</option>
          <option value="watchlist">Watchlist</option>
          <option value="deprecated">Deprecated</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Evidence class</span>
        <select
          aria-label="Evidence class"
          data-testid="capability-filter-evidence"
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
          <option value="community_candidate">Community candidate</option>
          <option value="api_wrapper_candidate">API candidates</option>
          <option value="documentation_only">Documentation only</option>
          <option value="blocked_validation">Blocked validation</option>
          <option value="excluded_or_stale">Excluded or stale</option>
          <option value="user_reported_source_needed">Source needed</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Setup readiness</span>
        <select
          aria-label="Setup readiness"
          data-testid="capability-filter-compatibility"
          value={value.compatibility}
          onChange={(event) =>
            update({
              compatibility: event.target.value as CompatibilityStatus | "",
            })
          }
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">All setup states</option>
          <option value="compatible">Ready to set up</option>
          <option value="uncertain">Check required</option>
          <option value="incompatible">Requirements missing</option>
          <option value="blocked">Setup blocked</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Risk level</span>
        <select
          aria-label="Risk level"
          data-testid="capability-filter-risk"
          value={value.risk}
          onChange={(event) =>
            update({ risk: event.target.value as RiskLevel | "" })
          }
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">All risk levels</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="safety-critical">Safety critical</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Locality</span>
        <select
          aria-label="Locality"
          data-testid="capability-filter-locality"
          value={value.locality}
          onChange={(event) =>
            update({
              locality: event.target.value as "local" | "remote" | "",
            })
          }
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">Local and remote</option>
          <option value="local">Local</option>
          <option value="remote">Remote</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Required host software</span>
        <input
          aria-label="Required host software"
          data-testid="capability-filter-host"
          value={value.host}
          placeholder="Host software"
          onChange={(event) => update({ host: event.target.value })}
          style={{ ...controlStyle, width: "100%" }}
        />
      </label>
      <label>
        <span className="sr-only">Validation state</span>
        <select
          aria-label="Validation state"
          data-testid="capability-filter-validation"
          value={value.validation}
          onChange={(event) => update({ validation: event.target.value })}
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">All validation states</option>
          <option value="not_checked">Not checked locally</option>
          <option value="queued">Queued</option>
          <option value="running">Running</option>
          <option value="passed">Passed</option>
          <option value="partially_passed">Partially passed</option>
          <option value="failed">Failed</option>
          <option value="blocked">Blocked</option>
          <option value="stale">Stale</option>
          <option value="unavailable">Unavailable</option>
          <option value="not_tested">Not tested in catalog evidence</option>
          <option value="dependency_missing">Dependency missing</option>
          <option value="skipped">Skipped</option>
        </select>
      </label>
      <label>
        <span className="sr-only">Installed state</span>
        <select
          aria-label="Installed state"
          data-testid="capability-filter-installed"
          value={value.installed}
          onChange={(event) =>
            update({
              installed: event.target.value as "" | "true" | "false",
            })
          }
          style={{ ...controlStyle, width: "100%" }}
        >
          <option value="">Installed and not installed</option>
          <option value="true">Installed or connected</option>
          <option value="false">Not installed</option>
        </select>
      </label>
    </form>
  );
}

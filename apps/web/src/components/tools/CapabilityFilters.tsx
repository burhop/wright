import type { CapabilityView } from "../../services/mcp-service";
import { capabilityFacts } from "./CapabilityFacts";

export interface CapabilityFilterState {
  search: string;
  platform: string;
  installed: "" | "true" | "false";
  commercial: boolean;
  openSource: boolean;
}
export const emptyCapabilityFilters: CapabilityFilterState = {
  search: "",
  platform: "",
  installed: "",
  commercial: false,
  openSource: false,
};
export function readCapabilityFilters(
  search = window.location.search,
): CapabilityFilterState {
  const params = new URLSearchParams(search);
  const platform = (params.get("platform") || "").split("_")[0];
  const installed = params.get("installed");
  return {
    search: params.get("search") || "",
    platform: ["windows", "linux", "macos"].includes(platform) ? platform : "",
    installed: installed === "true" || installed === "false" ? installed : "",
    commercial: params.get("commercial") === "true",
    openSource: params.get("open_source") === "true",
  };
}
export function writeCapabilityFilters(value: CapabilityFilterState) {
  const params = new URLSearchParams();
  if (value.search) params.set("search", value.search);
  if (value.platform) params.set("platform", value.platform);
  if (value.installed) params.set("installed", value.installed);
  if (value.commercial) params.set("commercial", "true");
  if (value.openSource) params.set("open_source", "true");
  window.history.replaceState(
    null,
    "",
    window.location.pathname + (params.size ? "?" + params : ""),
  );
}
export function matchesCapabilityFilters(
  capability: CapabilityView,
  value: CapabilityFilterState,
) {
  const facts = capabilityFacts(capability);
  const text = [
    capability.name,
    capability.vendor,
    capability.description,
    ...capability.domains,
    ...capability.tags,
    ...capability.aliases,
    ...capability.capability_summary,
  ]
    .join(" ")
    .toLowerCase();
  return (
    value.search
      .toLowerCase()
      .trim()
      .split(/\s+/)
      .every((word) => text.includes(word)) &&
    (!value.platform || facts.operatingSystems.includes(value.platform)) &&
    (!value.installed ||
      capability.user_state.installed === (value.installed === "true")) &&
    (!(value.commercial || value.openSource) ||
      (value.commercial && facts.commercial) ||
      (value.openSource && facts.openSource))
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
  const style = {
    minHeight: "42px",
    width: "100%",
    borderRadius: "var(--radius-lg)",
    border: "1px solid var(--color-border)",
    background: "var(--color-surface-subtle)",
    color: "var(--color-primary)",
    padding: "0 var(--space-md)",
  };
  return (
    <form
      aria-label="MCP server filters"
      onSubmit={(event) => event.preventDefault()}
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: "var(--space-sm)",
      }}
    >
      <input
        aria-label="Search MCP servers"
        data-testid="capability-search"
        type="search"
        placeholder="Search servers or applications"
        value={value.search}
        onChange={(event) => update({ search: event.target.value })}
        style={{ ...style, flex: "2 1 240px", width: "auto" }}
      />
      <select
        aria-label="Installed"
        value={value.installed}
        onChange={(event) =>
          update({
            installed: event.target.value as CapabilityFilterState["installed"],
          })
        }
        style={{ ...style, flex: "1 1 160px", width: "auto" }}
      >
        <option value="">Installed and not installed</option>
        <option value="true">Installed</option>
        <option value="false">Not installed</option>
      </select>
      <select
        aria-label="Operating system"
        value={value.platform}
        onChange={(event) => update({ platform: event.target.value })}
        style={{ ...style, flex: "1 1 150px", width: "auto" }}
      >
        <option value="">All operating systems</option>
        <option value="windows">Windows</option>
        <option value="macos">macOS</option>
        <option value="linux">Linux</option>
      </select>
      <label
        style={{ display: "flex", alignItems: "center", gap: 6, padding: 8 }}
      >
        <input
          type="checkbox"
          checked={value.commercial}
          onChange={(event) => update({ commercial: event.target.checked })}
        />{" "}
        Commercial
      </label>
      <label
        style={{ display: "flex", alignItems: "center", gap: 6, padding: 8 }}
      >
        <input
          type="checkbox"
          checked={value.openSource}
          onChange={(event) => update({ openSource: event.target.checked })}
        />{" "}
        Open source
      </label>
    </form>
  );
}

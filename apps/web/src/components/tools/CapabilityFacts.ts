import type { CapabilityView } from "../../services/mcp-service";

const OPEN_LICENSE =
  /^(MIT|Apache-2\.0|BSD-[23]-Clause|ISC|MPL-2\.0|GPL-[23]\.0(?:-only|-or-later)?|LGPL-[23]\.[01](?:-only|-or-later)?|AGPL-3\.0(?:-only|-or-later)?|Unlicense)$/i;
const OS_NAMES: Record<string, string> = {
  windows: "Windows",
  linux: "Linux",
  macos: "macOS",
};

export function capabilityFacts(capability: CapabilityView) {
  const requirements = capability.requirements;
  const license = requirements.license?.trim() || "";
  const auth = requirements.auth_model || "unknown";
  const openSource = OPEN_LICENSE.test(license);
  const commercial =
    auth === "license-server" ||
    capability.tags.includes("proprietary-host") ||
    /proprietary|subscription|commercial|service terms|product terms/i.test(
      license,
    );
  const operatingSystems = Object.entries(OS_NAMES)
    .filter(([os]) =>
      Object.entries(requirements.supported_platforms || {}).some(
        ([key, support]) =>
          key.startsWith(os + "_") &&
          ["yes", "likely", "host-dependent"].includes(support.status),
      ),
    )
    .map(([os]) => os);
  const cost = /subscription/i.test(license)
    ? "Subscription required"
    : auth === "license-server" || capability.tags.includes("proprietary-host")
      ? "Host software license required"
      : commercial
        ? "See publisher pricing"
        : openSource
          ? "Open-source MCP; service costs not specified"
          : "Not specified";
  const login = requirements.credentials?.length
    ? "Account or API key required"
    : (
        {
          oauth: "Login required",
          "api-key": "API key required",
          "desktop-session": "Sign in to the desktop app",
          "local-host": "Uses the local application",
          "license-server": "Uses the host application license",
          none: "No MCP login required",
        } as Record<string, string>
      )[auth] || "Not specified";
  const type =
    capability.lifecycle_stage === "verified_api_wrapper_candidate"
      ? "API integration candidate"
      : capability.transport === "webmcp"
        ? "WebMCP"
        : capability.tags.some((tag) =>
              ["hardware", "hardware-mcp", "device-control"].includes(tag),
            )
          ? "MCP · Hardware"
          : "MCP";
  const location =
    capability.locality === "remote"
      ? "Cloud / remote server"
      : operatingSystems.length
        ? operatingSystems.map((os) => OS_NAMES[os]).join(" · ")
        : "Local · OS not specified";
  const method =
    (
      {
        npm: "Install with npm",
        pip: "Install with pip",
        uvx: "Run with uvx",
        docker: "Run with Docker",
        source: "Install from source",
        "remote-http": "Connect to the server URL",
        "desktop-extension": "Install the application extension",
        "packaged-binary": "Install the application package",
        manual: "Follow publisher instructions",
      } as Record<string, string>
    )[requirements.install_method || ""] ||
    "See publisher installation instructions";
  return {
    openSource,
    commercial,
    operatingSystems,
    cost,
    login,
    type,
    location,
    method,
    license: license && license !== "unknown" ? license : "Not specified",
  };
}

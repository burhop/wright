import freecad from "../../../../docs/mcp-catalog/usage-guides/freecad-mcp.md?raw";
import blender from "../../../../docs/mcp-catalog/usage-guides/blender-mcp.md?raw";
import shell from "../../../../docs/mcp-catalog/usage-guides/mcp-shell-server.md?raw";
import oasis from "../../../../docs/mcp-catalog/usage-guides/oasis-mcp.md?raw";

import stevecad from "../../../../docs/mcp-catalog/usage-guides/stevecad-mcp.md?raw";
import autodeskHelp from "../../../../docs/mcp-catalog/usage-guides/autodesk-product-help-mcp.md?raw";

/** Existing provider documentation bundled for offline/local development help. */
export const providerSetupGuides = { freecad, blender, shell, oasis };

/** Exact catalog identities only: similar provider names do not share contracts. */
export const capabilitySetupGuides: Readonly<Record<string, string>> = {
  "freecad-mcp-nekanat": freecad,
  "blender-mcp": blender,
  "oasis-open-fem-agent": oasis,
  "stevecad-mcp": stevecad,
  "autodesk-product-help-mcp": autodeskHelp,
};

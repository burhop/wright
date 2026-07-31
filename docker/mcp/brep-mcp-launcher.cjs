#!/usr/bin/env node
"use strict";

const path = require("node:path");
const fs = require("node:fs");
const url = require("node:url");

const packageRootCandidates = [
  process.env.BREPJS_CAD_ROOT,
  process.env.APPDATA
    ? path.join(process.env.APPDATA, "npm", "node_modules", "brepjs-cad")
    : "",
  process.env.npm_config_prefix
    ? path.join(process.env.npm_config_prefix, "node_modules", "brepjs-cad")
    : "",
  "/usr/local/lib/node_modules/brepjs-cad",
].filter(Boolean);
const packageRoot =
  packageRootCandidates.find((candidate) => fs.existsSync(candidate)) ||
  packageRootCandidates[0];
const mcpEntry = path.join(packageRoot, "dist", "mcp", "server.cjs");
const cliEntry =
  process.env.BREPJS_CAD_CLI_ENTRY ||
  path.join(packageRoot, "dist", "cli", "main.js");

// brepjs-cad 0.103.0's published MCP bundle loses import.meta.url in the
// CommonJS build and embeds the CLI fallback as a data URL. Leave upstream
// package files untouched and redirect those runtime lookups to installed files.
const OriginalURL = global.URL;
function WrightBrepRuntimeURL(input, base) {
  if (base === "undefined" && String(input).startsWith("data:")) {
    return new OriginalURL(input);
  }
  return base === undefined
    ? new OriginalURL(input)
    : new OriginalURL(input, base);
}
Object.setPrototypeOf(WrightBrepRuntimeURL, OriginalURL);
WrightBrepRuntimeURL.prototype = OriginalURL.prototype;
global.URL = WrightBrepRuntimeURL;

const originalFileURLToPath = url.fileURLToPath;
url.fileURLToPath = function fileURLToPathForBrepMcp(value, ...args) {
  const rendered = String(value ?? "");
  if (rendered.startsWith("data:")) return cliEntry;
  if (!rendered || rendered === "undefined") return mcpEntry;
  return originalFileURLToPath.call(this, value, ...args);
};

require(mcpEntry);

import type {
  McpUiResourceCsp,
  McpUiResourcePermissions,
} from "@modelcontextprotocol/ext-apps/app-bridge";

export const MCP_APP_MEDIA_TYPE = "text/html;profile=mcp-app";
export const MCP_SANDBOX_PROTOCOL_VERSION = 1 as const;
export const MCP_SANDBOX_DEFAULT_ATTRIBUTE = "allow-scripts";
export const MCP_OUTER_SANDBOX_ATTRIBUTE = "allow-scripts allow-same-origin";

const MAX_DOMAINS_PER_DIRECTIVE = 32;
const MAX_DOMAIN_LENGTH = 512;
const PERMISSION_NAMES = new Set([
  "camera",
  "microphone",
  "geolocation",
  "clipboardWrite",
]);

export interface ValidatedResourceCsp {
  readonly connectDomains: readonly string[];
  readonly resourceDomains: readonly string[];
  readonly frameDomains: readonly string[];
  readonly baseUriDomains: readonly string[];
}

export interface ValidatedSandboxPolicy {
  readonly csp: ValidatedResourceCsp;
  readonly permissions: Readonly<McpUiResourcePermissions>;
  readonly contentSecurityPolicy: string;
  readonly permissionsPolicy: string;
  readonly allowAttribute: string;
  readonly sandboxAttribute: typeof MCP_SANDBOX_DEFAULT_ATTRIBUTE;
}

export interface SandboxProxyUrlOptions {
  readonly sandboxOrigin: string;
  readonly hostOrigin: string;
  readonly surfaceId: string;
  readonly generation: number;
  readonly nonce: string;
}

function fail(message: string): never {
  throw new TypeError(`Invalid MCP App sandbox policy: ${message}`);
}

function validateOriginSource(
  value: string,
  directive: keyof McpUiResourceCsp,
): string {
  if (value.length > MAX_DOMAIN_LENGTH) {
    fail(`${directive} entry is too long`);
  }
  if (/\s|'|"|;/.test(value)) {
    fail(`${directive} entry contains unsafe CSP syntax`);
  }
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    fail(`${directive} entry must be an absolute origin`);
  }
  const permittedSchemes =
    directive === "connectDomains"
      ? new Set(["https:", "wss:"])
      : new Set(["https:"]);
  if (!permittedSchemes.has(parsed.protocol)) {
    fail(`${directive} entry must use an approved secure scheme`);
  }
  if (
    parsed.username ||
    parsed.password ||
    parsed.pathname !== "/" ||
    parsed.search ||
    parsed.hash
  ) {
    fail(`${directive} entry must contain only an origin`);
  }
  const wildcard = parsed.hostname.startsWith("*.");
  const hostname = wildcard ? parsed.hostname.slice(2) : parsed.hostname;
  if (
    !hostname.includes(".") ||
    hostname === "localhost" ||
    hostname.endsWith(".localhost") ||
    hostname.endsWith(".local") ||
    /^\d+(?:\.\d+){3}$/.test(hostname) ||
    hostname.includes(":") ||
    hostname.includes("*")
  ) {
    fail(`${directive} entry must name a public DNS origin`);
  }
  return `${parsed.protocol}//${wildcard ? "*." : ""}${hostname}${
    parsed.port ? `:${parsed.port}` : ""
  }`;
}

function validateDomains(
  values: readonly string[] | undefined,
  directive: keyof McpUiResourceCsp,
): readonly string[] {
  if (values === undefined) return Object.freeze([]);
  if (!Array.isArray(values) || values.length > MAX_DOMAINS_PER_DIRECTIVE) {
    fail(`${directive} exceeds ${MAX_DOMAINS_PER_DIRECTIVE} entries`);
  }
  return Object.freeze(
    [...new Set(values.map((value) => validateOriginSource(value, directive)))],
  );
}

function validatePermissions(
  permissions: McpUiResourcePermissions | undefined,
): Readonly<McpUiResourcePermissions> {
  if (permissions === undefined) return Object.freeze({});
  if (typeof permissions !== "object" || permissions === null) {
    fail("permissions must be an object");
  }
  const result: Record<string, Record<string, never>> = {};
  for (const [name, declaration] of Object.entries(permissions)) {
    if (!PERMISSION_NAMES.has(name)) fail(`permission ${name} is unsupported`);
    if (
      typeof declaration !== "object" ||
      declaration === null ||
      Array.isArray(declaration) ||
      Object.keys(declaration).length !== 0
    ) {
      fail(`permission ${name} must use an empty declaration object`);
    }
    result[name] = Object.freeze({});
  }
  return Object.freeze(result) as Readonly<McpUiResourcePermissions>;
}

function sources(values: readonly string[]): string {
  return values.length === 0 ? "'none'" : values.join(" ");
}

export function buildContentSecurityPolicy(
  csp: ValidatedResourceCsp,
): string {
  const resources = sources(csp.resourceDomains);
  return [
    "default-src 'none'",
    `connect-src ${sources(csp.connectDomains)}`,
    `script-src 'unsafe-inline' ${resources}`,
    `style-src 'unsafe-inline' ${resources}`,
    `img-src data: blob: ${resources}`,
    `font-src ${resources}`,
    `media-src blob: ${resources}`,
    `worker-src blob: ${resources}`,
    `frame-src ${sources(csp.frameDomains)}`,
    `child-src ${sources(csp.frameDomains)}`,
    `base-uri ${csp.baseUriDomains.length === 0 ? "'self'" : csp.baseUriDomains.join(" ")}`,
    "object-src 'none'",
    "form-action 'none'",
    "manifest-src 'none'",
    "frame-ancestors 'none'",
  ].join("; ");
}

export function buildPermissionsPolicy(
  permissions: Readonly<McpUiResourcePermissions>,
): string {
  const granted = new Set(Object.keys(permissions));
  return [
    ["camera", "camera"],
    ["microphone", "microphone"],
    ["geolocation", "geolocation"],
    ["clipboard-write", "clipboardWrite"],
  ]
    .map(([feature, key]) => `${feature}=(${granted.has(key) ? "self" : ""})`)
    .join(", ");
}

export function buildAllowAttribute(
  permissions: Readonly<McpUiResourcePermissions>,
): string {
  const entries: string[] = [];
  if (permissions.camera) entries.push("camera");
  if (permissions.microphone) entries.push("microphone");
  if (permissions.geolocation) entries.push("geolocation");
  if (permissions.clipboardWrite) entries.push("clipboard-write");
  return entries.join("; ");
}

export function validateSandboxPolicy(
  csp: McpUiResourceCsp | undefined,
  grantedPermissions: McpUiResourcePermissions | undefined,
): ValidatedSandboxPolicy {
  if (csp !== undefined) {
    const unexpected = Object.keys(csp).find(
      (key) =>
        ![
          "connectDomains",
          "resourceDomains",
          "frameDomains",
          "baseUriDomains",
        ].includes(key),
    );
    if (unexpected) fail(`CSP field ${unexpected} is unsupported`);
  }
  const validatedCsp = Object.freeze({
    connectDomains: validateDomains(csp?.connectDomains, "connectDomains"),
    resourceDomains: validateDomains(csp?.resourceDomains, "resourceDomains"),
    frameDomains: validateDomains(csp?.frameDomains, "frameDomains"),
    baseUriDomains: validateDomains(csp?.baseUriDomains, "baseUriDomains"),
  });
  const permissions = validatePermissions(grantedPermissions);
  return Object.freeze({
    csp: validatedCsp,
    permissions,
    contentSecurityPolicy: buildContentSecurityPolicy(validatedCsp),
    permissionsPolicy: buildPermissionsPolicy(permissions),
    allowAttribute: buildAllowAttribute(permissions),
    sandboxAttribute: MCP_SANDBOX_DEFAULT_ATTRIBUTE,
  });
}

function exactOrigin(value: string, label: string): string {
  const parsed = new URL(value);
  if (parsed.origin === "null" || parsed.href !== `${parsed.origin}/`) {
    throw new TypeError(`${label} must be an exact HTTP(S) origin`);
  }
  if (
    parsed.protocol !== "https:" &&
    parsed.hostname !== "localhost" &&
    !parsed.hostname.endsWith(".localhost")
  ) {
    throw new TypeError(`${label} must use HTTPS outside localhost development`);
  }
  return parsed.origin;
}

export function createSandboxProxyUrl({
  sandboxOrigin,
  hostOrigin,
  surfaceId,
  generation,
  nonce,
}: SandboxProxyUrlOptions): URL {
  if (!Number.isSafeInteger(generation) || generation < 1) {
    throw new TypeError("generation must be a positive integer");
  }
  if (!/^[A-Za-z0-9_-]{16,256}$/.test(nonce)) {
    throw new TypeError("nonce must contain 16 to 256 URL-safe characters");
  }
  if (!/^[A-Za-z0-9._:-]{1,128}$/.test(surfaceId)) {
    throw new TypeError("surfaceId contains unsupported characters");
  }
  const origin = exactOrigin(sandboxOrigin, "sandboxOrigin");
  const url = new URL("/surface-sandbox/index.html", `${origin}/`);
  url.searchParams.set("hostOrigin", exactOrigin(hostOrigin, "hostOrigin"));
  url.searchParams.set("surfaceId", surfaceId);
  url.searchParams.set("generation", String(generation));
  url.searchParams.set("nonce", nonce);
  return url;
}

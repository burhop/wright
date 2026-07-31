export const SURFACE_CONTRACT_VERSION = 1 as const;

export type SurfaceLifecycle =
  | "declared"
  | "starting"
  | "ready"
  | "unhealthy"
  | "stopping"
  | "stopped"
  | "failed";

interface SurfaceSourceBase {
  readonly sourceId: string;
  readonly sourceVersion: string;
}

export interface FileSurfaceSource extends SurfaceSourceBase {
  readonly kind: "file";
  readonly path: string;
  readonly mediaType?: string;
}

export interface DisplaySurfaceSource extends SurfaceSourceBase {
  readonly kind: "display";
  readonly displayId: string;
  readonly revision: number;
}

export interface LiveAppSurfaceSource extends SurfaceSourceBase {
  readonly kind: "live_app";
  readonly manifestId: string;
}

export interface McpAppSurfaceSource extends SurfaceSourceBase {
  readonly kind: "mcp_app";
  readonly serverId: string;
  readonly resourceUri: string;
  readonly contentHash: string;
}

export interface ExternalUrlSurfaceSource extends SurfaceSourceBase {
  readonly kind: "external_url";
  readonly displayUrl: string;
  readonly viewOnly: true;
}

export type SurfaceSource =
  | FileSurfaceSource
  | DisplaySurfaceSource
  | LiveAppSurfaceSource
  | McpAppSurfaceSource
  | ExternalUrlSurfaceSource;

export type SurfaceCapabilityState =
  | "unavailable"
  | "available"
  | "consent_required"
  | "granted"
  | "denied";

export type SurfaceCapabilityRiskTier = "low" | "high" | "mutating";

export interface SurfaceCapabilityProjection {
  readonly name: string;
  readonly state: SurfaceCapabilityState;
  readonly riskTier: SurfaceCapabilityRiskTier;
}

export interface SurfaceDescriptor {
  readonly schemaVersion: 1;
  readonly surfaceId: string;
  readonly workspaceId: string;
  readonly source: SurfaceSource;
  readonly title: string;
  readonly lifecycle: SurfaceLifecycle;
  readonly instance?: Readonly<Record<string, unknown>> | null;
  readonly presentations: readonly Readonly<Record<string, unknown>>[];
  readonly capabilities: readonly SurfaceCapabilityProjection[];
  readonly diagnosticSummary?: Readonly<Record<string, unknown>> | null;
  readonly generationProvenance?: Readonly<Record<string, unknown>> | null;
  readonly revision: number;
  readonly createdAt: string;
  readonly updatedAt: string;
}

const lifecycleValues = new Set<SurfaceLifecycle>([
  "declared",
  "starting",
  "ready",
  "unhealthy",
  "stopping",
  "stopped",
  "failed",
]);
const capabilityStates = new Set<SurfaceCapabilityState>([
  "unavailable",
  "available",
  "consent_required",
  "granted",
  "denied",
]);
const capabilityRiskTiers = new Set<SurfaceCapabilityRiskTier>([
  "low",
  "high",
  "mutating",
]);

const descriptorKeys = new Set([
  "schemaVersion",
  "surfaceId",
  "workspaceId",
  "source",
  "title",
  "lifecycle",
  "instance",
  "presentations",
  "capabilities",
  "diagnosticSummary",
  "generationProvenance",
  "revision",
  "createdAt",
  "updatedAt",
]);

const sourceKeys: Record<SurfaceSource["kind"], ReadonlySet<string>> = {
  file: new Set(["kind", "sourceId", "sourceVersion", "path", "mediaType"]),
  display: new Set([
    "kind",
    "sourceId",
    "sourceVersion",
    "displayId",
    "revision",
  ]),
  live_app: new Set(["kind", "sourceId", "sourceVersion", "manifestId"]),
  mcp_app: new Set([
    "kind",
    "sourceId",
    "sourceVersion",
    "serverId",
    "resourceUri",
    "contentHash",
  ]),
  external_url: new Set([
    "kind",
    "sourceId",
    "sourceVersion",
    "displayUrl",
    "viewOnly",
  ]),
};

function record(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object`);
  }
  return value as Record<string, unknown>;
}

function string(value: unknown, label: string, maximum = 4096): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new TypeError(`${label} must be a non-empty string`);
  }
  if (value.length > maximum) {
    throw new TypeError(`${label} exceeds ${maximum} characters`);
  }
  return value;
}

function positiveInteger(value: unknown, label: string): number {
  if (!Number.isSafeInteger(value) || (value as number) < 1) {
    throw new TypeError(`${label} must be a positive integer`);
  }
  return value as number;
}

function exactKeys(
  value: Record<string, unknown>,
  allowed: ReadonlySet<string>,
  label: string,
): void {
  const unexpected = Object.keys(value).find((key) => !allowed.has(key));
  if (unexpected) {
    throw new TypeError(`${label}.${unexpected} is not allowed`);
  }
}

function parseSource(value: unknown): SurfaceSource {
  const source = record(value, "source");
  const kind = string(source.kind, "source.kind", 32);
  if (!(kind in sourceKeys)) {
    throw new TypeError(`source.kind is unsupported: ${kind}`);
  }
  const typedKind = kind as SurfaceSource["kind"];
  exactKeys(source, sourceKeys[typedKind], "source");
  const common = {
    sourceId: string(source.sourceId, "source.sourceId", 256),
    sourceVersion: string(source.sourceVersion, "source.sourceVersion", 256),
  };
  switch (typedKind) {
    case "file":
      return Object.freeze({
        kind: typedKind,
        ...common,
        path: string(source.path, "source.path"),
        ...(source.mediaType === undefined
          ? {}
          : { mediaType: string(source.mediaType, "source.mediaType", 128) }),
      });
    case "display":
      return Object.freeze({
        kind: typedKind,
        ...common,
        displayId: string(source.displayId, "source.displayId", 128),
        revision: positiveInteger(source.revision, "source.revision"),
      });
    case "live_app":
      return Object.freeze({
        kind: typedKind,
        ...common,
        manifestId: string(source.manifestId, "source.manifestId", 128),
      });
    case "mcp_app":
      return Object.freeze({
        kind: typedKind,
        ...common,
        serverId: string(source.serverId, "source.serverId", 128),
        resourceUri: string(source.resourceUri, "source.resourceUri", 2048),
        contentHash: string(source.contentHash, "source.contentHash", 128),
      });
    case "external_url":
      if (source.viewOnly !== true) {
        throw new TypeError("source.viewOnly must be true");
      }
      return Object.freeze({
        kind: typedKind,
        ...common,
        displayUrl: string(source.displayUrl, "source.displayUrl"),
        viewOnly: true,
      });
  }
}

function timestamp(value: unknown, label: string): string {
  const result = string(value, label, 64);
  if (Number.isNaN(Date.parse(result))) {
    throw new TypeError(`${label} must be an ISO date-time`);
  }
  return result;
}

function parseCapability(
  value: unknown,
  index: number,
): SurfaceCapabilityProjection {
  const capability = record(value, `capabilities[${index}]`);
  exactKeys(
    capability,
    new Set(["name", "state", "riskTier"]),
    `capabilities[${index}]`,
  );
  const state = string(capability.state, `capabilities[${index}].state`, 32);
  const riskTier = string(
    capability.riskTier,
    `capabilities[${index}].riskTier`,
    32,
  );
  if (!capabilityStates.has(state as SurfaceCapabilityState)) {
    throw new TypeError(`capabilities[${index}].state is unsupported`);
  }
  if (!capabilityRiskTiers.has(riskTier as SurfaceCapabilityRiskTier)) {
    throw new TypeError(`capabilities[${index}].riskTier is unsupported`);
  }
  return Object.freeze({
    name: string(capability.name, `capabilities[${index}].name`, 128),
    state: state as SurfaceCapabilityState,
    riskTier: riskTier as SurfaceCapabilityRiskTier,
  });
}

export function parseSurfaceDescriptor(value: unknown): SurfaceDescriptor {
  const descriptor = record(value, "surface");
  exactKeys(descriptor, descriptorKeys, "surface");
  if (descriptor.schemaVersion !== SURFACE_CONTRACT_VERSION) {
    throw new TypeError("schemaVersion must be 1");
  }
  const lifecycle = string(descriptor.lifecycle, "lifecycle", 32);
  if (!lifecycleValues.has(lifecycle as SurfaceLifecycle)) {
    throw new TypeError(`lifecycle is unsupported: ${lifecycle}`);
  }
  if (!Array.isArray(descriptor.presentations)) {
    throw new TypeError("presentations must be an array");
  }
  if (!Array.isArray(descriptor.capabilities)) {
    throw new TypeError("capabilities must be an array");
  }
  return Object.freeze({
    schemaVersion: 1,
    surfaceId: string(descriptor.surfaceId, "surfaceId", 128),
    workspaceId: string(descriptor.workspaceId, "workspaceId", 128),
    source: parseSource(descriptor.source),
    title: string(descriptor.title, "title", 256),
    lifecycle: lifecycle as SurfaceLifecycle,
    ...(descriptor.instance === undefined
      ? {}
      : { instance: descriptor.instance as Readonly<Record<string, unknown>> }),
    presentations: Object.freeze([...descriptor.presentations]),
    capabilities: Object.freeze(descriptor.capabilities.map(parseCapability)),
    ...(descriptor.diagnosticSummary === undefined
      ? {}
      : {
          diagnosticSummary: descriptor.diagnosticSummary as Readonly<
            Record<string, unknown>
          >,
        }),
    ...(descriptor.generationProvenance === undefined
      ? {}
      : {
          generationProvenance: descriptor.generationProvenance as Readonly<
            Record<string, unknown>
          >,
        }),
    revision: positiveInteger(descriptor.revision, "revision"),
    createdAt: timestamp(descriptor.createdAt, "createdAt"),
    updatedAt: timestamp(descriptor.updatedAt, "updatedAt"),
  });
}

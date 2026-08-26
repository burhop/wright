export interface DiagnosticMcpServerOption {
  serverId: string;
  name: string;
  description: string;
  transport: string;
  active: boolean;
  installed: boolean;
}

export interface DiagnosticMcpToolOption {
  toolId: string;
  serverId: string;
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  enabled: boolean;
}

export interface DiagnosticMcpCatalog {
  servers: readonly DiagnosticMcpServerOption[];
  tools: readonly DiagnosticMcpToolOption[];
}

export interface DiagnosticMcpSuggestion {
  serverId: string;
  toolId: string | null;
  reason: string;
  source: "context" | "fixture";
}

export interface DiagnosticMcpBindingDefault {
  serverName: string;
  toolName?: string;
  reason: string;
}

const genericServerWords = new Set([
  "agent",
  "hosted",
  "labs",
  "mcp",
  "official",
  "open",
  "server",
  "tool",
  "tools",
]);

function normalizedWords(value: string): string[] {
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

function normalizedPhrase(value: string): string {
  return normalizedWords(value).join(" ");
}

function phraseAppears(context: string, candidate: string): boolean {
  const phrase = normalizedPhrase(candidate);
  return phrase.length > 0 && ` ${context} `.includes(` ${phrase} `);
}

function distinctiveServerPhrase(name: string): string {
  return normalizedWords(name)
    .filter((word) => !genericServerWords.has(word))
    .join(" ");
}

export function diagnosticToolsForServer(
  catalog: DiagnosticMcpCatalog,
  serverId: string | null,
): DiagnosticMcpToolOption[] {
  if (!serverId) return [];
  return catalog.tools
    .filter((tool) => tool.serverId === serverId)
    .toSorted((left, right) => left.name.localeCompare(right.name));
}

export function diagnosticRequiredToolInputs(
  tool: DiagnosticMcpToolOption | null,
): string[] {
  const required = tool?.inputSchema.required;
  return Array.isArray(required)
    ? required.filter((value): value is string => typeof value === "string")
    : [];
}

/**
 * Resolve a fixture-authored default through exact catalog names. Catalog IDs
 * remain canonical after resolution, but are installation-specific and must
 * not be embedded in the reusable workflow fixture.
 */
export function resolveExplicitDiagnosticMcpBinding(
  catalog: DiagnosticMcpCatalog,
  configuredDefault: DiagnosticMcpBindingDefault,
): DiagnosticMcpSuggestion | null {
  const matchingServers = catalog.servers.filter(
    ({ name }) =>
      normalizedPhrase(name) === normalizedPhrase(configuredDefault.serverName),
  );
  if (matchingServers.length !== 1) return null;

  const server = matchingServers[0];
  let toolId: string | null = null;
  if (configuredDefault.toolName) {
    const expectedToolName = normalizedPhrase(configuredDefault.toolName);
    const matchingTools = catalog.tools.filter(
      ({ serverId, name }) =>
        serverId === server.serverId &&
        normalizedPhrase(name) === expectedToolName,
    );
    if (matchingTools.length !== 1) return null;
    toolId = matchingTools[0].toolId;
  }

  return {
    serverId: server.serverId,
    toolId,
    reason: configuredDefault.reason,
    source: "fixture",
  };
}

/**
 * Defaults only from explicit catalog identity in the block context. Broad
 * semantic similarity is useful for ranking, but is not safe enough to bind a
 * runtime tool without review.
 */
export function suggestDiagnosticMcpBinding(
  catalog: DiagnosticMcpCatalog,
  context: string,
): DiagnosticMcpSuggestion | null {
  const normalizedContext = normalizedPhrase(context);
  if (!normalizedContext) return null;

  const serverMatches = catalog.servers.filter((server) => {
    const phrase = distinctiveServerPhrase(server.name);
    return phrase.length > 0 && phraseAppears(normalizedContext, phrase);
  });
  const exactToolMatches = catalog.tools.filter((tool) =>
    phraseAppears(normalizedContext, tool.name),
  );

  if (exactToolMatches.length === 1) {
    const tool = exactToolMatches[0];
    const server = serverMatches.find(
      ({ serverId }) => serverId === tool.serverId,
    );
    return {
      serverId: tool.serverId,
      toolId: tool.toolId,
      source: "context",
      reason: server
        ? `The block context explicitly names ${server.name} and ${tool.name}.`
        : `The block context explicitly names ${tool.name}.`,
    };
  }

  if (serverMatches.length === 1) {
    const server = serverMatches[0];
    const serverToolMatches = exactToolMatches.filter(
      (tool) => tool.serverId === server.serverId,
    );
    return {
      serverId: server.serverId,
      toolId:
        serverToolMatches.length === 1 ? serverToolMatches[0].toolId : null,
      reason:
        serverToolMatches.length === 1
          ? `The block context explicitly names ${server.name} and ${serverToolMatches[0].name}.`
          : `The block context explicitly names ${server.name}; choose its exact tool before execution.`,
      source: "context",
    };
  }

  return null;
}

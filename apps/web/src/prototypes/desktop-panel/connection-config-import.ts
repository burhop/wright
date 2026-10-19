// Parse locally. Private environment/header values never enter a tool request.
export interface ImportedConnection {
  name: string;
  type: "stdio" | "https";
  command: string;
  arguments: string[];
  url: string;
  environmentFields: string[];
  headerFields?: string[];
  publicCandidates: Record<string, string>;
}
const secretName =
  /token|secret|password|passwd|api[_-]?key|authorization|credential/i;
const environmentName = /^[A-Za-z_][A-Za-z0-9_]{0,127}$/;
function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw Error("Expected object");
  return value as Record<string, unknown>;
}
export function importConnectionConfiguration(
  text: string,
): ImportedConnection[] {
  if (new TextEncoder().encode(text).length > 256 * 1024)
    throw Error("Configuration too large");
  const document = object(JSON.parse(text));
  const entries =
    "mcpServers" in document
      ? object(document.mcpServers)
      : "servers" in document
        ? object(document.servers)
        : {
            [typeof document.name === "string"
              ? document.name
              : "Imported MCP"]: document,
          };
  const names = Object.keys(entries);
  if (!names.length || names.length > 100)
    throw Error("Unsupported server count");
  return names.map((name) => {
    if (!name.trim() || name.length > 100) throw Error("Unsupported name");
    const raw = object(entries[name]);
    const allowed = new Set([
      "name",
      "type",
      "command",
      "args",
      "arguments",
      "url",
      "endpoint",
      "env",
      "headers",
    ]);
    if (Object.keys(raw).some((key) => !allowed.has(key)))
      throw Error("Unsupported configuration fields");
    const env = raw.env === undefined ? {} : object(raw.env);
    const headers = raw.headers === undefined ? {} : object(raw.headers);
    const headerFields = Object.keys(headers);
    const reserved = new Set([
      "host",
      "content-length",
      "transfer-encoding",
      "connection",
      "accept",
      "content-type",
      "mcp-session-id",
      "mcp-protocol-version",
      "proxy-authorization",
      "cookie",
    ]);
    if (
      headerFields.length > 32 ||
      new Set(headerFields.map((key) => key.toLowerCase())).size !==
        headerFields.length ||
      headerFields.some(
        (key) =>
          !/^[!#$%&'*+.^_`|~0-9A-Za-z-]{1,128}$/.test(key) ||
          reserved.has(key.toLowerCase()),
      )
    )
      throw Error("Unsupported authentication header names");
    const fields = Object.keys(env);
    if (fields.length > 32 || fields.some((key) => !environmentName.test(key)))
      throw Error("Unsupported environment names");
    const endpoint = raw.url ?? raw.endpoint;
    if (typeof endpoint === "string") {
      const url = new URL(endpoint);
      if (
        !["http", "streamable_http", undefined].includes(
          raw.type as string | undefined,
        ) ||
        url.protocol !== "https:" ||
        url.username ||
        url.password ||
        url.search ||
        url.hash ||
        fields.length
      )
        throw Error("Unsupported remote configuration");
      return {
        name,
        type: "https",
        command: "",
        arguments: [],
        url: url.href,
        environmentFields: [],
        publicCandidates: {},
        ...(headerFields.length ? { headerFields } : {}),
      };
    }
    if (headerFields.length)
      throw Error("HTTP headers require a remote HTTPS MCP");
    if (raw.type !== undefined && raw.type !== "stdio")
      throw Error("Unsupported transport");
    if (
      typeof raw.command !== "string" ||
      !raw.command ||
      raw.command.length > 500
    )
      throw Error("Unsupported command");
    const args = raw.args ?? raw.arguments ?? [];
    if (
      !Array.isArray(args) ||
      args.length > 512 ||
      !args.every(
        (value) => typeof value === "string" && value.length <= 4096,
      ) ||
      args.reduce((sum, value: string) => sum + value.length, 0) > 65536
    )
      throw Error("Unsupported arguments");
    // Refuse obvious credential arguments; literal arguments are explicitly reviewed.
    if (
      args.some((value) =>
        /^--?(?:api[-_]?key|token|secret|password|authorization)(?:=|$)/i.test(
          value,
        ),
      )
    )
      throw Error(
        "Move credential arguments to private provider configuration",
      );
    return {
      name,
      type: "stdio",
      command: raw.command,
      arguments: args,
      url: "",
      environmentFields: fields,
      publicCandidates: Object.fromEntries(
        fields
          .filter(
            (key) =>
              !secretName.test(key) &&
              typeof env[key] === "string" &&
              (env[key] as string).length <= 4096,
          )
          .map((key) => [key, env[key] as string]),
      ),
    };
  });
}

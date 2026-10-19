import { expect, it } from "vitest";
import { importConnectionConfiguration } from "./connection-config-import";

it.each(["mcpServers", "servers"])(
  "withholds private values and offers only explicit public candidates from %s",
  (kind) => {
    const result = importConnectionConfiguration(
      JSON.stringify({
        [kind]: {
          Design: {
            command: "uvx",
            args: ["example-mcp==1.2.3"],
            env: {
              API_KEY: "placeholder-private-value",
              RUN_MODE: "read-only",
            },
          },
        },
      }),
    );
    expect(result).toEqual([
      {
        name: "Design",
        type: "stdio",
        command: "uvx",
        arguments: ["example-mcp==1.2.3"],
        url: "",
        environmentFields: ["API_KEY", "RUN_MODE"],
        publicCandidates: { RUN_MODE: "read-only" },
      },
    ]);
    expect(JSON.stringify(result)).not.toContain("placeholder-private-value");
  },
);
it("supports a public HTTPS endpoint and refuses unknown or credential-bearing settings", () => {
  expect(
    importConnectionConfiguration(
      '{"name":"CAD","type":"http","url":"https://example.invalid/mcp"}',
    )[0].type,
  ).toBe("https");
  for (const config of [
    { command: "npx", headers: { Authorization: "placeholder-private-value" } },
    { command: "uvx", args: ["--api-key=placeholder-private-value"] },
    { url: "https://example.invalid/mcp?token=placeholder-private-value" },
    { command: "uvx", env: { "INVALID=NAME": "x" } },
    { command: "uvx", unknown: "placeholder-private-value" },
    { type: "sse", url: "https://example.invalid/sse" },
  ])
    expect(() =>
      importConnectionConfiguration(JSON.stringify(config)),
    ).toThrow();
});
it("bounds the file and retains distinct named connections", () => {
  expect(() =>
    importConnectionConfiguration(" ".repeat(256 * 1024 + 1)),
  ).toThrow();
  expect(
    importConnectionConfiguration(
      '{"mcpServers":{"a":{"command":"a"},"b":{"command":"b"}}}',
    ).map((item) => item.name),
  ).toEqual(["a", "b"]);
});

it("withholds all static header values and rejects protocol-routing header overrides", () => {
  const [result] = importConnectionConfiguration(
    JSON.stringify({
      name: "Remote",
      type: "http",
      url: "https://provider.example/mcp",
      headers: {
        Authorization: "Bearer placeholder-private-key",
        "X-API-Key": "placeholder-other-key",
      },
    }),
  );
  expect(result.headerFields).toEqual(["Authorization", "X-API-Key"]);
  expect(JSON.stringify(result)).not.toContain("placeholder-private-key");
  expect(JSON.stringify(result)).not.toContain("placeholder-other-key");
  for (const headers of [
    { Host: "example.invalid" },
    { "Mcp-Session-Id": "session" },
    { Authorization: "a", authorization: "b" },
  ])
    expect(() =>
      importConnectionConfiguration(
        JSON.stringify({ url: "https://provider.example/mcp", headers }),
      ),
    ).toThrow();
});

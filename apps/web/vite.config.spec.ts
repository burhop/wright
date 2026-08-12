import { describe, expect, it } from "vitest";

import { rewriteSurfaceText, surfaceProxyHeaders } from "./vite.config";

describe("surface development proxy rewriting", () => {
  it("keeps Rivet AI configuration and completion requests inside the preview", () => {
    const authority = encodeURIComponent("s-editor.localhost:8000");
    const rewritten = rewriteSurfaceText(
      'fetch("/wright-ai/config");{"baseUrl":"/wright-ai/v1"}',
      authority,
    );

    expect(rewritten).toContain(
      `fetch("/__wright-surface/${authority}/wright-ai/config")`,
    );
    expect(rewritten).toContain(
      `"baseUrl":"/__wright-surface/${authority}/wright-ai/v1"`,
    );
  });

  it("preserves JSON request length for Rivet's bounded local server", () => {
    const headers = surfaceProxyHeaders(
      {
        host: "127.0.0.1:5173",
        connection: "keep-alive",
        "content-length": "512",
        "content-type": "application/json",
      },
      "s-editor.localhost:8000",
    );

    expect(headers.host).toBe("s-editor.localhost:8000");
    expect(headers.connection).toBeUndefined();
    expect(headers["accept-encoding"]).toBe("identity");
    expect(headers["content-length"]).toBe("512");
  });
});

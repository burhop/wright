import { describe, expect, it } from "vitest";

import {
  extractSurfaceSessionCookie,
  rewriteSurfaceSetCookies,
  rewriteSurfaceText,
  surfaceProxyHeaders,
} from "./vite.config";

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

  it("injects only the server-held Wright preview cookie", () => {
    const headers = surfaceProxyHeaders(
      {
        cookie: "app_session=value; wright_surface=stale-browser-value",
      },
      "s-editor.localhost:8000",
      "wright_surface=server-held-value",
    );

    expect(headers.cookie).toBe(
      "app_session=value; wright_surface=server-held-value",
    );
  });

  it("extracts the internal preview credential without forwarding it", () => {
    const upstream = [
      "wright_surface=secret; HttpOnly; Path=/; SameSite=strict",
      "rivet_session=value; Path=/editor; SameSite=Lax",
    ];

    expect(extractSurfaceSessionCookie(upstream)).toBe("wright_surface=secret");
  });

  it("isolates preview cookies by tunneled surface authority", () => {
    const authority = encodeURIComponent("s-editor.localhost:8000");
    const cookies = rewriteSurfaceSetCookies(
      [
        "wright_surface=secret; HttpOnly; Path=/; SameSite=strict",
        "rivet_session=value; Path=/editor; SameSite=Lax",
      ],
      authority,
    );

    expect(cookies).toEqual([
      `rivet_session=value; Path=/__wright-surface/${authority}/editor; SameSite=Lax`,
    ]);
  });

  it("adds a scoped path when an application cookie omitted one", () => {
    const authority = encodeURIComponent("s-brep.localhost:8000");

    expect(
      rewriteSurfaceSetCookies("session=value; HttpOnly", authority),
    ).toEqual([
      `session=value; HttpOnly; Path=/__wright-surface/${authority}/`,
    ]);
  });
});

import { describe, expect, it } from "vitest";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

import {
  extractSurfaceSessionCookie,
  rewriteSurfaceSetCookies,
  rewriteSurfaceText,
  surfaceProxyMatch,
  surfaceProxyHeaders,
  surfaceProxyConnection,
  surfaceProxyResponseBody,
} from "./vite.config";
import configuration from "./vite.config";

describe("web license build output", () => {
  it.each(["build", "serve"] as const)(
    "writes licenses to the resolved %s directory",
    async (command) => {
      const directory = mkdtempSync(
        path.join(tmpdir(), "wright-license-output-"),
      );
      try {
        if (typeof configuration !== "function")
          throw new Error("Expected the owning config factory");
        const config = await configuration({ command, mode: "production" });
        const plugins = (config.plugins ?? []).flat(Infinity);
        const resolver = plugins.find(
          (plugin) =>
            plugin &&
            typeof plugin === "object" &&
            "name" in plugin &&
            plugin.name === "wright-web-license-output",
        ) as { configResolved(config: unknown): void };
        const exporter = plugins.find(
          (plugin) =>
            plugin &&
            typeof plugin === "object" &&
            "name" in plugin &&
            plugin.name === "rollup-plugin-license",
        ) as { generateBundle(): void };
        resolver.configResolved({
          root: directory,
          build: { outDir: "isolated-dist" },
          publicDir: path.join(directory, "isolated-public"),
        });
        exporter.generateBundle();
        const destination = path.join(
          directory,
          command === "build" ? "isolated-dist" : "isolated-public",
          "third-party-licenses-web.txt",
        );
        expect(readFileSync(destination, "utf-8")).toBe(
          "No third parties dependencies",
        );
        expect(existsSync(path.join(directory, "dist"))).toBe(false);
      } finally {
        const resolved = path.resolve(directory);
        if (
          !resolved.startsWith(path.resolve(tmpdir()) + path.sep) ||
          !path.basename(resolved).startsWith("wright-license-output-")
        )
          throw new Error("Temporary cleanup escaped its root");
        rmSync(resolved, { recursive: true, force: true });
      }
    },
  );
});

describe("surface development proxy rewriting", () => {
  it.each(["application/json", "text/plain", "application/octet-stream"])(
    "preserves exact recorded %s evidence bytes and owning headers",
    (contentType) => {
      const body = Buffer.from('{"url":"/wright-ai/v1","text":"é","bytes":"\\u0000"}');
      const headers = {
        "content-type": contentType,
        "content-length": String(body.byteLength),
        "x-wright-artifact-sha256": "a".repeat(64),
        "x-content-type-options": "nosniff",
        "content-security-policy": "default-src 'none'",
      };
      const original = { ...headers };
      expect(surfaceProxyResponseBody(body, headers, "s-editor.localhost%3A8030")).toBe(body);
      expect(headers).toEqual(original);
      expect(body.toString()).toContain('"url":"/wright-ai/v1"');
    },
  );

  it("retains an invalid or absent declared artifact size for the scoped client to refuse", () => {
    for (const length of [undefined, "999"]) {
      const headers = {
        "x-wright-artifact-sha256": "a".repeat(64),
        ...(length === undefined ? {} : { "content-length": length }),
      };
      const original = { ...headers };
      surfaceProxyResponseBody(Buffer.from("exact"), headers, "s-editor.localhost%3A8030");
      expect(headers).toEqual(original);
    }
  });

  it("recalculates rewritten UTF-8 application length without chunked framing", () => {
    const body = Buffer.from('fetch("/wright-ai/config");const label="é";');
    const headers = {
      "content-type": "application/javascript",
      "content-length": String(body.byteLength),
      "transfer-encoding": "chunked",
      "content-security-policy": "default-src 'self'",
    };
    const result = surfaceProxyResponseBody(body, headers, "s-editor.localhost%3A8030");
    expect(result.toString()).toContain('/__wright-surface/s-editor.localhost%3A8030/wright-ai/config');
    expect(headers["content-length"]).toBe(String(result.byteLength));
    expect(headers).not.toHaveProperty("transfer-encoding");
    expect(headers).not.toHaveProperty("content-security-policy");
  });

  it.each([
    ["http://127.0.0.1:8030", "http:", "127.0.0.1", "8030"],
    ["http://localhost:8018", "http:", "localhost", "8018"],
    ["https://localhost:8443", "https:", "localhost", "8443"],
    ["http://localhost", "http:", "localhost", "80"],
    ["https://localhost", "https:", "localhost", "443"],
  ])("connects surface previews to the configured API %s", (target, protocol, hostname, port) => {
    expect(surfaceProxyConnection(target)).toEqual({ protocol, hostname, port });
  });

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

  it("translates only the exact isolated development Origin to its issued backend Origin", () => {
    const authority = "s-editor.localhost:8000";
    expect(surfaceProxyHeaders({host: "s-editor.localhost:5242", origin: "http://s-editor.localhost:5242"}, authority).origin)
      .toBe("http://s-editor.localhost:8000");
    for (const origin of ["null", "https://foreign.invalid", "http://127.0.0.1:5242", "http://s-other.localhost:5242", "http://s-editor.localhost:5242/"]) {
      expect(surfaceProxyHeaders({host: "s-editor.localhost:5242", origin}, authority).origin).toBe(origin);
    }
    expect(surfaceProxyHeaders({host: "s-other.localhost:5242", origin: "http://s-other.localhost:5242"}, authority).origin)
      .toBe("http://s-other.localhost:5242");
    expect(surfaceProxyHeaders({host: "127.0.0.1:5242", origin: "http://127.0.0.1:5242"}, authority).origin)
      .toBe("http://127.0.0.1:5242");
    expect(surfaceProxyHeaders({host: "s-editor.localhost:5242"}, authority).origin).toBeUndefined();
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

  it("routes root-relative lazy assets from the exact isolated preview host without a referrer", () => {
    const match = surfaceProxyMatch(
      "/assets/CodeEditor-DQoetr3z.js",
      undefined,
      "s-editor.localhost:5173",
    );

    expect(match).toEqual({
      authority: "s-editor.localhost:8000",
      encoded: "s-editor.localhost%3A8000",
      targetPath: "/assets/CodeEditor-DQoetr3z.js",
    });
    expect(
      surfaceProxyHeaders(
        { host: "s-editor.localhost:5173" },
        match!.authority,
        "wright_surface=editor-session",
      ),
    ).toMatchObject({
      host: "s-editor.localhost:8000",
      cookie: "wright_surface=editor-session",
    });
  });

  it.each([
    "/assets/CodeEditor-DQoetr3z.js",
    "/assets/vendor-BfeYtx4Z.css",
    "/assets/vendor-Bw7vnkIi.js",
    "/assets/codeEditorModelCache-0CJKNP2F.js",
  ])("keeps maintained Rivet lazy asset %s on the same authority", (path) => {
    expect(
      surfaceProxyMatch(path, undefined, "s-editor.localhost:5173"),
    ).toMatchObject({
      authority: "s-editor.localhost:8000",
      targetPath: path,
    });
  });

  it("does not authorize control-host, malformed, or cross-preview asset routes", () => {
    const editorAuthority = encodeURIComponent("s-editor.localhost:8000");

    expect(
      surfaceProxyMatch("/assets/vendor.js", undefined, "127.0.0.1:5173"),
    ).toBeNull();
    expect(
      surfaceProxyMatch(
        "/assets/vendor.js",
        undefined,
        "not-a-preview.localhost:5173",
      ),
    ).toBeNull();
    expect(
      surfaceProxyMatch(
        `/__wright-surface/${editorAuthority}/assets/vendor.js`,
        undefined,
        "s-other.localhost:5173",
      ),
    ).toBeNull();
  });

  it("keeps simultaneous preview authorities and cookies isolated", () => {
    const first = surfaceProxyMatch(
      "/assets/vendor.js",
      undefined,
      "s-first.localhost:5173",
    );
    const second = surfaceProxyMatch(
      "/assets/vendor.js",
      undefined,
      "s-second.localhost:5173",
    );

    expect(first?.authority).toBe("s-first.localhost:8000");
    expect(second?.authority).toBe("s-second.localhost:8000");
    expect(
      surfaceProxyHeaders({}, first!.authority, "wright_surface=first").cookie,
    ).toBe("wright_surface=first");
    expect(
      surfaceProxyHeaders({}, second!.authority, "wright_surface=second")
        .cookie,
    ).toBe("wright_surface=second");
    expect(surfaceProxyHeaders({}, first!.authority).cookie).toBeUndefined();
  });
});

import { afterEach, describe, expect, it, vi } from "vitest";
import { mkdtempSync, writeFileSync, chmodSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { EventEmitter } from "node:events";
import { privateLanRequestAllowed, privateLanWebPlugin } from "../../prototypes/desktop-harness/private-lan.vite.config";

const origin = new URL("http://192.168.1.170:5216");
const request = (headers: Record<string, string> = {}, remoteAddress = "192.168.1.20") => ({
  method: "GET", url: "/workspace/dave", headers: { host: origin.host, ...headers } as Record<string, string>,
  socket: { remoteAddress },
});
const cookie = "wright_session=test-session; HttpOnly; Path=/api; SameSite=strict";
const clientAddress = "192.168.1.20";

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

describe("private desktop web entry", () => {
  it("admits the private presentation while rejecting foreign origins, hosts, and public peers", () => {
    expect(privateLanRequestAllowed(request() as never, origin, clientAddress)).toBe(true);
    expect(privateLanRequestAllowed(request({ origin: origin.origin }) as never, origin, clientAddress)).toBe(true);
    expect(privateLanRequestAllowed(request({ origin: "http://other.example" }) as never, origin, clientAddress)).toBe(false);
    expect(privateLanRequestAllowed(request({ host: "other.example:5216" }) as never, origin, clientAddress)).toBe(false);
    expect(privateLanRequestAllowed(request({ "sec-fetch-site": "cross-site" }) as never, origin, clientAddress)).toBe(false);
    expect(privateLanRequestAllowed(request({}, "203.0.113.10") as never, origin, clientAddress)).toBe(false);
    expect(privateLanRequestAllowed(request({}, "192.168.1.21") as never, origin, clientAddress)).toBe(false);
    expect(privateLanRequestAllowed(request({ "x-forwarded-for": clientAddress }, "192.168.1.21") as never, origin, clientAddress)).toBe(false);
  });

  it.each(["http://0.0.0.0:5216", "http://203.0.113.10:5216"])("rejects broad or public binding %s", (value) => {
    expect(() => privateLanWebPlugin({ origin: value, apiTarget: "http://127.0.0.1:8116", tokenFile: "unused", clientAddress })).toThrow();
  });

  it("uses the existing session endpoint and bootstraps the page without exposing the API token", async () => {
    const directory = mkdtempSync(path.join(tmpdir(), "wright-lan-session-"));
    const tokenFile = path.join(directory, "token");
    writeFileSync(tokenFile, "private-api-fixture", { mode: 0o600 });
    const exchange = vi.fn().mockResolvedValue(new Response(null, { status: 204, headers: { "set-cookie": cookie } }));
    vi.stubGlobal("fetch", exchange);
    const use = vi.fn();
    const server = {
      config: { server: { host: origin.hostname, port: 5216 } },
      middlewares: { use }, httpServer: new EventEmitter(),
    };
    const install = privateLanWebPlugin({ origin: origin.origin, apiTarget: "http://127.0.0.1:8116", tokenFile, clientAddress }).configureServer;
    try {
      if (typeof install !== "function") throw new Error("Missing server hook");
      await install.call({} as never, server as never);
      expect(exchange.mock.calls[0][0].href).toBe("http://127.0.0.1:8116/api/auth/session");
      expect(JSON.parse(exchange.mock.calls[0][1].body)).toEqual({ token: "private-api-fixture" });
      const middleware = use.mock.calls[0][0];
      const result = { setHeader: vi.fn(), end: vi.fn(), statusCode: 200 };
      const next = vi.fn();
      middleware(request(), result, next);
      expect(result.setHeader).toHaveBeenCalledWith("Set-Cookie", cookie);
      expect(JSON.stringify(result.setHeader.mock.calls)).not.toContain("private-api-fixture");
      expect(next).toHaveBeenCalledOnce();
      const write = { ...request({ origin: origin.origin }), method: "PUT", url: "/api/workspace/workflow-sources" };
      middleware(write, result, vi.fn());
      expect(write.headers.origin).toBe("http://127.0.0.1:5216");
      const deny = vi.fn();
      middleware(request({ origin: "http://other.example" }), result, deny);
      expect(result.statusCode).toBe(403);
      expect(deny).not.toHaveBeenCalled();
      chmodSync(tokenFile, 0o644);
      await expect(install.call({} as never, server as never)).rejects.toThrow("private regular file");
      chmodSync(tokenFile, 0o600);
      exchange.mockResolvedValue(new Response(null, { status: 401 }));
      await expect(install.call({} as never, server as never)).rejects.toThrow("did not establish");
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });
});

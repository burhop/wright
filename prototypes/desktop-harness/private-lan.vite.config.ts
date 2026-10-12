import { lstatSync, readFileSync } from "node:fs";
import { isIP } from "node:net";
import type { IncomingMessage, ServerResponse } from "node:http";
import { defineConfig, mergeConfig } from "vite";
import type { Plugin, ViteDevServer } from "vite";
import webConfiguration from "../../apps/web/vite.config";

function privateAddress(address: string): boolean {
  const value = address.replace(/^::ffff:/, "");
  if (isIP(value) !== 4) return false;
  const [a, b] = value.split(".").map(Number);
  return a === 10 || (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && b === 168);
}

export function privateLanRequestAllowed(
  request: Pick<IncomingMessage, "headers" | "socket">,
  origin: URL,
  clientAddress: string,
): boolean {
  const peer = (request.socket.remoteAddress ?? "").replace(/^::ffff:/, "");
  return request.headers.host === origin.host &&
    (peer === clientAddress || peer === origin.hostname || peer === "127.0.0.1" || peer === "::1") &&
    (request.headers.origin === undefined || request.headers.origin === origin.origin) &&
    request.headers["sec-fetch-site"] !== "cross-site";
}

export function privateLanWebPlugin(options: {
  origin: string;
  apiTarget: string;
  tokenFile: string;
  clientAddress: string;
}): Plugin {
  const origin = new URL(options.origin);
  const api = new URL(options.apiTarget);
  if (!privateAddress(options.clientAddress) ||
      origin.protocol !== "http:" || !privateAddress(origin.hostname) ||
      origin.pathname !== "/" || origin.search || origin.hash || origin.username || origin.password ||
      api.protocol !== "http:" || api.hostname !== "127.0.0.1" || api.pathname !== "/" ||
      api.search || api.hash || api.username || api.password) {
    throw new Error("Private desktop view requires an exact private IPv4 origin and loopback API");
  }

  return {
    name: "wright-desktop-private-lan-session",
    apply: "serve",
    async configureServer(server: ViteDevServer) {
      if (server.config.server.host !== origin.hostname ||
          String(server.config.server.port) !== (origin.port || "80")) {
        throw new Error("Private desktop view must bind only its configured LAN address and port");
      }
      const file = lstatSync(options.tokenFile);
      if (!file.isFile() || file.isSymbolicLink() || (file.mode & 0o077) !== 0) {
        throw new Error("Private desktop credential must be a private regular file");
      }
      // Exchange the existing private API credential through its owning login
      // endpoint. Only the ordinary HttpOnly browser session reaches the UI.
      const response = await fetch(new URL("/api/auth/session", api), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: readFileSync(options.tokenFile, "utf8").trim() }),
        redirect: "error",
        signal: AbortSignal.timeout(10_000),
      });
      const cookie = response.headers.get("set-cookie");
      if (response.status !== 204 || !cookie ||
          !/^wright_session=[^;\r\n]+;/i.test(cookie) ||
          !/;\s*httponly(?:;|$)/i.test(cookie) ||
          !/;\s*path=\/api(?:;|$)/i.test(cookie) ||
          !/;\s*samesite=strict(?:;|$)/i.test(cookie)) {
        throw new Error("Wright did not establish the private desktop browser session");
      }
      const upstreamOrigin = `http://127.0.0.1:${origin.port || "80"}`;
      const admit = (request: IncomingMessage): boolean => {
        if (!privateLanRequestAllowed(request, origin, options.clientAddress)) return false;
        // Reuse the existing API's configured loopback web origin for this
        // explicitly admitted private presentation; foreign origins are denied.
        if (request.headers.origin) request.headers.origin = upstreamOrigin;
        return true;
      };
      server.middlewares.use((request: IncomingMessage, result: ServerResponse, next) => {
        if (!admit(request)) {
          result.statusCode = 403;
          result.end("Private desktop view origin is not allowed");
          return;
        }
        const pathname = new URL(request.url ?? "/", origin).pathname;
        if (request.method === "GET" && (pathname === "/" || pathname.startsWith("/workspace/"))) {
          result.setHeader("Set-Cookie", cookie);
          result.setHeader("Cache-Control", "no-store");
        }
        next();
      });
      const upgrade = (request: IncomingMessage, socket: { destroy(): void }) => {
        if (!admit(request)) socket.destroy();
      };
      server.httpServer?.prependListener("upgrade", upgrade);
      server.httpServer?.once("close", () => server.httpServer?.removeListener("upgrade", upgrade));
    },
  };
}

export default defineConfig(async (environment) => {
  if (environment.command !== "serve") throw new Error("Private desktop view is development-only");
  const origin = process.env.WRIGHT_DESKTOP_PRIVATE_WEB_ORIGIN;
  const tokenFile = process.env.WRIGHT_DESKTOP_PRIVATE_WEB_TOKEN_FILE;
  const apiTarget = process.env.WRIGHT_WEB_API_PROXY_TARGET;
  const clientAddress = process.env.WRIGHT_DESKTOP_PRIVATE_WEB_CLIENT;
  if (!origin || !tokenFile || !apiTarget || !clientAddress) throw new Error("Private desktop view configuration is missing");
  const base = typeof webConfiguration === "function"
    ? await webConfiguration(environment) : await webConfiguration;
  return mergeConfig(base, {
    plugins: [privateLanWebPlugin({ origin, tokenFile, apiTarget, clientAddress })],
  });
});

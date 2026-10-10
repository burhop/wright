import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import license from "rollup-plugin-license";
import path from "path";
import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";
import type {
  ClientRequest,
  IncomingHttpHeaders,
  IncomingMessage,
  ServerResponse,
} from "node:http";
import type { Plugin, ViteDevServer } from "vite";

const surfacePreviewHost =
  /^(?:s-[a-z0-9-]+|r-[a-f0-9]+|mcp-sandbox)\.localhost(?::\d+)?$/i;
const extraAllowedHosts = (process.env.WRIGHT_WEB_ALLOWED_HOSTS ?? "")
  .split(",")
  .map((host) => host.trim())
  .filter((host) => host.length > 0);
const apiProxyTarget =
  process.env.WRIGHT_WEB_API_PROXY_TARGET ?? "http://127.0.0.1:8000";
export function surfaceProxyConnection(target = apiProxyTarget) {
  const endpoint = new URL(target);
  return {
    protocol: endpoint.protocol,
    hostname: endpoint.hostname,
    port: endpoint.port || (endpoint.protocol === "https:" ? "443" : "80"),
  };
}

const apiProxyConnection = surfaceProxyConnection();
const apiProxyPort = apiProxyConnection.port;

function surfacePreviewHostHeader(host: string): string {
  return `${host.replace(/:\d+$/, "")}:${apiProxyPort}`;
}

const surfaceProxyPrefix = "/__wright-surface/";

export interface SurfaceProxyMatch {
  authority: string;
  encoded: string;
  targetPath: string;
}

function normalizedPreviewAuthority(host: string | undefined): string | null {
  if (!host || !surfacePreviewHost.test(host)) return null;
  return surfacePreviewHostHeader(host).toLowerCase();
}

export function surfaceProxyMatch(
  url: string | undefined,
  referer: string | undefined,
  browserHost?: string,
): SurfaceProxyMatch | null {
  const current = url ?? "/";
  const expectedAuthority = normalizedPreviewAuthority(browserHost);
  if (browserHost !== undefined && expectedAuthority === null) return null;
  if (current.startsWith(surfaceProxyPrefix)) {
    const rest = current.slice(surfaceProxyPrefix.length);
    const slash = rest.indexOf("/");
    const encoded = slash === -1 ? rest : rest.slice(0, slash);
    const targetPath = slash === -1 ? "/" : rest.slice(slash) || "/";
    try {
      const authority = decodeURIComponent(encoded);
      if (
        !validSurfaceAuthority(authority) ||
        (expectedAuthority !== null &&
          authority.toLowerCase() !== expectedAuthority)
      ) {
        return null;
      }
      return {
        authority,
        encoded,
        targetPath,
      };
    } catch {
      return null;
    }
  }
  if (!current.startsWith("/") || current.startsWith("//")) return null;
  if (referer) {
    try {
      const ref = new URL(referer);
      if (
        browserHost !== undefined &&
        ref.host.toLowerCase() !== browserHost.toLowerCase()
      ) {
        return null;
      }
      const fromRef = surfaceProxyMatch(ref.pathname, undefined, browserHost);
      if (fromRef) return { ...fromRef, targetPath: current };
    } catch {
      return null;
    }
  }
  // Rivet/Vite's lazy preload helper emits absolute /assets/* URLs. The
  // upstream host intentionally sends Referrer-Policy: no-referrer, so those
  // requests cannot recover the tunneled authority from Referer. The browser
  // preview host is already a unique, isolated presentation origin; derive
  // only its exact API authority and let the server-held cookie map authorize
  // that same presentation. Control hosts and cross-presentation prefixes are
  // rejected above.
  if (expectedAuthority === null) return null;
  return {
    authority: expectedAuthority,
    encoded: encodeURIComponent(expectedAuthority),
    targetPath: current,
  };
}

function validSurfaceAuthority(authority: string): boolean {
  return /^(?:s-[a-z0-9-]+|r-[a-f0-9]+|mcp-sandbox)\.[a-z0-9.-]+(?::\d+)?$/i.test(
    authority,
  );
}

export function rewriteSurfaceText(body: string, encoded: string): string {
  const prefix = `${surfaceProxyPrefix}${encoded}`;
  return body
    .replaceAll(
      "fetch('/__wright/bootstrap'",
      `fetch('${prefix}/__wright/bootstrap'`,
    )
    .replaceAll(
      'fetch("/__wright/bootstrap"',
      `fetch("${prefix}/__wright/bootstrap"`,
    )
    .replaceAll(
      "location.replace('/' + location.search)",
      `location.replace('${prefix}/' + location.search)`,
    )
    .replaceAll(
      'location.replace("/" + location.search)',
      `location.replace("${prefix}/" + location.search)`,
    )
    .replaceAll("location.replace('/')", `location.replace('${prefix}/')`)
    .replaceAll('location.replace("/")', `location.replace("${prefix}/")`)
    .replace(/\b(src|href|action)=("|')\/(?!\/)/g, `$1=$2${prefix}/`)
    .replace(/\burl\((["']?)\/(?!\/)/g, `url($1${prefix}/`)
    .replace(
      /(["'`])\/(assets|monacoeditorwork|manifest|favicon|locales|workers|wright-ai|__wright)\//g,
      `$1${prefix}/$2/`,
    );
}

export function surfaceProxyHeaders(
  source: IncomingHttpHeaders,
  authority: string,
  surfaceSessionCookie?: string,
): IncomingHttpHeaders {
  const headers = { ...source };
  headers.host = authority;
  // The browser sees this exact isolated preview at Vite's port; the backend
  // authorizes its original issued origin. Translate only that same-origin
  // request. Foreign/control/null origins stay unchanged and are denied there.
  if (
    typeof source.origin === "string" &&
    typeof source.host === "string" &&
    normalizedPreviewAuthority(source.host) === authority.toLowerCase()
  ) {
    for (const scheme of ["http:", "https:"]) {
      if (source.origin === `${scheme}//${source.host}`) {
        headers.origin = `${new URL(apiProxyTarget).protocol}//${authority}`;
        break;
      }
    }
  }
  headers["accept-encoding"] = "identity";
  delete headers.connection;
  const cookies = String(headers.cookie ?? "")
    .split(";")
    .map((cookie) => cookie.trim())
    .filter(
      (cookie) =>
        cookie.length > 0 &&
        !cookie.toLowerCase().startsWith("wright_surface="),
    );
  if (surfaceSessionCookie) cookies.push(surfaceSessionCookie);
  if (cookies.length > 0) headers.cookie = cookies.join("; ");
  else delete headers.cookie;
  return headers;
}

export function extractSurfaceSessionCookie(
  value: string | string[] | undefined,
): string | undefined {
  if (value === undefined) return undefined;
  const cookies = Array.isArray(value) ? value : [value];
  for (const cookie of cookies) {
    const match = /^\s*(wright_surface=[^;\r\n]*)/i.exec(cookie);
    if (match?.[1]) return match[1];
  }
  return undefined;
}

export function rewriteSurfaceSetCookies(
  value: string | string[] | undefined,
  encoded: string,
): string[] | undefined {
  if (value === undefined) return undefined;
  const prefix = `${surfaceProxyPrefix}${encoded}`;
  const cookies = Array.isArray(value) ? value : [value];
  const rewritten: string[] = [];

  for (const cookie of cookies) {
    const parts = cookie.split(";");
    const name = parts[0]?.split("=", 1)[0]?.trim();
    // The isolated preview origin is cross-site when Wright is opened at
    // 127.0.0.1. Chromium then rejects this HTTP-only iframe cookie. The dev
    // proxy keeps Wright's internal credential server-side and injects it only
    // for the matching random presentation authority.
    if (name?.toLowerCase() === "wright_surface") continue;
    let foundPath = false;
    const scoped = parts.map((part) => {
      const match = /^\s*path\s*=\s*(.*)$/i.exec(part);
      if (!match) return part;
      foundPath = true;
      const pathValue = match[1]?.trim() || "/";
      const absolutePath = pathValue.startsWith("/")
        ? pathValue
        : `/${pathValue}`;
      return ` Path=${prefix}${absolutePath}`;
    });
    if (!foundPath) scoped.push(` Path=${prefix}/`);
    rewritten.push(scoped.join(";"));
  }

  return rewritten;
}

export function surfaceProxyResponseBody(
  body: Buffer,
  headers: IncomingHttpHeaders,
  encoded: string,
): Buffer {
  // Recorded evidence keeps its owning reader's exact bytes and declared size.
  // JSON evidence may contain URLs; rewriting it would invalidate its digest.
  if (headers["x-wright-artifact-sha256"] !== undefined) return body;
  const contentType = String(headers["content-type"] ?? "");
  if (
    contentType.includes("text/html") ||
    contentType.includes("text/css") ||
    contentType.includes("javascript") ||
    contentType.includes("application/json")
  ) {
    body = Buffer.from(
      rewriteSurfaceText(body.toString("utf-8"), encoded),
      "utf-8",
    );
    delete headers["content-security-policy"];
  }
  // The development proxy buffers finite responses; rewritten text needs its
  // actual UTF-8 size and must not advertise both length and chunked framing.
  delete headers["transfer-encoding"];
  headers["content-length"] = String(body.byteLength);
  return body;
}

export function surfaceDevProxyPlugin(): Plugin {
  const surfaceSessions = new Map<string, string>();
  const install = (server: Pick<ViteDevServer, "middlewares">) => {
    server.middlewares.use(
      (req: IncomingMessage, res: ServerResponse, next) => {
        const match = surfaceProxyMatch(
          req.url,
          typeof req.headers.referer === "string"
            ? req.headers.referer
            : undefined,
          req.headers.host,
        );
        if (!match) {
          next();
          return;
        }
        if (!validSurfaceAuthority(match.authority)) {
          res.statusCode = 400;
          res.end("Invalid surface preview host");
          return;
        }

        const headers = surfaceProxyHeaders(
          req.headers,
          match.authority,
          surfaceSessions.get(match.authority),
        );

        const request =
          apiProxyConnection.protocol === "https:" ? httpsRequest : httpRequest;
        const proxyReq = request(
          {
            ...apiProxyConnection,
            method: req.method,
            path: match.targetPath,
            headers,
          },
          (proxyRes) => {
            const chunks: Buffer[] = [];
            proxyRes.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
            proxyRes.on("end", () => {
              let body: Buffer = Buffer.concat(chunks);
              const outgoing = { ...proxyRes.headers };
              const surfaceSession = extractSurfaceSessionCookie(
                outgoing["set-cookie"],
              );
              if (surfaceSession) {
                if (surfaceSessions.size >= 256) {
                  const oldest = surfaceSessions.keys().next().value;
                  if (oldest) surfaceSessions.delete(oldest);
                }
                surfaceSessions.set(match.authority, surfaceSession);
              } else if (proxyRes.statusCode === 401) {
                surfaceSessions.delete(match.authority);
              }
              const scopedCookies = rewriteSurfaceSetCookies(
                outgoing["set-cookie"],
                match.encoded,
              );
              if (scopedCookies === undefined || scopedCookies.length === 0) {
                delete outgoing["set-cookie"];
              } else {
                outgoing["set-cookie"] = scopedCookies;
              }
              if (
                typeof outgoing.location === "string" &&
                outgoing.location.startsWith("/")
              ) {
                outgoing.location = `${surfaceProxyPrefix}${match.encoded}${outgoing.location}`;
              }
              body = surfaceProxyResponseBody(body, outgoing, match.encoded);
              res.writeHead(proxyRes.statusCode ?? 502, outgoing);
              res.end(body);
            });
          },
        );
        proxyReq.on("error", (error) => {
          res.statusCode = 502;
          res.end(`Surface preview proxy failed: ${error.message}`);
        });
        req.pipe(proxyReq);
      },
    );
  };
  return {
    name: "wright-surface-dev-proxy",
    configureServer: install,
    configurePreviewServer: install,
  };
}

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  const isBuild = command === "build";
  const isDesktop =
    process.env.BUILD_TARGET === "desktop" || mode === "desktop";
  // Resolve after Vite applies CLI overrides so isolated verification builds
  // write their license artifact beside their own bundle, not into served dist.
  const licenseOutput = {
    file: "third-party-licenses-web.txt",
    encoding: "utf-8",
  };
  const licenseOutputResolver: Plugin = {
    name: "wright-web-license-output",
    configResolved(config) {
      licenseOutput.file = path.resolve(
        isBuild
          ? path.resolve(config.root, config.build.outDir)
          : config.publicDir,
        "third-party-licenses-web.txt",
      );
    },
  };

  return {
    base: isDesktop ? "./" : "/",
    plugins: [
      react(),
      surfaceDevProxyPlugin(),
      licenseOutputResolver,
      license({ thirdParty: { output: licenseOutput } }),
    ],
    build: {
      outDir: isDesktop ? "dist-desktop" : "dist",
    },
    server: {
      allowedHosts: ["promaxgb10-9666", ".localhost", ...extraAllowedHosts],
      proxy: {
        "^/(?!api(?:/|$)).*": {
          target: apiProxyTarget,
          changeOrigin: false,
          ws: true,
          bypass(req: IncomingMessage) {
            const host = String(req.headers.host ?? "");
            if (surfacePreviewHost.test(host)) return undefined;
            return req.url ?? "/";
          },
          configure(proxy) {
            const forwardSurfaceHost = (
              proxyReq: ClientRequest,
              req: IncomingMessage,
            ) => {
              const host = String(req.headers.host ?? "");
              if (surfacePreviewHost.test(host)) {
                proxyReq.setHeader("host", surfacePreviewHostHeader(host));
              }
            };
            proxy.on("proxyReq", forwardSurfaceHost);
            proxy.on("proxyReqWs", forwardSurfaceHost);
          },
        },
        "/api": {
          target: apiProxyTarget,
          changeOrigin: true,
          ws: true,
        },
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      // The workflow recovery interaction suite performs several complete
      // user-event sequences. Keep the timeout bounded but realistic on
      // shared and Windows CI runners where JSDOM workers contend for CPU.
      testTimeout: 30_000,
      // Bound JSDOM concurrency: unrestricted workers cause CPU starvation and
      // delayed effects on the same shared hosts used by local and CI gates.
      maxWorkers: 2,
      environmentOptions: {
        jsdom: {
          url: "http://localhost/",
        },
      },
      setupFiles: "./src/test/setup.ts",
    },
  };
});

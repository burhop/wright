import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import license from "rollup-plugin-license";
import path from "path";
import { request as httpRequest } from "node:http";
import type {
  ClientRequest,
  IncomingHttpHeaders,
  IncomingMessage,
  ServerResponse,
} from "node:http";
import type { Plugin } from "vite";

const surfacePreviewHost =
  /^(?:s-[a-z0-9-]+|r-[a-f0-9]+|mcp-sandbox)\.localhost(?::\d+)?$/i;
const extraAllowedHosts = (process.env.WRIGHT_WEB_ALLOWED_HOSTS ?? "")
  .split(",")
  .map((host) => host.trim())
  .filter((host) => host.length > 0);

function surfacePreviewHostHeader(host: string): string {
  return `${host.replace(/:\d+$/, "")}:8000`;
}

const surfaceProxyPrefix = "/__wright-surface/";

function surfaceProxyMatch(
  url: string | undefined,
  referer: string | undefined,
): { authority: string; encoded: string; targetPath: string } | null {
  const current = url ?? "/";
  if (current.startsWith(surfaceProxyPrefix)) {
    const rest = current.slice(surfaceProxyPrefix.length);
    const slash = rest.indexOf("/");
    const encoded = slash === -1 ? rest : rest.slice(0, slash);
    const targetPath = slash === -1 ? "/" : rest.slice(slash) || "/";
    try {
      return {
        authority: decodeURIComponent(encoded),
        encoded,
        targetPath,
      };
    } catch {
      return null;
    }
  }
  if (!referer || !current.startsWith("/")) return null;
  try {
    const ref = new URL(referer);
    const fromRef = surfaceProxyMatch(ref.pathname, undefined);
    if (!fromRef) return null;
    return { ...fromRef, targetPath: current };
  } catch {
    return null;
  }
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

function surfaceDevProxyPlugin(): Plugin {
  const surfaceSessions = new Map<string, string>();
  return {
    name: "wright-surface-dev-proxy",
    configureServer(server) {
      server.middlewares.use(
        (req: IncomingMessage, res: ServerResponse, next) => {
          const match = surfaceProxyMatch(
            req.url,
            typeof req.headers.referer === "string"
              ? req.headers.referer
              : undefined,
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

          const proxyReq = httpRequest(
            {
              hostname: "127.0.0.1",
              port: 8000,
              method: req.method,
              path: match.targetPath,
              headers,
            },
            (proxyRes) => {
              const chunks: Buffer[] = [];
              proxyRes.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
              proxyRes.on("end", () => {
                const contentType = String(
                  proxyRes.headers["content-type"] ?? "",
                );
                const textLike =
                  contentType.includes("text/html") ||
                  contentType.includes("text/css") ||
                  contentType.includes("javascript") ||
                  contentType.includes("application/json");
                let body = Buffer.concat(chunks);
                const outgoing = { ...proxyRes.headers };
                delete outgoing["content-length"];
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
                if (textLike) {
                  body = Buffer.from(
                    rewriteSurfaceText(body.toString("utf-8"), match.encoded),
                    "utf-8",
                  );
                  delete outgoing["content-security-policy"];
                }
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
    },
  };
}

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  const isBuild = command === "build";
  const isDesktop =
    process.env.BUILD_TARGET === "desktop" || mode === "desktop";

  return {
    base: isDesktop ? "./" : "/",
    plugins: [
      react(),
      surfaceDevProxyPlugin(),
      license({
        thirdParty: {
          output: {
            file: isBuild
              ? path.resolve(
                  __dirname,
                  isDesktop
                    ? "dist-desktop/third-party-licenses-web.txt"
                    : "dist/third-party-licenses-web.txt",
                )
              : path.resolve(__dirname, "public/third-party-licenses-web.txt"),
            encoding: "utf-8",
          },
        },
      }),
    ],
    build: {
      outDir: isDesktop ? "dist-desktop" : "dist",
    },
    server: {
      allowedHosts: ["promaxgb10-9666", ".localhost", ...extraAllowedHosts],
      proxy: {
        "^/(?!api(?:/|$)).*": {
          target: "http://127.0.0.1:8000",
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
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
          ws: true,
        },
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
    },
  };
});

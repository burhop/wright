(() => {
  "use strict";

  const params = new URLSearchParams(window.location.search);
  const hostOrigin = params.get("hostOrigin");
  const surfaceId = params.get("surfaceId");
  const generation = Number(params.get("generation"));
  const nonce = params.get("nonce");
  let innerFrame = null;
  let resourceAccepted = false;

  function validBootstrap() {
    if (!hostOrigin || !surfaceId || !nonce || !Number.isSafeInteger(generation)) {
      return false;
    }
    try {
      const parsed = new URL(hostOrigin);
      return parsed.origin === hostOrigin && parsed.origin !== "null";
    } catch {
      return false;
    }
  }

  function envelope(method, paramsValue) {
    return {
      jsonrpc: "2.0",
      method,
      params: paramsValue,
      _wright: { version: 1, surfaceId, generation, nonce },
    };
  }

  function isJsonRpc(value) {
    return (
      value !== null &&
      typeof value === "object" &&
      value.jsonrpc === "2.0" &&
      (typeof value.method === "string" || "result" in value || "error" in value)
    );
  }

  function matchesEnvelope(value) {
    const marker = value && value._wright;
    return (
      marker &&
      marker.version === 1 &&
      marker.surfaceId === surfaceId &&
      marker.generation === generation &&
      marker.nonce === nonce
    );
  }

  function injectPolicy(html, contentSecurityPolicy) {
    const escaped = contentSecurityPolicy
      .replaceAll("&", "&amp;")
      .replaceAll('"', "&quot;");
    const policy = `<meta http-equiv="Content-Security-Policy" content="${escaped}"><meta name="referrer" content="no-referrer">`;
    const head = /<head(?:\s[^>]*)?>/i;
    return head.test(html)
      ? html.replace(head, (match) => `${match}${policy}`)
      : `<!doctype html><html><head>${policy}</head><body>${html}</body></html>`;
  }

  function validatedDomains(values, connect) {
    if (values === undefined) return [];
    if (!Array.isArray(values) || values.length > 32) throw new Error("Invalid CSP domains");
    return [...new Set(values.map((value) => {
      if (typeof value !== "string" || value.length > 512 || /\s|'|"|;/.test(value)) {
        throw new Error("Invalid CSP domain");
      }
      const parsed = new URL(value);
      if (!(connect ? ["https:", "wss:"] : ["https:"]).includes(parsed.protocol)) {
        throw new Error("Invalid CSP scheme");
      }
      if (parsed.username || parsed.password || parsed.pathname !== "/" || parsed.search || parsed.hash) {
        throw new Error("CSP source must be an origin");
      }
      const wildcard = parsed.hostname.startsWith("*.");
      const hostname = wildcard ? parsed.hostname.slice(2) : parsed.hostname;
      if (!hostname.includes(".") || hostname.endsWith(".local") || hostname.includes("*") || /^\d+(?:\.\d+){3}$/.test(hostname)) {
        throw new Error("CSP source must be a public DNS origin");
      }
      return `${parsed.protocol}//${wildcard ? "*." : ""}${hostname}${parsed.port ? `:${parsed.port}` : ""}`;
    }))];
  }

  function sandboxPolicy(cspValue, permissionsValue) {
    const csp = cspValue || {};
    const expectedCsp = new Set(["connectDomains", "resourceDomains", "frameDomains", "baseUriDomains"]);
    if (typeof csp !== "object" || Object.keys(csp).some((key) => !expectedCsp.has(key))) {
      throw new Error("Unsupported CSP declaration");
    }
    const connect = validatedDomains(csp.connectDomains, true);
    const resources = validatedDomains(csp.resourceDomains, false);
    const frames = validatedDomains(csp.frameDomains, false);
    const bases = validatedDomains(csp.baseUriDomains, false);
    const source = (values) => values.length ? values.join(" ") : "'none'";
    const policy = [
      "default-src 'none'",
      `connect-src ${source(connect)}`,
      `script-src 'unsafe-inline' ${source(resources)}`,
      `style-src 'unsafe-inline' ${source(resources)}`,
      `img-src data: blob: ${source(resources)}`,
      `font-src ${source(resources)}`,
      `media-src blob: ${source(resources)}`,
      `worker-src blob: ${source(resources)}`,
      `frame-src ${source(frames)}`,
      `child-src ${source(frames)}`,
      `base-uri ${bases.length ? bases.join(" ") : "'self'"}`,
      "object-src 'none'",
      "form-action 'none'",
      "manifest-src 'none'",
      "frame-ancestors 'none'",
    ].join("; ");
    const permissions = permissionsValue || {};
    const known = new Set(["camera", "microphone", "geolocation", "clipboardWrite"]);
    if (
      typeof permissions !== "object" ||
      Object.entries(permissions).some(([key, value]) =>
        !known.has(key) || !value || typeof value !== "object" || Object.keys(value).length)
    ) {
      throw new Error("Unsupported permission declaration");
    }
    const granted = new Set(Object.keys(permissions));
    return {
      policy,
      allow: [
        ["camera", "camera"],
        ["microphone", "microphone"],
        ["geolocation", "geolocation"],
        ["clipboard-write", "clipboardWrite"],
      ].filter(([, key]) => granted.has(key)).map(([feature]) => feature).join("; "),
      permissionsPolicy: [
        ["camera", "camera"],
        ["microphone", "microphone"],
        ["geolocation", "geolocation"],
        ["clipboard-write", "clipboardWrite"],
      ].map(([feature, key]) => `${feature}=(${granted.has(key) ? "self" : ""})`).join(", "),
    };
  }

  function mountResource(message) {
    if (resourceAccepted) return;
    const payload = message.params;
    if (!payload || typeof payload.html !== "string" || payload.sandbox !== "allow-scripts") {
      return;
    }
    let policy;
    try {
      policy = sandboxPolicy(payload.csp, payload.permissions);
    } catch {
      return;
    }
    resourceAccepted = true;
    const frame = document.createElement("iframe");
    frame.title = "MCP App view";
    frame.sandbox.value = payload.sandbox;
    frame.setAttribute("referrerpolicy", "no-referrer");
    frame.setAttribute("allow", policy.allow);
    frame.setAttribute("data-permissions-policy", policy.permissionsPolicy);
    frame.srcdoc = injectPolicy(payload.html, policy.policy);
    document.body.replaceChildren(frame);
    innerFrame = frame;
  }

  if (!validBootstrap() || window.parent === window) {
    document.body.textContent = "Invalid sandbox bootstrap.";
    return;
  }

  window.addEventListener("message", (event) => {
    if (
      event.source === window.parent &&
      event.origin === hostOrigin &&
      isJsonRpc(event.data) &&
      matchesEnvelope(event.data)
    ) {
      if (event.data.method === "ui/notifications/sandbox-resource-ready") {
        mountResource(event.data);
        return;
      }
      if (innerFrame?.contentWindow) {
        const forwarded = { ...event.data };
        delete forwarded._wright;
        innerFrame.contentWindow.postMessage(forwarded, "*");
      }
      return;
    }
    if (
      innerFrame?.contentWindow &&
      event.source === innerFrame.contentWindow &&
      event.origin === "null" &&
      isJsonRpc(event.data)
    ) {
      window.parent.postMessage(
        { ...event.data, _wright: { version: 1, surfaceId, generation, nonce } },
        hostOrigin,
      );
    }
  });

  document.body.dataset.proxyReady = "true";
  window.parent.postMessage(
    envelope("ui/notifications/sandbox-proxy-ready", {}),
    hostOrigin,
  );
})();

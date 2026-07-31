import { expect, test, type Frame, type Page } from "@playwright/test";

const sandboxOrigin = "http://wright-sandbox.localhost:5173";
const envelope = {
  version: 1,
  surfaceId: "surface-sandbox-test",
  generation: 2,
  nonce: "abcdefghijklmnopqrstuvwxyz123456",
};

async function mountOuter(page: Page): Promise<Frame> {
  await page.goto("/");
  await page.setContent("<!doctype html><title>Sandbox host test</title><main></main>");
  await page.evaluate(
    ({ sandboxOriginValue, envelopeValue }) => {
      const frame = document.createElement("iframe");
      frame.id = "outer-sandbox";
      frame.sandbox.value = "allow-scripts allow-same-origin";
      frame.referrerPolicy = "no-referrer";
      frame.allow = "camera *; microphone 'none'; geolocation 'none'; clipboard-write 'none'";
      const url = new URL("/surface-sandbox/index.html", sandboxOriginValue);
      url.searchParams.set("hostOrigin", window.location.origin);
      url.searchParams.set("surfaceId", envelopeValue.surfaceId);
      url.searchParams.set("generation", String(envelopeValue.generation));
      url.searchParams.set("nonce", envelopeValue.nonce);
      frame.src = url.href;
      (window as Window & { sandboxMessages?: unknown[] }).sandboxMessages = [];
      window.addEventListener("message", (event) => {
        if (event.source === frame.contentWindow && event.origin === sandboxOriginValue) {
          (window as Window & { sandboxMessages: unknown[] }).sandboxMessages.push(event.data);
        }
      });
      document.querySelector("main")?.append(frame);
    },
    { sandboxOriginValue: sandboxOrigin, envelopeValue: envelope },
  );
  await expect.poll(() => page.frames().some((frame) => frame.url().startsWith(sandboxOrigin))).toBe(true);
  const outer = page.frames().find((frame) => frame.url().startsWith(sandboxOrigin));
  if (!outer) throw new Error("outer sandbox did not load on its distinct origin");
  await expect.poll(() => outer.evaluate(() => document.body.dataset.proxyReady)).toBe("true");
  await expect
    .poll(() =>
      page.evaluate(() =>
        (window as Window & { sandboxMessages?: Array<{ method?: string }> })
          .sandboxMessages?.some(
            (message) => message.method === "ui/notifications/sandbox-proxy-ready",
          ),
      ),
    )
    .toBe(true);
  return outer;
}

async function sendToOuter(
  page: Page,
  message: Record<string, unknown>,
): Promise<void> {
  await page.evaluate(
    ({ sandboxOriginValue, envelopeValue, messageValue }) => {
      const frame = document.querySelector<HTMLIFrameElement>("#outer-sandbox");
      frame?.contentWindow?.postMessage(
        { ...messageValue, _wright: envelopeValue },
        sandboxOriginValue,
      );
    },
    {
      sandboxOriginValue: sandboxOrigin,
      envelopeValue: envelope,
      messageValue: message,
    },
  );
}

test("uses a distinct-origin double iframe with restrictive defaults", async ({ page }) => {
  const attempted: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("undeclared.invalid")) attempted.push(request.url());
  });
  const outer = await mountOuter(page);
  expect(new URL(outer.url()).origin).not.toBe(new URL(page.url()).origin);

  await sendToOuter(page, {
    jsonrpc: "2.0",
    method: "ui/notifications/sandbox-resource-ready",
    params: {
      html: `<!doctype html><html><body>
        <main id="app">sandboxed app</main>
        <object data="https://undeclared.invalid/plugin"></object>
        <iframe src="https://undeclared.invalid/frame"></iframe>
        <script>
          window.received = [];
          addEventListener("message", (event) => window.received.push(event.data));
          fetch("https://undeclared.invalid/data")
            .then(() => window.fetchState = "allowed")
            .catch(() => window.fetchState = "blocked");
        </script>
      </body></html>`,
      sandbox: "allow-scripts",
      csp: {},
      permissions: {},
    },
  });

  await expect.poll(() => outer.childFrames().length).toBe(1);
  const inner = outer.childFrames()[0];
  expect(inner).toBeDefined();
  await expect.poll(() => inner.evaluate(() => document.querySelector("#app")?.textContent)).toBe(
    "sandboxed app",
  );
  await expect.poll(() => inner.evaluate(() => (window as Window & { fetchState?: string }).fetchState)).toBe(
    "blocked",
  );
  expect(attempted).toEqual([]);
  const innerElement = await outer.locator("iframe").first();
  await expect(innerElement).toHaveAttribute("sandbox", "allow-scripts");
  await expect(innerElement).not.toHaveAttribute("allowfullscreen");
  await expect(innerElement).toHaveAttribute(
    "data-permissions-policy",
    "camera=(), microphone=(), geolocation=(), clipboard-write=()",
  );
  expect(await inner.evaluate(() => window.origin)).toBe("null");
});

test("rejects invalid domain and permission declarations before mounting content", async ({ page }) => {
  const outer = await mountOuter(page);
  await sendToOuter(page, {
    jsonrpc: "2.0",
    method: "ui/notifications/sandbox-resource-ready",
    params: {
      html: "<p>must not mount</p>",
      sandbox: "allow-scripts",
      csp: { connectDomains: ["http://169.254.169.254"] },
      permissions: { usb: {} },
    },
  });
  await page.waitForTimeout(100);
  expect(outer.childFrames()).toHaveLength(0);

  await sendToOuter(page, {
    jsonrpc: "2.0",
    method: "ui/notifications/sandbox-resource-ready",
    params: {
      html: "<p id='valid'>valid resource</p>",
      sandbox: "allow-scripts",
      csp: { resourceDomains: ["https://cdn.example.test"] },
      permissions: { camera: {} },
    },
  });
  await expect.poll(() => outer.childFrames().length).toBe(1);
  await expect(outer.locator("iframe")).toHaveAttribute("allow", "camera");
});

test("drops host messages sent before resource initialization", async ({ page }) => {
  const outer = await mountOuter(page);
  await sendToOuter(page, {
    jsonrpc: "2.0",
    method: "ui/notifications/tool-input",
    params: { arguments: { phase: "early" } },
  });
  await sendToOuter(page, {
    jsonrpc: "2.0",
    method: "ui/notifications/sandbox-resource-ready",
    params: {
      html: `<script>
        window.received = [];
        addEventListener("message", (event) => window.received.push(event.data));
      </script>`,
      sandbox: "allow-scripts",
      csp: {},
      permissions: {},
    },
  });
  await expect.poll(() => outer.childFrames().length).toBe(1);
  const inner = outer.childFrames()[0];
  await expect.poll(() => inner.evaluate(() => Array.isArray((window as Window & { received?: unknown[] }).received))).toBe(true);
  expect(await inner.evaluate(() => (window as Window & { received: unknown[] }).received)).toEqual([]);

  await sendToOuter(page, {
    jsonrpc: "2.0",
    method: "ui/notifications/tool-input",
    params: { arguments: { phase: "ready" } },
  });
  await expect
    .poll(() =>
      inner.evaluate(
        () => (window as Window & { received: Array<{ method?: string }> }).received[0]?.method,
      ),
    )
    .toBe("ui/notifications/tool-input");
});

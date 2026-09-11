import { afterEach, describe, expect, it, vi } from "vitest";
import { PanelHostImpl } from "../panel-host";
import { IframeProvider } from "../providers/iframe-provider";

describe("viewer heartbeat eligibility", () => {
  afterEach(() => vi.useRealTimers());

  it("does not time out an ordinary HTML document that has no heartbeat protocol", () => {
    vi.useFakeTimers();
    const container = document.createElement("div");
    container.appendChild(document.createElement("iframe"));
    document.body.appendChild(container);
    const provider = new IframeProvider();
    const file = { id: "report.html", uri: "report.html", name: "report.html", extension: "html", mimeType: "text/html" };
    const host = new PanelHostImpl("report", "Report", container, true, true, provider.getCapabilities(file, "preview").supportsHeartbeat === true);
    const unresponsive = vi.fn();
    const ping = vi.spyOn(host, "postMessage");
    host.onDidBecomeUnresponsive(unresponsive);
    try {
      vi.advanceTimersByTime(15_000);
      expect(ping).not.toHaveBeenCalled();
      expect(unresponsive).not.toHaveBeenCalled();
    } finally { host.dispose(); container.remove(); }
  });

  it("still detects an opted-in viewer that stops responding and recovers on its pong", () => {
    vi.useFakeTimers();
    const container = document.createElement("div");
    const iframe = document.createElement("iframe");
    container.appendChild(iframe);
    document.body.appendChild(container);
    const host = new PanelHostImpl("app", "App", container, true, true, true);
    const unresponsive = vi.fn();
    const responsive = vi.fn();
    host.onDidBecomeUnresponsive(unresponsive);
    host.onDidBecomeResponsive(responsive);
    try {
      vi.advanceTimersByTime(3_000);
      expect(unresponsive).toHaveBeenCalledOnce();
      window.dispatchEvent(new MessageEvent("message", { source: window, data: { type: "pong" } }));
      expect(responsive).not.toHaveBeenCalled();
      window.dispatchEvent(new MessageEvent("message", { source: iframe.contentWindow, data: { type: "pong" } }));
      expect(responsive).toHaveBeenCalledOnce();
      host.dispose();
      vi.advanceTimersByTime(10_000);
      expect(unresponsive).toHaveBeenCalledOnce();
    } finally { host.dispose(); container.remove(); }
  });
});

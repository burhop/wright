/** Native frame connection. Messages are locators; native owners resolve authority. */
import { assertContract, type NavigationTarget } from "@wright/process-client";
import type { ProcessInterfacePresentation } from "./process-ui-authoring";

const version = "wright.process-host/1";
const themeKeys = ["color-scheme", "--color-neutral", "--color-surface", "--color-surface-elevated", "--color-surface-subtle",
  "--color-primary", "--color-secondary", "--color-accent", "--color-border", "--color-success", "--color-warning",
  "--color-error", "--color-text-muted", "--font-size-md", "--space-md", "--space-lg", "--radius-md"];
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === "object" && !Array.isArray(value);
const identifier = (value: unknown): value is string => typeof value === "string" && /^[a-z0-9][a-z0-9._:-]{0,159}$/i.test(value);

export interface ProcessPresentationHostPorts {
  readonly ready: () => void;
  readonly started: (requestId?: string) => void | Promise<void>;
  readonly navigate?: (target: NavigationTarget) => void | Promise<void>;
  readonly failed: (error: unknown) => void;
}
export function connectProcessPresentation(frame: HTMLIFrameElement, view: ProcessInterfacePresentation,
  ports: ProcessPresentationHostPorts): () => void {
  const origin = new URL(view.launch.absoluteBootstrapUrl).origin;
  let nonce = crypto.randomUUID();
  let disposed = false, ready = false, attempts = 0;
  let timer: ReturnType<typeof setInterval> | undefined;
  const requests = new Set<string>();
  const send = (type: "hello" | "theme") => {
    if (disposed) return;
    const style = getComputedStyle(document.documentElement);
    const tokens = Object.fromEntries(themeKeys.map(key => [key, style.getPropertyValue(key).trim()])
      .filter(([key, value]) => value.length > 0 && value.length <= 128 && !/[;{}@]|url\s*\(/i.test(value) &&
        (key !== "color-scheme" || value === "dark" || value === "light")));
    frame.contentWindow?.postMessage({schema_version: version, nonce, presentation_id: view.launch.presentationId,
      generation: view.launch.generation, type, tokens}, origin);
  };
  const invoke = (fn: () => void | Promise<void>) => {
    try {void Promise.resolve(fn()).catch(error => {if (!disposed) ports.failed(error);});}
    catch (error) {if (!disposed) ports.failed(error);}
  };
  const receive = (event: MessageEvent) => {
    if (disposed || event.source !== frame.contentWindow || event.origin !== origin || !object(event.data)) return;
    const value = event.data;
    if (value.schema_version !== version || value.nonce !== nonce || value.presentation_id !== view.launch.presentationId ||
      value.generation !== view.launch.generation || Object.keys(value).some(key =>
        !["schema_version", "nonce", "presentation_id", "generation", "type", "request_id", "target"].includes(key))) return;
    if (value.type === "ready" && value.request_id === undefined && value.target === undefined) {
      if (ready) return;
      ready = true; clearInterval(timer); ports.ready();
      if (!view.binding.read_only && view.binding.run_id === null) invoke(() => ports.started());
    } else if (ready && value.type === "started" && value.target === undefined && identifier(value.request_id)) {
      if (view.binding.read_only || view.binding.run_id !== null || requests.has(value.request_id)) return;
      const requestId = value.request_id; requests.add(requestId);
      invoke(() => ports.started(requestId));
    } else if (ready && value.type === "navigate" && value.request_id === undefined && ports.navigate) {
      try {
        const target = assertContract("NavigationTarget", value.target);
        if (target.run_id !== undefined && target.run_id !== null && target.run_id !== view.binding.run_id) return;
        invoke(() => ports.navigate!(target));
      } catch { /* Malformed frame messages have no native effect. */ }
    }
  };
  const connect = () => {
    clearInterval(timer); attempts = 0;
    // Every frame document can mount asynchronously after load. Re-arm a
    // bounded handshake; receipt reads never submit or resume process work.
    timer = setInterval(() => {if (++attempts >= 120) clearInterval(timer); send("hello");}, 250);
    send("hello");
  };
  const loaded = () => {
    if (disposed) return;
    nonce = crypto.randomUUID(); ready = false; connect();
  };
  frame.addEventListener("load", loaded);
  // Bounded hello handles the authenticated bootstrap redirect and async mount.
  window.addEventListener("message", receive);
  const theme = new MutationObserver(() => {if (ready) send("theme");});
  theme.observe(document.documentElement, {attributes: true, attributeFilter: ["class", "style", "data-theme"]});
  connect();
  return () => {disposed = true; clearInterval(timer); theme.disconnect(); frame.removeEventListener("load", loaded); window.removeEventListener("message", receive);};
}

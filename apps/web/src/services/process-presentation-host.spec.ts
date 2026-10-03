import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { connectProcessPresentation } from "./process-presentation-host";
import { authoringPresentation as view } from "../../tests/fixtures/process-ui-authoring";

const origin = new URL(view.launch.absoluteBootstrapUrl).origin;
function fixture(readOnly = false) {
  const frame = document.createElement("iframe"); document.body.append(frame);
  const post = vi.spyOn(frame.contentWindow!, "postMessage").mockImplementation(() => {});
  const ports = {ready: vi.fn(), started: vi.fn(async () => {}), navigate: vi.fn(async () => {}), failed: vi.fn()};
  const dispose = connectProcessPresentation(frame, {...view, binding: {...view.binding, read_only: readOnly}}, ports);
  const hello = post.mock.calls[0][0] as Record<string, unknown>;
  const message = (type: string, extra: Record<string, unknown> = {}, eventOrigin = origin, source: MessageEventSource | null = frame.contentWindow) =>
    window.dispatchEvent(new MessageEvent("message", {origin: eventOrigin, source,
      data: {schema_version: hello.schema_version, nonce: hello.nonce, presentation_id: hello.presentation_id,
        generation: hello.generation, type, ...extra}}));
  return {frame, post, ports, dispose, hello, message};
}
describe("native exact process frame connection", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {vi.useRealTimers(); document.body.replaceChildren();});

  it("accepts only exact origin, window, nonce, presentation and generation", () => {
    const f = fixture();
    f.message("ready", {}, "https://foreign.invalid"); f.message("ready", {}, origin, window);
    for (const extra of [{nonce: "wrong"}, {presentation_id: "other"}, {generation: 2}, {invokeTool: "forbidden"}]) f.message("ready", extra);
    expect(f.ports.ready).not.toHaveBeenCalled(); expect(f.ports.started).not.toHaveBeenCalled();
    f.message("ready"); f.message("ready");
    expect(f.ports.ready).toHaveBeenCalledOnce(); expect(f.ports.started).toHaveBeenCalledExactlyOnceWith();
    f.dispose(); f.message("started", {request_id: "start-one"});
    expect(f.ports.started).toHaveBeenCalledTimes(1);
  });

  it("start signals carry request locators, never browser-provided run authority", () => {
    const f = fixture(); f.message("started", {request_id: "start-one"});
    expect(f.ports.started).not.toHaveBeenCalled(); f.message("ready");
    f.message("started", {request_id: "start-one", run_id: "invented"});
    f.message("started", {request_id: "../outside"});
    f.message("started", {request_id: "start-one"}); f.message("started", {request_id: "start-one"});
    expect(f.ports.started.mock.calls).toEqual([[], ["start-one"]]);
    f.dispose();
  });

  it("preview readiness cannot request start attachment", () => {
    const f = fixture(true); f.message("ready"); f.message("started", {request_id: "start-one"});
    expect(f.ports.ready).toHaveBeenCalledOnce(); expect(f.ports.started).not.toHaveBeenCalled(); f.dispose();
  });

  it("navigation is closed and cannot select an unbound run", () => {
    const f = fixture(); f.message("ready");
    f.message("navigate", {target: {kind: "block", block_id: "geometry", run_id: "foreign-run"}});
    f.message("navigate", {target: {kind: "block", block_id: "geometry", path: "../outside"}});
    f.message("navigate", {target: {kind: "block", block_id: "geometry"}});
    expect(f.ports.navigate).toHaveBeenCalledExactlyOnceWith({kind: "block", block_id: "geometry"}); f.dispose();
  });

  it("sends bounded allowlisted theme values and stops hello attempts when disposed", () => {
    document.documentElement.style.setProperty("--color-primary", "#ffffff");
    document.documentElement.style.setProperty("--color-neutral", "url(https://foreign.invalid)");
    document.documentElement.style.setProperty("--private-token", "secret");
    const f = fixture();
    expect(f.hello.tokens).toEqual({"--color-primary": "#ffffff"});
    vi.advanceTimersByTime(40_000); expect(f.post).toHaveBeenCalledTimes(121);
    f.dispose(); const calls = f.post.mock.calls.length;
    f.frame.dispatchEvent(new Event("load")); vi.advanceTimersByTime(10_000);
    expect(f.post).toHaveBeenCalledTimes(calls);
    document.documentElement.removeAttribute("style");
  });

  it.each(["light", "dark"])("sends the selected %s browser-control scheme", scheme => {
    document.documentElement.style.setProperty("color-scheme", scheme);
    const f = fixture(true);
    try {
      expect(f.hello.tokens).toMatchObject({"color-scheme": scheme});
      f.message("ready");
      expect(f.ports.started).not.toHaveBeenCalled();
    } finally {f.dispose(); document.documentElement.style.removeProperty("color-scheme");}
  });

  it.each(["normal", "light dark"])("does not send the unsupported %s scheme", scheme => {
    document.documentElement.style.setProperty("color-scheme", scheme);
    const f = fixture(true);
    try {expect(f.hello.tokens).not.toHaveProperty("color-scheme");}
    finally {f.dispose(); document.documentElement.style.removeProperty("color-scheme");}
  });

  it("updates a ready frame's browser-control scheme without a process action", async () => {
    document.documentElement.style.setProperty("color-scheme", "dark");
    const f = fixture(true);
    try {
      f.message("ready");
      document.documentElement.style.setProperty("color-scheme", "light");
      await Promise.resolve();
      expect(f.post.mock.calls.at(-1)![0]).toMatchObject({type: "theme", tokens: {"color-scheme": "light"}});
      expect(f.ports.started).not.toHaveBeenCalled();
    } finally {f.dispose(); document.documentElement.style.removeProperty("color-scheme");}
  });

  it("reconnects each loaded document and rejects the previous document nonce without replaying start signals", () => {
    const f = fixture(); f.message("ready"); f.message("started", {request_id: "start-one"});
    f.frame.dispatchEvent(new Event("load"));
    const hello = f.post.mock.calls.at(-1)![0] as Record<string, unknown>;
    expect(hello.nonce).not.toBe(f.hello.nonce);
    f.message("ready"); expect(f.ports.ready).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(1000);
    expect(f.post.mock.calls.at(-1)![0]).toMatchObject({type: "hello", nonce: hello.nonce});
    f.message("ready", {nonce: hello.nonce});
    expect(f.ports.ready).toHaveBeenCalledTimes(2);
    f.message("started", {nonce: hello.nonce, request_id: "start-one"});
    expect(f.ports.started.mock.calls).toEqual([[], ["start-one"], []]);
    f.dispose();
  });
});

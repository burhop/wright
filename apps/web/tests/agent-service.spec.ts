import { afterEach, describe, expect, it, vi } from "vitest";
import {
  HermesAgentService,
  summarizeProgressPayload,
} from "../src/services/agent-service";

const notify = vi.hoisted(() => vi.fn());
vi.mock("../src/services/host-adapter", () => ({ hostAdapter: { notify } }));

afterEach(() => {
  notify.mockClear();
  vi.unstubAllGlobals();
});

describe("summarizeProgressPayload", () => {
  it("uses generic advertised fields and computes bounded progress", () => {
    const summary = summarizeProgressPayload({
      server: "geometry",
      tool: "geometry__create",
      title: "Create geometry",
      status: "running",
      progress: 1,
      total: 4,
      message: "Sketching",
      correlationId: "request-1",
    });

    expect(summary).toMatchObject({
      title: "Create geometry",
      percentage: 25,
      server: "geometry",
      tool: "geometry__create",
      status: "running",
      progress: 1,
      total: 4,
      correlationId: "request-1",
    });
    expect(summary.detail).toContain("geometry / geometry__create");
    expect(summary.detail).toContain("Sketching");
  });

  it("falls back safely when no provider fields are supplied", () => {
    expect(summarizeProgressPayload({})).toEqual({
      title: "Tool progress",
      detail: undefined,
      message: "Tool progress",
      percentage: undefined,
      server: undefined,
      tool: undefined,
      status: undefined,
      progress: undefined,
      total: undefined,
      correlationId: undefined,
      heartbeat: undefined,
    });
  });

  it("shares and caches the static command catalog request", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          commands: [{ name: "wright", description: "Wright", prefix: "/" }],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const service = new HermesAgentService();

    const [first, second] = await Promise.all([
      service.getCommands(),
      service.getCommands(),
    ]);
    const third = await service.getCommands();

    expect(first).toEqual(second);
    expect(third).toEqual(first);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});


describe("platform-bound chat behavior", () => {
  it("keeps concurrent model catalogs separate by saved session", async () => {
    const pending: Record<string, (response: Response) => void> = {};
    const fetchMock = vi.fn((url: string) => new Promise<Response>((resolve) => { pending[new URL(url, "http://localhost").searchParams.get("session_id")!] = resolve; }));
    vi.stubGlobal("fetch", fetchMock);
    const service = new HermesAgentService();
    const hermes = service.listHermesModels(false, "hermes-session");
    const codex = service.listHermesModels(false, "codex-session");
    const respond = (session: string, model: string) => pending[session](new Response(JSON.stringify({ current_model: model }), {status: 200}));
    respond("codex-session", "gpt-6.1-sol");
    expect((await codex).current_model).toBe("gpt-6.1-sol");
    respond("hermes-session", "hermes-model");
    expect((await hermes).current_model).toBe("hermes-model");
    // A later Codex lookup cannot consume the most recently cached Hermes result.
    const again = service.listHermesModels(false, "codex-session");
    expect(fetchMock).toHaveBeenCalledTimes(3);
    respond("codex-session", "gpt-6.1-sol");
    expect((await again).current_model).toBe("gpt-6.1-sol");
  });

  it.each(["failed", "unknown", "interrupted"])("does not announce completion for %s", (status) => {
    const service = new HermesAgentService();
    service["parseSSEEvent"]("stream_end", JSON.stringify({status}), "session");
    expect(notify.mock.calls.some(([title]) => title === "Agent Task Finished")).toBe(false);
  });
});

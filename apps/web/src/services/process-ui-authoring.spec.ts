import { beforeEach, describe, expect, it, vi } from "vitest";
import { createInterfaceAuthoringClient, interfaceAuthoringReason, type ProcessInterfacePresentation } from "./process-ui-authoring";
import type { AuthoringJob, BuildReport, InterfaceManifest, InterfaceRevision } from "@wright/process-client";

const host = vi.hoisted(() => ({fetch: vi.fn(), resolveBackendUrl: vi.fn((path: string) => "http://localhost:8000" + path),
  validateIssuedPreviewUrl: vi.fn((value: string) => value)}));
vi.mock("./host-adapter", () => ({hostAdapter: host}));

const process = {workspace_id: "workspace", source_path: "workflows/job.wflow", source_digest: "a".repeat(64)};
const ui = "ui-" + "a".repeat(32), revision = "revision-" + "b".repeat(32);
const now = "2026-10-01T12:00:00Z";
const resolution = {profile: {instructions_version: "role-v1", instructions_digest: "a".repeat(64)},
  adapter: "controlled", model_reference: "configured-default", configuration_digest: "b".repeat(64),
  effective_instructions_digest: "a".repeat(64)};
const job: AuthoringJob = {job_id: "job-one", process, request_id: "request-one", request_digest: "c".repeat(64),
  state: "preview_ready", role_resolution: resolution, created_at: now, updated_at: now, revision_id: revision};
const manifest: InterfaceManifest = {ui_id: ui, revision_id: revision, title: "Result comparison", process,
  client_version: "1.0.0", kit_version: "1.0.0"};
const build: BuildReport = {build_id: "build-one", source_digest: "d".repeat(64), manifest_digest: "e".repeat(64),
  bundle_digest: "f".repeat(64), toolchain_digest: "a".repeat(64), state: "built", created_at: now, bundled_bytes: 21};
const built = {job, preview: {manifest, build, active_revision: null, previewed_at: null}};
const descriptor: ProcessInterfacePresentation["descriptor"] = {schemaVersion: 1, surfaceId: "surface-one", workspaceId: "workspace",
  source: {kind: "live_app", sourceId: `process.${ui}.${revision}`, sourceVersion: "a".repeat(64), manifestId: `process.${ui}.${revision}`},
  title: "Comparison", lifecycle: "ready", instance: {instanceId: "instance-one", generation: 1, sharing: "isolated"},
  presentations: [{kind: "panel", eligible: true}], capabilities: [], revision: 2, createdAt: now, updatedAt: now};
const launch: ProcessInterfacePresentation["launch"] = {presentationId: "presentation-one", instanceId: "instance-one", generation: 1, kind: "panel",
  absoluteBootstrapUrl: "http://s-presentation-one.localhost:8000/bootstrap?token=issued", expiresAt: now};
const binding = {process, ui_id: ui, revision_id: revision, run_id: null, read_only: true,
  presentation_id: "presentation-one", generation: 1};
const view = {descriptor, launch, binding, job_id: "job-one", build};
const saved: InterfaceRevision = {manifest, build, source_digest: build.source_digest, role_resolution: resolution,
  generation_request_digest: job.request_digest, created_at: now, previewed_at: now};
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), {status, headers: {"content-type": "application/json"}});
const client = () => createInterfaceAuthoringClient(process, "owned-session");

describe("native interface authoring client", () => {
  beforeEach(() => {vi.clearAllMocks(); host.validateIssuedPreviewUrl.mockImplementation(value => value);});

  it("preserves the recorded trace on built and active jobs and accepts older responses", async () => {
    host.fetch.mockResolvedValue(json({...built, trace_id: "trace-recorded-one"}));
    expect((await client().getJob("job-one")).trace_id).toBe("trace-recorded-one");
    host.fetch.mockResolvedValue(json({job: {...job, state: "generating"}, preview: null, trace_id: "trace-recorded-one"}));
    expect((await client().getJob("job-one")).trace_id).toBe("trace-recorded-one");
    host.fetch.mockResolvedValue(json(built));
    expect((await client().getJob("job-one")).trace_id).toBeNull();
  });

  it.each([true, {}, "not an identity", "a".repeat(161)])("rejects an invalid diagnostic trace identity %j", async trace => {
    host.fetch.mockResolvedValue(json({...built, trace_id: trace}));
    await expect(client().getJob("job-one")).rejects.toThrow();
  });

  it("keeps exact presentation cleanup alive during document departure", async () => {
    host.fetch.mockResolvedValue(new Response(null, {status: 204}));
    await client().close(view, {keepalive: true});
    expect(host.fetch).toHaveBeenCalledExactlyOnceWith("http://localhost:8000/api/workspace/process-interfaces/presentations/close", {
      method: "POST", signal: undefined, keepalive: true,
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({surface_id: "surface-one", presentation_id: "presentation-one", session_id: "owned-session",
        path: process.source_path, expected_storage_digest: process.source_digest}),
    });
  });

  it("keeps normal presentation cleanup on the ordinary request path", async () => {
    host.fetch.mockResolvedValue(new Response(null, {status: 204}));
    await client().close(view);
    expect(host.fetch.mock.calls[0][1]).not.toHaveProperty("keepalive");
    expect(host.fetch.mock.calls[0][0]).toContain("/presentations/close");
  });

  it.each(["details", "detail"])("preserves the backend actionable reason from %s", async key => {
    const reason = {code: "CAPABILITY_UNAVAILABLE", message: "The managed interface is not ready.",
      correction: "Open the common view and inspect managed runtime diagnostics."};
    host.fetch.mockResolvedValue(json({error_code: reason.code, message: reason.message,
      [key]: {reason, diagnostic: {runtime_code: "SURFACE_READINESS_TIMEOUT"}}}, 503));
    try {
      await client().getJob("job-one");
      expect.fail("Unavailable job must reject");
    } catch (error) {
      expect(interfaceAuthoringReason(error)).toEqual(reason);
      expect(interfaceAuthoringReason(error)).not.toHaveProperty("diagnostic");
    }
  });

  it("does not trust malformed reasons or copy raw API diagnostics", async () => {
    host.fetch.mockResolvedValue(json({details: {reason: {code: "SECRET", message: "PRIVATE"},
      diagnostic: {secret: "PRIVATE"}}}, 503));
    await expect(client().getJob("job-one")).rejects.toThrow();
  });

  it("uses native host authentication and preserves one explicit generation request identity", async () => {
    host.fetch.mockImplementation(async () => json(job));
    const request = {request_id: "request-one", instruction: "Show useful findings", title: "Comparison"};
    const api = client();
    await api.submit(request);
    await api.submit(request);
    expect(host.fetch).toHaveBeenCalledTimes(2);
    for (const [url, init] of host.fetch.mock.calls) {
      expect(url).toBe("http://localhost:8000/api/workspace/process-interfaces/authoring-jobs");
      expect(init.method).toBe("POST");
      expect(JSON.parse(init.body)).toEqual({...request, session_id: "owned-session", path: process.source_path,
        expected_storage_digest: process.source_digest});
    }
  });

  it("checks job/bundle/observation metadata without exposing authoring source", async () => {
    host.fetch.mockImplementation(async () => json(built));
    const value = await client().getJob("job-one");
    expect(value.preview?.previewed_at).toBeNull();
    expect(value.job.role_resolution.model_reference).toBe("configured-default");
    expect(new URL(host.fetch.mock.calls[0][0]).searchParams.get("session_id")).toBe("owned-session");
    expect(value).not.toHaveProperty("source");
  });

  it.each([
    {job: {...job, job_id: "foreign-job"}},
    {job: {...job, process: {...process, workspace_id: "foreign"}}},
    {preview: null},
    {preview: {...built.preview, manifest: {...manifest, revision_id: "foreign-revision"}}},
    {preview: {...built.preview, build: {...build, state: "failed"}}},
    {preview: {...built.preview, previewed_at: "not-a-date"}},
  ])("rejects malformed or mismatched job data %j", async change => {
    host.fetch.mockImplementation(async () => json({...built, ...change}));
    await expect(client().getJob("job-one")).rejects.toThrow();
  });

  it("validates the issued managed preview and closes only its native presentation", async () => {
    host.fetch.mockImplementationOnce(async () => json(view)).mockImplementationOnce(async () => new Response(null, {status: 204}));
    const api = client();
    const value = await api.preview("job-one", "preview-request");
    expect(value.binding.read_only).toBe(true);
    expect(host.validateIssuedPreviewUrl).toHaveBeenCalledWith(launch.absoluteBootstrapUrl);
    await api.close(value);
    expect(host.fetch.mock.calls[1][0]).toContain("/presentations/close");
    expect(JSON.parse(host.fetch.mock.calls[1][1].body)).toMatchObject({surface_id: "surface-one", presentation_id: "presentation-one"});
    expect(host.fetch.mock.calls.some(([url]) => String(url).includes("/runs"))).toBe(false);
  });

  it.each([
    {binding: {...binding, read_only: false}},
    {binding: {...binding, run_id: "foreign-run"}},
    {binding: {...binding, presentation_id: "foreign-presentation"}},
    {launch: {...launch, generation: 2}},
    {descriptor: {...descriptor, workspaceId: "foreign"}},
    {descriptor: {...descriptor, source: {...descriptor.source, sourceId: "unrelated-app"}}},
  ])("rejects changed preview identity %j", async changes => {
    host.fetch.mockImplementation(async () => json({...view, ...changes}));
    await expect(client().preview("job-one", "preview-request")).rejects.toThrow();
  });

  it("opens an exact saved revision/run without invoking generation or compilation", async () => {
    host.fetch.mockImplementation(async () => json({...view, binding: {...binding, run_id: "run-two", read_only: false}}));
    const value = await client().present(ui, revision, "saved-request", "run-two");
    expect(value.binding.run_id).toBe("run-two");
    expect(host.fetch).toHaveBeenCalledTimes(1);
    expect(host.fetch.mock.calls[0][0]).toContain(`/uis/${ui}/present`);
  });

  it("saves exact hashes with the expected active revision", async () => {
    host.fetch.mockImplementation(async () => json(saved));
    await client().save(built, "prior-revision");
    const payload = JSON.parse(host.fetch.mock.calls[0][1].body);
    expect(payload).toMatchObject({job_id: "job-one", source_digest: build.source_digest,
      manifest_digest: build.manifest_digest, bundle_digest: build.bundle_digest,
      expected_active_revision: "prior-revision"});
  });

  it("requests exact compatibility query once and preserves backend reasons", async () => {
    host.fetch.mockImplementation(async () => json({ui_id: ui, revision_id: revision, current_process: process,
      state: "incompatible", reasons: [{code: "UI_INCOMPATIBLE", message: "Input changed", correction: "Update interface"}]}));
    const value = await client().compatibility(ui, revision);
    expect(value.state).toBe("incompatible");
    const url = new URL(host.fetch.mock.calls[0][0]);
    expect(url.searchParams.getAll("session_id")).toEqual(["owned-session"]);
    expect(url.searchParams.getAll("revision_id")).toEqual([revision]);
  });

  it("reports safe owner correction and does not replay a failed request", async () => {
    const reason = {code: "REQUEST_CONFLICT", message: "This request already has different content", correction: "Reopen the recorded job"};
    host.fetch.mockImplementation(async () => json({detail: {reason}}, 409));
    try { await client().submit({request_id: "request-one", instruction: "Changed", title: "Comparison"}); }
    catch (error) {expect(interfaceAuthoringReason(error)).toEqual(reason);}
    expect(host.fetch).toHaveBeenCalledTimes(1);
  });

  it("attaches only a native verified view/request receipt without a browser run identity", async () => {
    const working = {...view, binding: {...binding, read_only: false}};
    const receipt = {principal_id: "native-user", process, request_id: "start-one", payload_digest: "a".repeat(64),
      input_snapshot_id: "inputs-one", input_digest: "b".repeat(64), run_id: "confirmed-run", initial_outcome: "accepted", created_at: now};
    host.fetch.mockImplementationOnce(async () => json(working)).mockImplementationOnce(async () => json({receipt}));
    const api = client(), owned = await api.present(ui, revision, "view-request");
    expect(await api.startReceipt(owned, "start-one")).toEqual(receipt);
    const body = JSON.parse(host.fetch.mock.calls[1][1].body);
    expect(body).toMatchObject({surface_id: "surface-one", presentation_id: "presentation-one", request_id: "start-one"});
    expect(body).not.toHaveProperty("run_id");
    host.fetch.mockResolvedValue(json({receipt: {...receipt, request_id: "foreign-request"}}));
    await expect(api.startReceipt(owned, "start-one")).rejects.toThrow();
    host.fetch.mockResolvedValue(json({receipt: null})); expect(await api.startReceipt(owned)).toBeNull();
    await expect(api.startReceipt({...owned, binding: {...owned.binding, read_only: true}})).rejects.toThrow();
  });
});

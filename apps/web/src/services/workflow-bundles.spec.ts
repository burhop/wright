import { beforeEach, expect, it, vi } from "vitest";
const host = vi.hoisted(() => ({
  fetch: vi.fn(),
  resolveBackendUrl: (path: string) => `http://localhost:8000${path}`,
}));
vi.mock("./host-adapter", () => ({ hostAdapter: host }));
import { workflowBundles, parseWorkflowBundleFile } from "./workflow-bundles";
const bundle = {
  schema_version: "wright.workflow-bundle/1",
  source: "exact accepted source",
  source_digest: "a".repeat(64),
  mode: "source",
  dependencies: [],
};
const digest = "b".repeat(64);
const inspection = {
  bundle_digest: digest,
  can_import: true,
  can_run: false,
  diagnostics: [],
  external_dependencies: [],
  requirements: [],
};
beforeEach(() => host.fetch.mockReset());
it("exports exact accepted source identity and explicit asset selections without retry", async () => {
  host.fetch.mockResolvedValue(
    new Response(JSON.stringify({ bundle, bundle_digest: digest })),
  );
  expect(
    await workflowBundles.export(
      "session",
      "workflows/example.workflow.wflow",
      "a".repeat(64),
      "bundle",
      ["images/reference.png"],
      ["ui-1"],
    ),
  ).toEqual({ bundle, bundle_digest: digest });
  expect(host.fetch.mock.calls[0]![0]).toBe(
    "http://localhost:8000/api/workspace/workflow-bundles/export",
  );
  expect(JSON.parse(host.fetch.mock.calls[0]![1].body)).toEqual({
    session_id: "session",
    path: "workflows/example.workflow.wflow",
    expected_storage_digest: "a".repeat(64),
    mode: "bundle",
    selected_reference_paths: ["images/reference.png"],
    selected_ui_ids: ["ui-1"],
  });
});
it("inspects before importing and pins import to the returned bundle digest", async () => {
  host.fetch
    .mockResolvedValueOnce(new Response(JSON.stringify(inspection)))
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          source: {
            workspace_id: "workspace",
            path: "workflows/imported.workflow.wflow",
            source: "exact",
            storage_digest: "c".repeat(64),
          },
          imported_paths: [],
          inspection,
        }),
      ),
    );
  const report = await workflowBundles.inspect(
    "session",
    bundle,
    "workflows/imported.workflow.wflow",
  );
  await workflowBundles.import(
    "session",
    bundle,
    "workflows/imported.workflow.wflow",
    report.bundle_digest,
  );
  expect(JSON.parse(host.fetch.mock.calls[1]![1].body)).toEqual({
    session_id: "session",
    bundle,
    destination_path: "workflows/imported.workflow.wflow",
    expected_bundle_digest: digest,
  });
});
it("does not accept an inspection that claims execution readiness", async () => {
  host.fetch.mockResolvedValue(
    new Response(JSON.stringify({ ...inspection, can_run: true })),
  );
  await expect(
    workflowBundles.inspect(
      "session",
      bundle,
      "workflows/imported.workflow.wflow",
    ),
  ).rejects.toThrow("invalid workflow transfer inspection");
});
it("reads exported JSON envelopes and rejects unrelated/oversized files", () => {
  expect(
    parseWorkflowBundleFile(JSON.stringify({ bundle, bundle_digest: digest })),
  ).toEqual(bundle);
  expect(parseWorkflowBundleFile(JSON.stringify(bundle))).toEqual(bundle);
  expect(() => parseWorkflowBundleFile('{"arbitrary":"file"}')).toThrow(
    "exported Wright",
  );
  expect(() =>
    parseWorkflowBundleFile(" ".repeat(20 * 1024 * 1024 + 1)),
  ).toThrow("20 MiB");
});
it("preserves validation errors and never retries an uncertain import", async () => {
  host.fetch.mockResolvedValue(
    new Response(
      JSON.stringify({
        detail: {
          code: "workflow_bundle_rejected",
          message: "Destination already exists",
        },
      }),
      { status: 422 },
    ),
  );
  await expect(
    workflowBundles.import(
      "session",
      bundle,
      "workflows/imported.workflow.wflow",
      digest,
    ),
  ).rejects.toThrow("Destination already exists");
  expect(host.fetch).toHaveBeenCalledOnce();
});

it.each([undefined, null, "references/design.png"])(
  "preserves a diagnostic dependency of %s",
  async (dependency) => {
    const diagnostic = {
      code: "external_dependency",
      severity: "warning",
      message: "Prepare this dependency before starting.",
      dependency,
    };
    host.fetch.mockResolvedValue(
      new Response(
        JSON.stringify({ ...inspection, diagnostics: [diagnostic] }),
      ),
    );
    const report = await workflowBundles.inspect(
      "session",
      bundle,
      "workflows/imported.workflow.wflow",
    );
    expect(report.diagnostics[0]?.dependency).toEqual(dependency);
  },
);

it.each([123, false, {}, ["references/design.png"]])(
  "rejects a malformed dependency instead of rendering it: %j",
  async (dependency) => {
    host.fetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          ...inspection,
          diagnostics: [
            {
              code: "invalid",
              severity: "error",
              message: "Invalid file",
              dependency,
            },
          ],
        }),
      ),
    );
    await expect(
      workflowBundles.inspect(
        "session",
        bundle,
        "workflows/imported.workflow.wflow",
      ),
    ).rejects.toThrow("invalid transfer diagnostics");
    expect(host.fetch).toHaveBeenCalledOnce();
  },
);

it("rejects an unknown diagnostic severity", async () => {
  host.fetch.mockResolvedValue(
    new Response(
      JSON.stringify({
        ...inspection,
        diagnostics: [
          { code: "invalid", severity: "ready", message: "Unqualified" },
        ],
      }),
    ),
  );
  await expect(
    workflowBundles.inspect(
      "session",
      bundle,
      "workflows/imported.workflow.wflow",
    ),
  ).rejects.toThrow("invalid transfer diagnostics");
});

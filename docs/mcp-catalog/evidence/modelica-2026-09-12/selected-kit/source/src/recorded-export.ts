import type { McpApp } from "@casys/mcp-server";
import type { ResumableSimulationService } from "./application/resumable-simulation-service.ts";
import { ValidationError } from "./domain/errors.ts";
import { sha256 } from "./domain/hashing.ts";

const DATASETS = ["water-heater-sizing-01", "water-heater-sizing-02", "water-heater-sizing-03"];
const NAMES = ["request.json", "resolved-parameters.json", "WrightWaterHeater.mo", "scenario.json", "parameter-schema.json", "run.mos", "omc.log", "result.csv", "evidence.json"];

export function validateExportInput(input: Record<string, unknown>) {
  if (Object.keys(input).sort().join(",") !== "attempt_id,dataset_id,expected_manifest_sha256,request_id") throw new ValidationError("Unknown recorded export field.");
  const { dataset_id, attempt_id, request_id, expected_manifest_sha256 } = input;
  if (typeof dataset_id !== "string" || !DATASETS.includes(dataset_id) ||
    typeof attempt_id !== "string" || !/^attempt-[A-Za-z0-9-]{1,40}$/.test(attempt_id) ||
    typeof request_id !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(request_id) ||
    !request_id.startsWith(`${dataset_id}-${attempt_id}-`) ||
    typeof expected_manifest_sha256 !== "string" || !/^[0-9a-f]{64}$/.test(expected_manifest_sha256)) {
    throw new ValidationError("Recorded export requires an exact same-dataset/attempt request identity and manifest digest.");
  }
  return { dataset_id, attempt_id, request_id, expected_manifest_sha256 };
}

export async function exportRecorded(service: ResumableSimulationService, raw: Record<string, unknown>) {
  const input = validateExportInput(raw);
  // This is the exact read-only verifier used by the provider's MCP resources:
  // completed claim + run seal + request/manifest + native artifact hash/bytes.
  const evidence = await service.getCompletedEvidence(input.request_id);
  const record = evidence.runJson.record;
  const manifest = record.manifest as Record<string, unknown>;
  const model = manifest.model as Record<string, unknown>;
  if (record.status !== "succeeded" || record.request_id !== input.request_id ||
    manifest.manifest_sha256 !== input.expected_manifest_sha256 ||
    model.id !== "wright-water-heater-v1" || model.version !== "0.1.0") {
    throw new ValidationError("Recorded export requires the exact successful selected kit run.");
  }
  if (evidence.artifacts.length !== NAMES.length ||
    evidence.artifacts.some(artifact => !NAMES.includes(artifact.file_name))) {
    throw new ValidationError("Unexpected native artifact set.");
  }
  const bytes = new Map<string, { data: Uint8Array; digest: string; uri: string }>();
  for (const artifact of evidence.artifacts) {
    const verified = await service.store.readArtifact(input.request_id, artifact);
    bytes.set(artifact.file_name, { data: new TextEncoder().encode(verified.source), digest: artifact.sha256, uri: artifact.uri });
  }
  bytes.set("run.json", { data: new TextEncoder().encode(evidence.runJson.source), digest: await sha256(evidence.runJson.source), uri: `casys://modelica/requests/${input.request_id}/run.json` });
  // Only separately mounted attempt output roots exist here. No arbitrary
  // directory/file, source path, URI, contents, or command is a tool input.
  const root = `/exports/${input.dataset_id}/${input.attempt_id}`;
  if ((await Deno.realPath(root)) !== root || !(await Deno.lstat(root)).isDirectory) throw new ValidationError("Attempt output root is missing or redirected.");
  const directory = `${root}/${input.request_id}`;
  try { await Deno.mkdir(directory); } catch (error) { if (!(error instanceof Deno.errors.AlreadyExists)) throw error; }
  if ((await Deno.realPath(directory)) !== directory || (await Deno.lstat(directory)).isSymlink) throw new ValidationError("Export directory is redirected.");
  for await (const entry of Deno.readDir(directory)) {
    if (!bytes.has(entry.name) || !entry.isFile || entry.isSymlink) throw new ValidationError("Existing export contains unexpected entries.");
  }
  const produced_files = [];
  for (const [name, value] of bytes) {
    const path = `${directory}/${name}`;
    try {
      const file = await Deno.open(path, { write: true, createNew: true });
      try { let offset = 0; while (offset < value.data.length) offset += await file.write(value.data.subarray(offset)); await file.sync(); } finally { file.close(); }
    } catch (error) {
      if (!(error instanceof Deno.errors.AlreadyExists)) throw error;
      const existing = await Deno.lstat(path);
      if (!existing.isFile || existing.isSymlink || (await Deno.realPath(path)) !== path) throw new ValidationError("Existing export file is redirected.");
      const existingBytes = await Deno.readFile(path);
      const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", existingBytes))).map(byte => byte.toString(16).padStart(2, "0")).join("");
      if (hash !== value.digest) throw new ValidationError("Existing export bytes differ; refusing overwrite.");
    }
    produced_files.push({ output_path: `campaign/${input.dataset_id}/${input.attempt_id}/artifacts/${input.request_id}/${name}`, output_bytes: value.data.length, sha256: value.digest,
      output_format: name.endsWith(".json") ? "json" : name.endsWith(".csv") ? "csv" : "text", source_uri: value.uri });
  }
  return { operation: "export_recorded_modelica_result", request_id: input.request_id, native_run_id: record.run_id,
    manifest_sha256: input.expected_manifest_sha256, produced_files };
}

export function registerRecordedExport(server: McpApp, service: ResumableSimulationService) {
  const name = "modelica_export_recorded_result";
  server.registerTools([{ name, description: "Export only the exact sealed successful selected Modelica request, native CSV and provenance into its mounted same-attempt output folder. Never accepts arbitrary contents, paths or URIs; refuses differing existing files.",
    inputSchema: { type: "object", additionalProperties: false, properties: {
      dataset_id: { type: "string", enum: DATASETS }, attempt_id: { type: "string", pattern: "^attempt-[A-Za-z0-9-]{1,40}$" },
      request_id: { type: "string", pattern: "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$" }, expected_manifest_sha256: { type: "string", pattern: "^[0-9a-f]{64}$" },
    }, required: ["dataset_id", "attempt_id", "request_id", "expected_manifest_sha256"] },
  }], new Map([[name, async (input: Record<string, unknown>) => {
    const result = await exportRecorded(service, input);
    return { content: [{ type: "text", text: JSON.stringify(result) }], structuredContent: result };
  }]]));
}

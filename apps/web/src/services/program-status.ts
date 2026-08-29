import { hostAdapter } from "./host-adapter";

const API_BASE = hostAdapter.getApiBaseUrl();

export const PROGRAM_STATUS_SCHEMA_VERSION = "1.0.0" as const;

export type ProgramStatusAvailability = "current" | "stale" | "failed" | "unavailable";

export interface ProgramStatusError {
  error_code: string;
  message: string;
  recovery_class: string;
  trace_id: string;
}

export interface ProgramStatusBundle {
  schema_version: typeof PROGRAM_STATUS_SCHEMA_VERSION;
  bundle_id: string;
  generated_at: string;
  source: ProgramStatusSource;
  dashboard: Readonly<Record<string, unknown>>;
  supplement: Readonly<Record<string, unknown>>;
}

export interface ProgramStatusEvidenceReference {
  id: string;
  path: string;
  sha256: string;
}

export interface ProgramStatusSource {
  commit: string;
  tree: string;
  program_tree: string;
  snapshot_path: string;
  snapshot_raw_sha256: string;
  raw_identity_verification: "publisher_git_blob_attested";
  raw_identity_evidence: ProgramStatusEvidenceReference;
  dashboard_canonical_sha256: string;
  source_catalog_path: "specs/077-browser-program-status/contracts/program-status-source-catalog.json";
  source_catalog_sha256: string;
  validation_transition: string;
  validation_verdict: "passed";
}

export interface ProgramStatusPublisher {
  mode: string;
  state: "active" | "inactive" | "failed" | "unavailable";
  observed_commit: string | null;
  last_attempt_at: string | null;
  last_success_at: string | null;
  failure_code: string | null;
  recovery: string | null;
}

export interface ProgramStatusFetchResult {
  status: 200 | 304;
  etag: string | null;
  bundle: ProgramStatusBundle | null;
}

export function decodeProgramStatusBundle(value: unknown): ProgramStatusBundle {
  void value;
  throw new Error("Strict EPP-F01B bundle decoding begins at T017");
}

export function decodeProgramStatusPublisher(
  value: unknown,
): ProgramStatusPublisher {
  void value;
  throw new Error("Strict EPP-F01B publisher decoding begins at T017");
}

export async function fetchProgramStatus(
  etag?: string,
  signal?: AbortSignal,
): Promise<ProgramStatusFetchResult> {
  void etag;
  void signal;
  void API_BASE;
  throw new Error("Authenticated conditional fetching begins at T017");
}

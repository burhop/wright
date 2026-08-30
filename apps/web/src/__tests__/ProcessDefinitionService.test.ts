import { beforeEach, describe, expect, it, vi } from "vitest";

import definitionRaw from "../../../../src/wright_engineering/static/process-definitions/product-definition-v1.json?raw";
import vectorsRaw from "../../../../specs/078-process-definition-view/contracts/wright-process-json-v1-vectors.json?raw";

vi.mock("../services/host-adapter", () => ({
  hostAdapter: {
    getApiBaseUrl: () => "http://wright.local",
    fetch: vi.fn(),
  },
}));

import { hostAdapter } from "../services/host-adapter";
import {
  PROCESS_DEFINITION_SCHEMA_VERSION,
  PROCESS_DEFINITION_SOURCE_ID,
  canonicalProcessDigest,
  canonicalProcessJson,
  decodeProcessDefinitionEnvelope,
  fetchProcessDefinition,
  parseProcessJsonBytes,
  verifyProcessDefinitionIdentity,
  type ProcessDefinitionEnvelope,
} from "../services/process-definition";

const mockedFetch = vi.mocked(hostAdapter.fetch);
const encoder = new TextEncoder();

interface CanonicalVector {
  name: string;
  input_utf8_hex: string;
  canonical_utf8_hex?: string;
  canonical_sha256?: string;
}

const vectors = JSON.parse(vectorsRaw) as {
  profile: string;
  valid: CanonicalVector[];
  invalid: CanonicalVector[];
};

function bytesFromHex(value: string): Uint8Array {
  return Uint8Array.from(value.match(/.{2}/g) ?? [], (byte) =>
    Number.parseInt(byte, 16),
  );
}

function hexFromBytes(value: Uint8Array): string {
  return Array.from(value, (byte) => byte.toString(16).padStart(2, "0")).join(
    "",
  );
}

async function makeEnvelope(): Promise<ProcessDefinitionEnvelope> {
  const definition = parseProcessJsonBytes(encoder.encode(definitionRaw));
  const material = {
    definition,
    source_kind: "installed",
    source_id: PROCESS_DEFINITION_SOURCE_ID,
    source_sha256:
      "6a02f71e35f9c3d9a3184509ddeab2df251cff454b6d6ce66d7244d015eefdef",
    source_available: true,
    supported_schema_versions: [PROCESS_DEFINITION_SCHEMA_VERSION],
  };
  return decodeProcessDefinitionEnvelope({
    ...material,
    etag: await canonicalProcessDigest(material),
  });
}

async function responseFor(
  envelope: ProcessDefinitionEnvelope,
  status = 200,
): Promise<Response> {
  return new Response(JSON.stringify(envelope), {
    status,
    headers: {
      "content-type": "application/json",
      etag: `"${envelope.etag}"`,
    },
  });
}

describe.sequential("wright-process-json-v1 browser parity", () => {
  it("uses the exact frozen profile", () => {
    expect(vectors.profile).toBe("wright-process-json-v1");
  });

  it.each(vectors.valid)("canonicalizes $name exactly", async (vector) => {
    const value = parseProcessJsonBytes(bytesFromHex(vector.input_utf8_hex));
    const canonical = encoder.encode(canonicalProcessJson(value));
    expect(hexFromBytes(canonical)).toBe(vector.canonical_utf8_hex);
    expect(await canonicalProcessDigest(value)).toBe(vector.canonical_sha256);
  });

  it.each(vectors.invalid)("rejects invalid vector $name", (vector) => {
    expect(() =>
      parseProcessJsonBytes(bytesFromHex(vector.input_utf8_hex)),
    ).toThrow();
  });
});

describe("closed process-definition client", () => {
  beforeEach(() => mockedFetch.mockReset());

  it("accepts only the fixed closed envelope with optional schema reference", async () => {
    const envelope = await makeEnvelope();
    expect(decodeProcessDefinitionEnvelope(envelope)).toEqual(envelope);

    const withoutSchema = structuredClone(envelope);
    delete withoutSchema.definition.$schema;
    expect(
      decodeProcessDefinitionEnvelope(withoutSchema).definition.$schema,
    ).toBeUndefined();

    const topLevelExtra = { ...envelope, filesystem_path: "C:/secret" };
    expect(() => decodeProcessDefinitionEnvelope(topLevelExtra)).toThrow(
      "UNKNOWN_FIELD",
    );

    const nestedExtra = structuredClone(envelope) as ProcessDefinitionEnvelope & {
      definition: ProcessDefinitionEnvelope["definition"] & { run_id?: string };
    };
    nestedExtra.definition.run_id = "not-authorized";
    expect(() => decodeProcessDefinitionEnvelope(nestedExtra)).toThrow(
      "UNKNOWN_FIELD",
    );
  });

  it("rejects missing fields, wrong identities, bounds, duplicates, and non-NFC text", async () => {
    const envelope = await makeEnvelope();

    const missing = structuredClone(envelope) as Partial<ProcessDefinitionEnvelope>;
    delete missing.source_id;
    expect(() => decodeProcessDefinitionEnvelope(missing)).toThrow(
      "MISSING_FIELD",
    );

    const wrongSource = { ...envelope, source_id: "process-definitions/other.json" };
    expect(() => decodeProcessDefinitionEnvelope(wrongSource)).toThrow(
      "ENUM_INVALID",
    );

    const overlong = structuredClone(envelope);
    overlong.definition.purpose = "x".repeat(1001);
    expect(() => decodeProcessDefinitionEnvelope(overlong)).toThrow(
      "EXPECTED_TEXT",
    );

    const duplicate = structuredClone(envelope);
    duplicate.definition.actions[0]?.input_port_ids.push("customer-needs");
    expect(() => decodeProcessDefinitionEnvelope(duplicate)).toThrow(
      "DUPLICATE_REFERENCE",
    );

    const tooMany = structuredClone(envelope);
    tooMany.definition.phases = Array.from(
      { length: 21 },
      () => envelope.definition.phases[0]!,
    );
    expect(() => decodeProcessDefinitionEnvelope(tooMany)).toThrow(
      "ARRAY_BOUNDS_INVALID",
    );

    const nfd = structuredClone(envelope);
    nfd.definition.title = "cafe\u0301";
    expect(() => decodeProcessDefinitionEnvelope(nfd)).toThrow("TEXT_NOT_NFC");
  });

  it("independently binds definition content and complete envelope identity", async () => {
    const envelope = await makeEnvelope();
    await expect(verifyProcessDefinitionIdentity(envelope)).resolves.toBeUndefined();

    const contentDrift = structuredClone(envelope);
    contentDrift.definition.title = "Changed with a stale content identity";
    await expect(verifyProcessDefinitionIdentity(contentDrift)).rejects.toThrow(
      "CONTENT_IDENTITY_MISMATCH",
    );

    const envelopeDrift = structuredClone(envelope);
    envelopeDrift.source_kind = "packaged_fallback";
    await expect(verifyProcessDefinitionIdentity(envelopeDrift)).rejects.toThrow(
      "ENVELOPE_IDENTITY_MISMATCH",
    );
  });

  it("fetches the fixed read-only route and verifies a complete 200 response", async () => {
    const envelope = await makeEnvelope();
    mockedFetch.mockResolvedValue(await responseFor(envelope));
    const signal = new AbortController().signal;
    const prior = `"${"a".repeat(64)}"`;

    await expect(fetchProcessDefinition(prior, signal)).resolves.toEqual({
      state: "current",
      status: 200,
      etag: `"${envelope.etag}"`,
      envelope,
    });
    expect(mockedFetch).toHaveBeenCalledWith(
      "http://wright.local/api/process-definitions/product-definition-v1",
      {
        headers: { "If-None-Match": prior },
        signal,
        cache: "no-cache",
      },
    );
  });

  it("rejects body, header, and successful-status identity drift", async () => {
    const envelope = await makeEnvelope();
    const bodyDrift = structuredClone(envelope);
    bodyDrift.definition.purpose = "Stale digest";
    mockedFetch.mockResolvedValueOnce(await responseFor(bodyDrift));
    await expect(fetchProcessDefinition()).rejects.toThrow(
      "CONTENT_IDENTITY_MISMATCH",
    );

    mockedFetch.mockResolvedValueOnce(
      new Response(JSON.stringify(envelope), {
        status: 200,
        headers: { etag: `"${"b".repeat(64)}"` },
      }),
    );
    await expect(fetchProcessDefinition()).rejects.toThrow(
      "ETAG_IDENTITY_MISMATCH",
    );

    mockedFetch.mockResolvedValueOnce(
      new Response(JSON.stringify(envelope), {
        status: 201,
        headers: { etag: `"${envelope.etag}"` },
      }),
    );
    await expect(fetchProcessDefinition()).rejects.toThrow(
      "RESPONSE_STATUS_INVALID",
    );
  });

  it("accepts only a requested bodyless 304 with the exact prior identity", async () => {
    const prior = `"${"c".repeat(64)}"`;
    mockedFetch.mockResolvedValueOnce(
      new Response(null, { status: 304, headers: { etag: prior } }),
    );
    await expect(fetchProcessDefinition(prior)).resolves.toEqual({
      state: "not_modified",
      status: 304,
      etag: prior,
      envelope: null,
    });

    mockedFetch.mockResolvedValueOnce(
      new Response(null, { status: 304, headers: { etag: prior } }),
    );
    await expect(fetchProcessDefinition()).rejects.toThrow(
      "UNSOLICITED_NOT_MODIFIED",
    );

    mockedFetch.mockResolvedValueOnce(
      new Response(null, {
        status: 304,
        headers: { etag: `"${"d".repeat(64)}"` },
      }),
    );
    await expect(fetchProcessDefinition(prior)).rejects.toThrow(
      "NOT_MODIFIED_IDENTITY_MISMATCH",
    );
  });

  it("keeps typed recovery closed and support safe", async () => {
    mockedFetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          error_code: "PROCESS_DEFINITION_UNSUPPORTED_VERSION",
          message: "The installed process definition uses an unsupported schema.",
          recovery_class: "install_compatible_wright",
          trace_id: "trace-1",
          supported_schema_versions: ["1.0.0"],
        }),
        { status: 422 },
      ),
    );
    await expect(fetchProcessDefinition()).rejects.toMatchObject({
      status: 422,
      detail: {
        error_code: "PROCESS_DEFINITION_UNSUPPORTED_VERSION",
        recovery_class: "install_compatible_wright",
        trace_id: "trace-1",
      },
    });
  });
});

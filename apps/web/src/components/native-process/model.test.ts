import { describe, expect, it } from "vitest";
import type { NativeDocument } from "../../services/native-process";
import {
  applyCommand,
  canonicalJson,
  emptyDocument,
  parseCanonicalInput,
  pushCommand,
  redo,
  undo,
  validateDocument,
} from "./model";
import { bufferConfig, stepBuffer } from "./NativeInspector";
import { contract, example, fixtureJson } from "./native-process.fixture";
const vectors = fixtureJson<{
  accepted: {
    id: string;
    input_json: string;
    canonical_utf8_hex: string;
    sha256: string;
  }[];
  rejected: { id: string; input_json: string }[];
}>("canonical-vectors.json");
describe("official language conformance (simulated programmatic clients)", () => {
  for (const vector of vectors.accepted)
    it(`matches frozen UTF-8 bytes: ${vector.id}`, () => {
      const bytes = new TextEncoder().encode(
        canonicalJson(parseCanonicalInput(vector.input_json)),
      );
      expect(
        Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join(
          "",
        ),
      ).toBe(vector.canonical_utf8_hex);
    });
  for (const vector of vectors.rejected)
    it(`rejects noncanonical input: ${vector.id}`, () => {
      expect(() => parseCanonicalInput(vector.input_json)).toThrow();
    });
  it("accepts the same frozen schema and example used by backend clients", () => {
    expect(() => validateDocument(example, contract)).not.toThrow();
    expect(JSON.parse(canonicalJson(example.definition))).toEqual(
      example.definition,
    );
  });
  it("permits incomplete drafts while rejecting unknown document keys", () => {
    expect(() => validateDocument(emptyDocument(), contract)).not.toThrow();
    const bad = structuredClone(example);
    Object.assign(bad.definition, { hiddenExecution: true });
    expect(() => validateDocument(bad, contract)).toThrow(/unknown field/);
  });
});
describe("atomic authoring commands", () => {
  it("preserves explicitly configured empty text when editing a programmatic step", () => {
    const step = {
      id: "empty-input",
      title: "Empty text",
      operation: "text.input@1",
      config: { value: "" },
    };
    const descriptor = contract.operations.find(
      (operation) => operation.id === step.operation,
    )!;
    expect(bufferConfig(stepBuffer(step), descriptor.config_schema)).toEqual({
      value: "",
    });
  });
  it("creates exact descriptor ports without introducing renderer semantics", () => {
    const next = applyCommand(
      emptyDocument(),
      {
        type: "add-step",
        operation: "text.join@1",
        id: "join-step",
        title: "Join text",
      },
      contract,
    );
    expect(
      next.definition.ports.map(({ key, direction, type }) => ({
        key,
        direction,
        type,
      })),
    ).toEqual([
      { key: "first", direction: "input", type: "text" },
      { key: "second", direction: "input", type: "text" },
      { key: "text", direction: "output", type: "text" },
    ]);
    expect(next.definition.steps[0].config).toEqual({});
  });
  it("retains exact endpoints and rejects a duplicate single input without mutation", () => {
    const original = canonicalJson(example);
    const connection = example.definition.connections[0];
    expect(() =>
      applyCommand(
        example,
        {
          type: "connect",
          id: "duplicate-edge",
          source: connection.source_port_id,
          target: connection.target_port_id,
        },
        contract,
      ),
    ).toThrow(/already has/);
    expect(canonicalJson(example)).toBe(original);
  });
  it("rejects mismatched port types and cycles", () => {
    const current = structuredClone(example);
    current.definition.connections = [];
    const text = current.definition.ports.find(
      (p) => p.direction === "output" && p.type === "text",
    )!;
    const input = current.definition.ports.find(
      (p) => p.direction === "input",
    )!;
    const artifact = current.definition.ports.find(
      (p) => p.direction === "output" && p.type === "artifact",
    )!;
    expect(() =>
      applyCommand(
        current,
        {
          type: "connect",
          id: "bad-type",
          source: artifact.id,
          target: input.id,
        },
        contract,
      ),
    ).toThrow(/types/);
    const selfInput = current.definition.ports.find(
      (p) => p.step_id === input.step_id && p.direction === "output",
    )!;
    expect(() =>
      applyCommand(
        current,
        {
          type: "connect",
          id: "bad-cycle",
          source: selfInput.id,
          target: input.id,
        },
        contract,
      ),
    ).toThrow(/itself/);
    const next = applyCommand(
      current,
      { type: "connect", id: "valid-edge", source: text.id, target: input.id },
      contract,
    );
    expect(next.definition.connections[0]).toMatchObject({
      source_port_id: text.id,
      target_port_id: input.id,
    });
  });
  it("deletes all affected edges/outputs atomically and undo restores exact identity", () => {
    const producer = example.definition.ports.find(
      (p) => p.id === example.definition.outputs[0].port_id,
    )!;
    const history = { present: example, past: [], future: [] };
    const after = pushCommand(
      history,
      { type: "remove-step", id: producer.step_id },
      contract,
    );
    expect(after.present.definition.outputs).toHaveLength(0);
    expect(
      after.present.definition.ports.some(
        (p) => p.step_id === producer.step_id,
      ),
    ).toBe(false);
    expect(undo(after).present).toEqual(example);
    expect(redo(undo(after)).present).toEqual(after.present);
  });
  it("layout-only edits preserve the semantic bytes and exact endpoints", () => {
    const next = applyCommand(
      example,
      {
        type: "position",
        id: example.definition.steps[0].id,
        x: 10.4,
        y: 29.9,
      },
      contract,
    );
    expect(canonicalJson(next.definition)).toBe(
      canonicalJson(example.definition),
    );
    expect(next.presentation[example.definition.steps[0].id]).toEqual({
      x: 10,
      y: 30,
    });
  });
  it.each(["1.0", "01", "-0", "1e3", "1000000000000000001"])(
    "rejects invalid exact decimal %s without replacing a valid document",
    (value) => {
      const document = fixtureJson<NativeDocument["definition"]>(
        "examples/mass-check.json",
      );
      const step = document.steps.find(
        (s) => s.operation === "quantity.input@1",
      )!;
      expect(() =>
        applyCommand(
          { definition: document, presentation: {} },
          {
            type: "step",
            id: step.id,
            title: step.title,
            config: { value: { value, unit: "m3" } },
          },
          contract,
        ),
      ).toThrow();
    },
  );
});

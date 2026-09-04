// Test-only simulated service discovery, derived from the frozen language artifacts.
import schemaText from "../../../../../specs/079-wright-native-authoring/contracts/native-process.schema.json?raw";
import conceptText from "../../../../../specs/079-wright-native-authoring/contracts/examples/concept-brief.json?raw";
import massText from "../../../../../specs/079-wright-native-authoring/contracts/examples/mass-check.json?raw";
import packageText from "../../../../../specs/079-wright-native-authoring/contracts/examples/package-review.json?raw";
import vectorsText from "../../../../../specs/079-wright-native-authoring/contracts/canonical-vectors.json?raw";
import type {
  JsonSchema,
  NativeContract,
  NativeDefinition,
  NativeDocument,
  NativeOperation,
  SavedProcess,
} from "../../services/native-process";
import { defaultPresentation } from "./model";
const artifacts: Record<string, string> = {
  "native-process.schema.json": schemaText,
  "examples/concept-brief.json": conceptText,
  "examples/mass-check.json": massText,
  "examples/package-review.json": packageText,
  "canonical-vectors.json": vectorsText,
};
export function fixtureJson<T>(name: string): T {
  return JSON.parse(artifacts[name]) as T;
}
export const schema = fixtureJson<JsonSchema>("native-process.schema.json");
const definitions = ["concept-brief", "mass-check", "package-review"].map(
  (name) => fixtureJson<NativeDefinition>(`examples/${name}.json`),
);
export const example: NativeDocument = {
  definition: definitions[0],
  presentation: defaultPresentation(definitions[0]),
};
export const contract: NativeContract = {
  format: "wright-native-process",
  schema_version: "1.0.0",
  schema,
  canonicalization: "wright-native-json-v1",
  operations: (schema.$defs!.step.allOf ?? []).map((condition) => {
    const id = condition.if!.properties!.operation.const as string;
    const sample = definitions
      .flatMap((definition) =>
        definition.steps.map((step) => ({ definition, step })),
      )
      .find((item) => item.step.operation === id);
    const ports = sample
      ? sample.definition.ports.filter(
          (port) => port.step_id === sample.step.id,
        )
      : [];
    return {
      id,
      inputs: ports
        .filter((p) => p.direction === "input")
        .map(({ key, type }) => ({
          key,
          type,
          cardinality: "one",
          required: true,
        })),
      outputs: ports
        .filter((p) => p.direction === "output")
        .map(({ key, type }) => ({
          key,
          type,
          cardinality: "one",
          required: true,
        })),
      config_schema: condition.then!.properties!.config,
      required_config_keys: [],
    } as NativeOperation;
  }),
};
export function savedProcess(document = example, revision = 1): SavedProcess {
  return {
    ...structuredClone(document),
    revision,
    token: String(revision).repeat(64),
    semantic_digest: "a".repeat(64),
    updated_at: "2026-09-04T12:00:00Z",
  };
}

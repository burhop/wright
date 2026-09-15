import { ValidationError } from "../domain/errors.ts";
import type { ModelicaKit, ParameterDefinition } from "../domain/types.ts";

/**
 * Input schemas are a projection of the already-qualified KitRegistry.
 *
 * They describe selections which the service can already execute; they never
 * add a model path, Modelica source, script, solver, or runtime selector.
 */
export interface ModelicaKitInputSchemas {
  simulate: Record<string, unknown>;
  manifest: Record<string, unknown>;
  requestTemplate: Record<string, unknown>;
  submit: Record<string, unknown>;
}

const REQUEST_ID_SCHEMA = {
  type: "string",
  pattern: "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
};

const MANIFEST_SHA256_SCHEMA = {
  type: "string",
  pattern: "^[0-9a-f]{64}$",
};

const TIMEOUT_SCHEMA = { type: "integer", minimum: 1, maximum: 120_000 };

/**
 * Build all agent-facing selection schemas in one fail-closed operation.
 *
 * `x-modelica-default` is deliberately metadata rather than JSON Schema's
 * `default`: the framework validator applies JSON Schema defaults, whereas a
 * 2.1 caller must explicitly supply every value and unit.
 */
export function createModelicaKitInputSchemas(
  kits: readonly ModelicaKit[],
): ModelicaKitInputSchemas {
  assertSchemaCoherence(kits);
  const combinations = kits.flatMap((kit) =>
    kit.scenarios.map((scenario) => ({ kit, scenarioId: scenario.id }))
  );
  if (combinations.length === 0) {
    throw new ValidationError("Qualified Modelica registry has no selectable kit scenario.", {
      code: "registry.no_selectable_scenario",
      field: "registry",
      recovery: "Register a qualified kit with at least one qualified scenario before startup.",
    });
  }

  return {
    simulate: {
      oneOf: combinations.map(({ kit, scenarioId }) => simulateBranch(kit, scenarioId)),
    },
    manifest: {
      oneOf: combinations.map(({ kit, scenarioId }) => identityBranch(kit, scenarioId)),
    },
    requestTemplate: {
      oneOf: combinations.map(({ kit, scenarioId }) => requestTemplateBranch(kit, scenarioId)),
    },
    submit: {
      oneOf: combinations.map(({ kit, scenarioId }) => submitBranch(kit, scenarioId)),
    },
  };
}

function simulateBranch(kit: ModelicaKit, scenarioId: string): Record<string, unknown> {
  return {
    type: "object",
    additionalProperties: false,
    properties: {
      model_id: { const: kit.id },
      scenario_id: { const: scenarioId },
      parameter_overrides: optionalParametersSchema(kit.parameters),
      timeout_ms: TIMEOUT_SCHEMA,
    },
    required: ["model_id", "scenario_id"],
  };
}

function identityBranch(kit: ModelicaKit, scenarioId: string): Record<string, unknown> {
  return {
    type: "object",
    additionalProperties: false,
    properties: identityProperties(kit, scenarioId),
    required: ["model_id", "model_version", "scenario_id"],
  };
}

function requestTemplateBranch(kit: ModelicaKit, scenarioId: string): Record<string, unknown> {
  return {
    type: "object",
    additionalProperties: false,
    properties: {
      request_id: REQUEST_ID_SCHEMA,
      manifest_sha256: MANIFEST_SHA256_SCHEMA,
      ...identityProperties(kit, scenarioId),
      timeout_ms: TIMEOUT_SCHEMA,
    },
    required: [
      "request_id",
      "manifest_sha256",
      "model_id",
      "model_version",
      "scenario_id",
    ],
  };
}

function submitBranch(kit: ModelicaKit, scenarioId: string): Record<string, unknown> {
  return {
    type: "object",
    additionalProperties: false,
    properties: {
      request_id: REQUEST_ID_SCHEMA,
      manifest_sha256: MANIFEST_SHA256_SCHEMA,
      ...identityProperties(kit, scenarioId),
      parameters: explicitParametersSchema(kit.parameters),
      timeout_ms: TIMEOUT_SCHEMA,
    },
    required: [
      "request_id",
      "manifest_sha256",
      "model_id",
      "model_version",
      "scenario_id",
      "parameters",
      "timeout_ms",
    ],
  };
}

function identityProperties(kit: ModelicaKit, scenarioId: string): Record<string, unknown> {
  return {
    model_id: { const: kit.id },
    model_version: { const: kit.version },
    scenario_id: { const: scenarioId },
  };
}

function optionalParametersSchema(
  parameters: readonly ParameterDefinition[],
): Record<string, unknown> {
  return {
    type: "object",
    additionalProperties: false,
    properties: Object.fromEntries(
      parameters.map((parameter) => [parameter.id, parameterQuantitySchema(parameter)]),
    ),
  };
}

function explicitParametersSchema(
  parameters: readonly ParameterDefinition[],
): Record<string, unknown> {
  return {
    ...optionalParametersSchema(parameters),
    required: parameters.map((parameter) => parameter.id),
  };
}

function parameterQuantitySchema(parameter: ParameterDefinition): Record<string, unknown> {
  return {
    type: "object",
    additionalProperties: false,
    properties: {
      value: {
        type: "number",
        minimum: parameter.minimum,
        maximum: parameter.maximum,
        // This metadata remains non-mutating under the MCP framework's AJV
        // configuration; 2.1 must never silently default caller values.
        "x-modelica-default": parameter.defaultValue,
        "x-modelica-type": parameter.modelicaType,
      },
      unit: { const: parameter.unit },
    },
    required: ["value", "unit"],
  };
}

function assertSchemaCoherence(kits: readonly ModelicaKit[]): void {
  const ids = new Set<string>();
  for (const kit of kits) {
    canonical(kit.id, "kit.id");
    canonical(kit.version, `${kit.id}.version`);
    if (ids.has(kit.id)) {
      fail(
        "registry.duplicate_kit_id",
        "kit.id",
        `Qualified Modelica registry contains duplicate kit id '${kit.id}'.`,
      );
    }
    ids.add(kit.id);
    if (kit.scenarios.length === 0) {
      fail(
        "registry.no_scenarios",
        `${kit.id}.scenarios`,
        `Qualified Modelica kit '${kit.id}' declares no selectable scenarios.`,
      );
    }

    const scenarioIds = new Set<string>();
    for (const scenario of kit.scenarios) {
      canonical(scenario.id, `${kit.id}.scenario.id`);
      if (scenarioIds.has(scenario.id)) {
        fail(
          "registry.duplicate_scenario_id",
          `${kit.id}.scenarios`,
          `Qualified Modelica kit '${kit.id}' declares duplicate scenario '${scenario.id}'.`,
        );
      }
      scenarioIds.add(scenario.id);
    }

    const parameterIds = new Set<string>();
    for (const parameter of kit.parameters) {
      canonical(parameter.id, `${kit.id}.parameter.id`);
      canonical(parameter.modelicaName, `${kit.id}.${parameter.id}.modelicaName`);
      canonical(parameter.modelicaType, `${kit.id}.${parameter.id}.modelicaType`);
      canonical(parameter.unit, `${kit.id}.${parameter.id}.unit`);
      if (parameterIds.has(parameter.id)) {
        fail(
          "registry.duplicate_parameter_id",
          `${kit.id}.parameters`,
          `Qualified Modelica kit '${kit.id}' declares duplicate parameter '${parameter.id}'.`,
        );
      }
      parameterIds.add(parameter.id);
      if (
        !Number.isFinite(parameter.minimum) || !Number.isFinite(parameter.maximum) ||
        !Number.isFinite(parameter.defaultValue) || parameter.minimum > parameter.maximum ||
        parameter.defaultValue < parameter.minimum || parameter.defaultValue > parameter.maximum
      ) {
        fail(
          "registry.invalid_parameter_bounds",
          `${kit.id}.parameters.${parameter.id}`,
          `Qualified Modelica parameter '${parameter.id}' has incoherent default or bounds.`,
        );
      }
    }
  }
}

function canonical(value: unknown, field: string): void {
  if (typeof value !== "string" || value.trim().length === 0 || value !== value.trim()) {
    fail("registry.noncanonical_identity", field, `${field} must be a non-empty canonical string.`);
  }
}

function fail(code: string, field: string, message: string): never {
  throw new ValidationError(message, {
    code,
    field,
    recovery: "Correct the qualified KitRegistry contract before starting the MCP server.",
  });
}

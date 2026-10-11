import { z } from "zod";

export const WORKFLOW_INSTRUCTIONS_VERSION = "wright.workflow-instructions/1";
export const INSTRUCTION_ROLES = [
  "workflow-task",
  "image-generation",
  "mcp-task",
  "recovery",
  "protocol",
  "validation",
  "chat",
  "process-ui-author",
  "resource-context",
] as const;
const identifier = z
  .string()
  .trim()
  .min(1)
  .refine(
    (value) => [...value].length <= 160,
    "Instruction identifiers must have at most 160 characters.",
  );
const digest = z
  .string()
  .regex(/^[0-9a-f]{64}$/, "Use a lowercase SHA-256 instruction digest.");
const role = z.enum(INSTRUCTION_ROLES);
const assumptionPolicy = z.enum(["document_reasonable", "require_specified"]);
const unique = (values: string[]) => new Set(values).size === values.length;
const text = z
  .string()
  .refine(
    (value) =>
      !value.includes("\0") &&
      !/[\uD800-\uDFFF]/u.test(value) &&
      new TextEncoder().encode(value).length <= 131072,
    "Instructions must be valid UTF-8 text without NUL, within 128 KiB.",
  );
const assetSchema = z
  .object({
    schema_version: z
      .literal("wright.instruction-asset/1")
      .default("wright.instruction-asset/1"),
    id: identifier,
    role,
    version: identifier,
    body: text.refine(
      (value) => !!value.trim(),
      "Instruction bodies require meaningful text.",
    ),
    body_digest: digest,
    origin: identifier,
    variables: z.array(identifier).max(64).default([]),
    execution_contract: z
      .literal(WORKFLOW_INSTRUCTIONS_VERSION)
      .default(WORKFLOW_INSTRUCTIONS_VERSION),
  })
  .strict()
  .superRefine((asset, context) => {
    if (
      !unique(asset.variables) ||
      asset.variables.some((value) => !/^[a-z][a-z0-9_]*$/.test(value))
    )
      context.addIssue({
        code: "custom",
        path: ["variables"],
        message: "Instruction variables must be unique stable names.",
      });
    const placeholders = new Set(
      [...asset.body.matchAll(/\{\{([a-z][a-z0-9_]*)\}\}/g)].map(
        (match) => match[1],
      ),
    );
    if (
      placeholders.size !== asset.variables.length ||
      asset.variables.some((value) => !placeholders.has(value))
    )
      context.addIssue({
        code: "custom",
        path: ["variables"],
        message: "Template placeholders must match the declared variables.",
      });
  });
const policySchema = z
  .object({
    assumption_policy: assumptionPolicy.default("require_specified"),
    protected_requirements: z
      .array(identifier)
      .max(256)
      .refine(unique, "Protected requirements must be unique.")
      .default([]),
  })
  .strict();
const bindingSchema = z
  .object({
    role,
    asset_ids: z
      .array(identifier)
      .min(1)
      .max(64)
      .refine(unique, "A role cannot contain duplicate instruction assets."),
  })
  .strict();
const layerSchema = z
  .object({
    origin: identifier,
    roles: z
      .array(role)
      .min(1)
      .refine(unique, "Instruction layers require unique role scopes.")
      .default(["workflow-task", "image-generation", "mcp-task"]),
    mode: z.enum(["append", "replace"]).default("append"),
    text: text.default(""),
    assumption_policy: assumptionPolicy.nullable().default(null),
  })
  .strict()
  .superRefine((layer, context) => {
    if (layer.mode === "replace" && !layer.text.trim())
      context.addIssue({
        code: "custom",
        path: ["text"],
        message: "Replacement instructions require meaningful text.",
      });
  });
const instructionSetSchema = z
  .object({
    schema_version: z
      .literal(WORKFLOW_INSTRUCTIONS_VERSION)
      .default(WORKFLOW_INSTRUCTIONS_VERSION),
    profile_id: identifier,
    profile_version: identifier,
    action_intent_contract: z
      .literal("wright.workflow-action-intent/1")
      .nullable()
      .optional(),
    assets: z.array(assetSchema).min(1).max(128),
    bindings: z.array(bindingSchema).min(1).max(16),
    policy: policySchema.default({
      assumption_policy: "require_specified",
      protected_requirements: [],
    }),
    layers: z.array(layerSchema).max(16).default([]),
  })
  .strict()
  .superRefine((set, context) => {
    const assets = new Map(set.assets.map((asset) => [asset.id, asset]));
    if (assets.size !== set.assets.length)
      context.addIssue({
        code: "custom",
        path: ["assets"],
        message: "Instruction asset identities must be unique.",
      });
    if (!unique(set.bindings.map((binding) => binding.role)))
      context.addIssue({
        code: "custom",
        path: ["bindings"],
        message: "Instruction roles must have one ordered binding.",
      });
    for (const binding of set.bindings)
      for (const id of binding.asset_ids) {
        const asset = assets.get(id);
        if (!asset)
          context.addIssue({
            code: "custom",
            path: ["bindings"],
            message: `Saved role ${binding.role} references missing instruction body ${id}.`,
          });
        else if (asset.role !== binding.role)
          context.addIssue({
            code: "custom",
            path: ["bindings"],
            message: "Instruction bindings cannot cross role scopes.",
          });
      }
    if (
      set.assets.reduce(
        (size, asset) => size + new TextEncoder().encode(asset.body).length,
        0,
      ) > 524288
    )
      context.addIssue({
        code: "custom",
        path: ["assets"],
        message:
          "Saved instruction bodies exceed the 512 KiB collection limit.",
      });
  });

export type WorkflowInstructionSet = z.infer<typeof instructionSetSchema>;
export type WorkflowInstructionAsset = z.infer<typeof assetSchema>;
export type WorkflowInstructionOverride = z.infer<typeof layerSchema>;

export function normalizeWorkflowInstructionOverride(
  value: unknown,
): WorkflowInstructionOverride {
  const result = layerSchema.safeParse(value);
  if (!result.success)
    throw new Error(`Step instructions: ${result.error.issues[0].message}`);
  return result.data;
}

/** Mirrors core defaults; body digest verification remains with the backend save/compiler. */
export function normalizeWorkflowInstructions(
  value: unknown,
): WorkflowInstructionSet {
  const result = instructionSetSchema.safeParse(value);
  if (!result.success) {
    const issue = result.error.issues[0];
    throw new Error(
      `Workflow instructions ${issue.path.join(".") || "collection"}: ${issue.message}`,
    );
  }
  if (result.data.action_intent_contract == null) {
    const { action_intent_contract: _absent, ...legacy } = result.data;
    return legacy;
  }
  return result.data;
}

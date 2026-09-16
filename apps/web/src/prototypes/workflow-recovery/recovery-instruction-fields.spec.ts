import { describe, expect, it } from "vitest";
import { fromCanonicalWire, toCanonicalWire } from "./canonical-wire";
import { authoringConfigurationCommands } from "./authoring-objects";
import {
  initialWorkflow,
  RECOVERY_AUTHORING_INSTRUCTION_FIELD_KEY,
  RECOVERY_AUTHORING_SECONDARY_INSTRUCTION_KEY,
  RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY,
} from "./model";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
  validateRecoveryAuthoringRoundTrip,
} from "./recovery-authoring";

function source(
  actor: string,
  fields: string,
  settings = "{}",
  stepType = "work",
) {
  return `${formatRecoveryAuthoringSource(initialWorkflow).text}
task field_compatibility
  name: "Field compatibility"
  purpose: "Preserve engineering intent and executable instructions."
  step_type: "${stepType}"
  group: null
  performed_by: "${actor}"
  inputs: []
  outputs: []
${fields}
  settings: ${settings}
  tool: null
  reusable_step: null
end
`;
}

const both =
  '  instructions: "Original engineering intent"\n  prompt: "Executable task prompt"';

describe("canonical prompt and instructions compatibility", () => {
  it.each([
    ["ai_assisted", "{}", "work", "Executable task prompt", "prompt"],
    [
      "engineer",
      '{"authoring_template":"manual-review"}',
      "work",
      "Original engineering intent",
      "instructions",
    ],
    [
      "engineer",
      '{"authoring_template":"external-action-approval"}',
      "review",
      "Original engineering intent",
      "instructions",
    ],
  ])(
    "preserves both fields through wire, editing and cold authoring round trips for %s %s",
    (actor, settings, kind, active, activeField) => {
      const parsed = parseRecoveryAuthoringSource(
        source(actor, both, settings, kind),
        initialWorkflow,
      );
      expect(parsed.diagnostics).toEqual([]);
      expect(parsed.ok).toBe(true);
      const wire = JSON.parse(
        JSON.stringify(toCanonicalWire(parsed.workflow!)),
      );
      const reopened = fromCanonicalWire(wire);
      const block = reopened.blocks.find(
        (entry) => entry.id === "block.field-compatibility",
      )!;
      expect(block.instructions).toBe(active);
      expect(formatRecoveryAuthoringSource(reopened).text).toContain(
        'instructions: "Original engineering intent"',
      );
      expect(formatRecoveryAuthoringSource(reopened).text).toContain(
        'prompt: "Executable task prompt"',
      );
      block.instructions = "Edited current task";
      const formatted = formatRecoveryAuthoringSource(reopened).text;
      expect(formatted).toContain(`${activeField}: "Edited current task"`);
      expect(formatted).toContain(
        activeField === "prompt"
          ? 'instructions: "Original engineering intent"'
          : 'prompt: "Executable task prompt"',
      );
      expect(formatted).not.toContain("__wright_authoring_");
      const roundTrip = validateRecoveryAuthoringRoundTrip(reopened);
      expect(roundTrip.diagnostics).toEqual([]);
      expect(roundTrip.ok).toBe(true);
      expect(toCanonicalWire(roundTrip.workflow!)).toEqual(
        toCanonicalWire(reopened),
      );
    },
  );

  it.each([
    ["ai_assisted", '  instructions: "Legacy intent"', "instructions"],
    ["engineer", '  prompt: "Legacy review"', "prompt"],
  ])("retains the original sole field for %s", (actor, fields, field) => {
    const parsed = parseRecoveryAuthoringSource(
      source(actor, fields),
      initialWorkflow,
    );
    expect(parsed.diagnostics).toEqual([]);
    const block = parsed.workflow!.blocks.find(
      (entry) => entry.id === "block.field-compatibility",
    )!;
    expect(block.configuration[RECOVERY_AUTHORING_INSTRUCTION_FIELD_KEY]).toBe(
      field,
    );
    const formatted = formatRecoveryAuthoringSource(
      fromCanonicalWire(toCanonicalWire(parsed.workflow!)),
    ).text;
    const section = formatted.split("task field_compatibility")[1]!;
    expect(section).toContain(fields);
    expect(section).not.toContain(
      field === "prompt" ? "  instructions:" : "  prompt:",
    );
  });

  it.each([
    ["ai_assisted", '  prompt: "Active"\n  instructions: 42'],
    ["ai_assisted", '  prompt: "Active"\n  instructions: null'],
    ["engineer", '  instructions: "Active"\n  prompt: {}'],
    ["engineer", '  instructions: "Active"\n  prompt: false'],
  ])("rejects malformed secondary text for %s", (actor, fields) => {
    const parsed = parseRecoveryAuthoringSource(
      source(actor, fields),
      initialWorkflow,
    );
    expect(parsed.ok).toBe(false);
    expect(
      parsed.diagnostics.some(
        (entry) => entry.code === "WFR-SOURCE-FIELD-TYPE",
      ),
    ).toBe(true);
  });

  it.each([
    RECOVERY_AUTHORING_INSTRUCTION_FIELD_KEY,
    RECOVERY_AUTHORING_SECONDARY_INSTRUCTION_KEY,
    RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY,
  ])(
    "rejects reserved metadata injection through source or settings editor: %s",
    (key) => {
      const parsed = parseRecoveryAuthoringSource(
        source("ai_assisted", both, JSON.stringify({ [key]: "Injected" })),
        initialWorkflow,
      );
      expect(parsed.ok).toBe(false);
      expect(
        parsed.diagnostics.some(
          (entry) => entry.code === "WFR-SOURCE-FIELD-MANAGED",
        ),
      ).toBe(true);
      expect(() =>
        authoringConfigurationCommands(initialWorkflow.blocks[0]!, {
          [key]: "Injected",
        }),
      ).toThrow("Wright-managed settings");
    },
  );

  it("retains exact structured approval settings across wire round trips and prompt edits", () => {
    const settings = {
      authoring_template: "external-action-approval",
      action_kind: "local_review",
      approval_binding: {
        server: "wright",
        tool: "review_artifacts",
        schema: "pinned-schema",
      },
      approval_destination: { kind: "local_review", id: "workspace" },
      approval_settings: {
        review_task_id: "inspect",
        files: ["result.json"],
        overwrite: false,
      },
      approval_action: { kind: "local_review", mode: "review_only" },
    };
    const parsed = parseRecoveryAuthoringSource(
      source("engineer", both, JSON.stringify(settings), "review"),
      initialWorkflow,
    );
    expect(parsed.diagnostics).toEqual([]);
    const reopened = fromCanonicalWire(
      JSON.parse(JSON.stringify(toCanonicalWire(parsed.workflow!))),
    );
    const block = reopened.blocks.find(
      (entry) => entry.id === "block.field-compatibility",
    )!;
    block.instructions = "Review current files";
    expect(
      Object.values(block.configuration).every((value) =>
        ["string", "number", "boolean"].includes(typeof value),
      ),
    ).toBe(true);
    const text = formatRecoveryAuthoringSource(reopened).text.split(
      "task field_compatibility",
    )[1]!;
    expect(text).not.toContain("__wright_");
    expect(JSON.parse(text.match(/ {2}settings: (.+)/)![1]!)).toEqual(settings);
    const roundTrip = validateRecoveryAuthoringRoundTrip(reopened);
    expect(roundTrip.diagnostics).toEqual([]);
    expect(toCanonicalWire(roundTrip.workflow!)).toEqual(
      toCanonicalWire(reopened),
    );
  });

  it.each([
    { authoring_template: "external-action-approval", approval_binding: [] },
    { authoring_template: "external-action-approval", approval_action: null },
    { authoring_template: "external-action-approval", unknown_object: {} },
    { authoring_template: "mcp-task", approval_binding: {} },
  ])("rejects undocumented or malformed structured settings %j", (settings) => {
    const parsed = parseRecoveryAuthoringSource(
      source("engineer", both, JSON.stringify(settings)),
      initialWorkflow,
    );
    expect(parsed.ok).toBe(false);
    expect(
      parsed.diagnostics.some(
        (entry) => entry.code === "WFR-SOURCE-FIELD-TYPE",
      ),
    ).toBe(true);
  });
});

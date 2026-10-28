import { useState } from "react";
import type { RecoveryCommand } from "./command-system";
import {
  recoveryAuthoringSectionKind,
  type RecoveryBlock,
  type RecoveryWorkflow,
} from "./model";
import { sourceKey } from "./prompt-settings";
import {
  validationProfiles,
  validatorSettings,
  validationProfileCommands,
  validationRevisionCommands,
  validationRevisionLimitCommands,
  validationRevisionTargets,
  validationSubjectCommands,
} from "./validation-settings";

export function ValidatorBlockEditor({
  block,
  workflow,
  readOnly,
  onApply,
}: {
  block: RecoveryBlock;
  workflow: RecoveryWorkflow;
  readOnly: boolean;
  onApply: (commands: RecoveryCommand[]) => boolean;
}) {
  const [error, setError] = useState("");
  const settings = validatorSettings(block);
  const segmentCorrection = settings?.rework_scope === "verified_segment";
  const selected = validationProfiles.find(
    (p) => p.name === settings?.profile.name,
  );
  const revision = workflow.relationships.find(
    (edge) => edge.kind === "feedback" && edge.sourceId === block.id,
  );
  const revisionTargets = validationRevisionTargets(block, workflow);
  const apply = (build: () => RecoveryCommand[]) => {
    try {
      if (onApply(build())) setError("");
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "The validation settings could not be changed.",
      );
    }
  };
  const candidates = workflow.ports.filter((port) => {
    const owner = workflow.blocks.find((item) => item.id === port.ownerBlockId);
    return (
      port.direction === "output" &&
      port.cardinality !== "many" &&
      owner &&
      owner.id !== block.id &&
      owner.configuration.authoring_template !== "process-validator" &&
      recoveryAuthoringSectionKind(owner) !== "input" &&
      [
        "type.document.engineering",
        "type.result.structured",
        "type.value.text",
        "type.file.workspace",
        "type.geometry.brep",
        "type.analysis.result",
      ].includes(port.typeId)
    );
  });
  return (
    <section
      className="recovery-prompt-editor"
      data-testid="workflow-recovery-validator-editor"
    >
      <label>
        Validation profile
        <select
          value={
            settings?.profile.source === "packaged" ? settings.profile.name : ""
          }
          disabled={readOnly || segmentCorrection}
          onChange={(e) =>
            apply(() =>
              validationProfileCommands(block, workflow, e.target.value),
            )
          }
        >
          <option value="">Choose a validation profile</option>
          {validationProfiles.map((profile) => (
            <option key={profile.name} value={profile.name}>
              {profile.title}
            </option>
          ))}
        </select>
      </label>
      <p>
        Inspect a previous step’s output against the selected requirements.
        Downstream steps wait for a passing assessment.
      </p>
      {Object.entries(settings?.subjects ?? {}).map(([role, key]) => {
        const target = workflow.ports.find(
          (p) => p.ownerBlockId === block.id && sourceKey(p.id) === key,
        );
        const edge = workflow.relationships.find(
          (e) => e.kind === "data" && e.targetId === target?.id,
        );
        return (
          <label key={role}>
            Output to validate · {role}
            <select
              disabled={readOnly || !target}
              value={edge?.sourceId ?? ""}
              onChange={(e) =>
                target &&
                apply(() =>
                  validationSubjectCommands(
                    block,
                    workflow,
                    target.id,
                    e.target.value,
                  ),
                )
              }
            >
              <option value="">Choose a producing step output</option>
              {candidates.map((p) => (
                <option key={p.id} value={p.id}>
                  {workflow.blocks.find((b) => b.id === p.ownerBlockId)?.title}{" "}
                  · {p.name}
                </option>
              ))}
            </select>
          </label>
        );
      })}
      {selected && (
        <p className="recovery-field-help">
          Scope:{" "}
          {selected.excluded_scope.length
            ? `Excludes ${selected.excluded_scope.join(", ")}.`
            : "The checks declared in this profile."}
        </p>
      )}
      {settings && (
        <section aria-label="Automatic correction">
          {segmentCorrection && (
            <p>
              If this check fails, the workflow corrects the design and repeats
              the connected checks. These settings are defined in Source;
              readiness checks whether the steps can safely repeat.
            </p>
          )}
          <label>
            If validation finds a correctable defect
            <select
              aria-label="Validation revision target"
              value={revision?.targetId ?? ""}
              disabled={readOnly || segmentCorrection}
              onChange={(e) =>
                apply(() =>
                  validationRevisionCommands(block, workflow, e.target.value),
                )
              }
            >
              <option value="">Hold the process and report findings</option>
              {segmentCorrection && revision && !revisionTargets.some((item) => item.id === revision.targetId) && (
                <option value={revision.targetId}>
                  Correct {workflow.blocks.find((item) => item.id === revision.targetId)?.title ?? "the designated step"} and repeat connected checks
                </option>
              )}
              {revisionTargets.map((item) => (
                <option key={item.id} value={item.id}>
                  Return findings to {item.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Maximum corrected revisions
            <input
              aria-label="Maximum corrected revisions"
              type="number"
              min={0}
              max={3}
              disabled={readOnly || !revision}
              value={Number(block.configuration.max_revisions ?? 0)}
              onChange={(e) =>
                apply(() =>
                  validationRevisionLimitCommands(
                    block,
                    workflow,
                    Number(e.target.value),
                  ),
                )
              }
            />
          </label>
          <p className="recovery-field-help">
            Zero disables automatic correction. A correction creates a new
            output revision and reruns the complete pinned profile; downstream
            steps stay held until the current revision passes.
          </p>
        </section>
      )}
      {error && <p role="alert">{error}</p>}
      {settings && (
        <details className="recovery-technical-details">
          <summary>Requirement and profile references</summary>
          <p>
            Profile {settings.profile.reference.id}, version{" "}
            {settings.profile.reference.version}. Requirements{" "}
            {settings.baseline.id}, version {settings.baseline.version}.
          </p>
          <pre>{JSON.stringify(settings, null, 2)}</pre>
        </details>
      )}
    </section>
  );
}

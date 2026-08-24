import type { CanvasCandidateId } from "../canvas/canvas-adapter";

export type CandidateCriterionId =
  | "visual-fidelity"
  | "phase-and-feedback-grammar"
  | "accessibility"
  | "canonical-separation"
  | "component-testability"
  | "scale"
  | "maintenance-and-security"
  | "bundle-cost"
  | "deletion-cost";

export interface CandidateCriterion {
  criterionId: CandidateCriterionId;
  label: string;
  weight: number;
  minimumScore?: number;
  evidenceRequired: string;
}

export interface CandidateCriterionScore {
  criterionId: CandidateCriterionId;
  score: 0 | 1 | 2 | 3 | 4 | 5;
  evidence: string;
}

export interface CandidateEvaluation {
  candidateId: CanvasCandidateId;
  scores: CandidateCriterionScore[];
}

export const candidateRubric: readonly CandidateCriterion[] = [
  {
    criterionId: "visual-fidelity",
    label: "Visual-contract fidelity",
    weight: 2,
    evidenceRequired: "Reference-size screenshot and visual review notes",
  },
  {
    criterionId: "phase-and-feedback-grammar",
    label: "Phase lanes, gates, ports, and feedback paths",
    weight: 2,
    evidenceRequired: "Reference fixture plus cross-phase and feedback edges",
  },
  {
    criterionId: "accessibility",
    label: "Accessible navigation and selection",
    weight: 3,
    minimumScore: 3,
    evidenceRequired: "Semantic queries, keyboard inspection, and axe result",
  },
  {
    criterionId: "canonical-separation",
    label: "Wright model remains canonical",
    weight: 3,
    minimumScore: 3,
    evidenceRequired: "Dependency review and candidate deletion exercise",
  },
  {
    criterionId: "component-testability",
    label: "Fast deterministic component tests",
    weight: 3,
    minimumScore: 3,
    evidenceRequired: "Focused test command, duration, and failure class",
  },
  {
    criterionId: "scale",
    label: "25- and 100-block interaction",
    weight: 2,
    evidenceRequired: "Render, fit, select, and focus timing",
  },
  {
    criterionId: "maintenance-and-security",
    label: "Maintenance, licensing, and security",
    weight: 2,
    evidenceRequired: "Official-source review, pinned version, and audit",
  },
  {
    criterionId: "bundle-cost",
    label: "Lazy bundle cost",
    weight: 1,
    evidenceRequired: "Production chunk measurement",
  },
  {
    criterionId: "deletion-cost",
    label: "Candidate deletion cost",
    weight: 2,
    evidenceRequired: "Files/imports/dependencies required for removal",
  },
] as const;

export interface CandidateEvaluationResult {
  weightedScore: number;
  maximumWeightedScore: number;
  passing: boolean;
  missingCriteria: CandidateCriterionId[];
  failedMinimums: CandidateCriterionId[];
}

export function evaluateCandidate(
  evaluation: CandidateEvaluation,
): CandidateEvaluationResult {
  const scoreByCriterion = new Map(
    evaluation.scores.map((score) => [score.criterionId, score]),
  );
  const missingCriteria = candidateRubric
    .filter(({ criterionId }) => !scoreByCriterion.has(criterionId))
    .map(({ criterionId }) => criterionId);
  const failedMinimums = candidateRubric
    .filter(({ criterionId, minimumScore }) => {
      const score = scoreByCriterion.get(criterionId)?.score;
      return minimumScore !== undefined && score !== undefined
        ? score < minimumScore
        : false;
    })
    .map(({ criterionId }) => criterionId);
  const weightedScore = candidateRubric.reduce(
    (total, criterion) =>
      total +
      (scoreByCriterion.get(criterion.criterionId)?.score ?? 0) *
        criterion.weight,
    0,
  );
  const maximumWeightedScore = candidateRubric.reduce(
    (total, criterion) => total + 5 * criterion.weight,
    0,
  );

  return {
    weightedScore,
    maximumWeightedScore,
    passing: missingCriteria.length === 0 && failedMinimums.length === 0,
    missingCriteria,
    failedMinimums,
  };
}

import { describe, expect, it } from "vitest";

import {
  candidateRubric,
  evaluateCandidate,
  type CandidateEvaluation,
} from "./candidate-rubric";

function completeEvaluation(score: 0 | 1 | 2 | 3 | 4 | 5): CandidateEvaluation {
  return {
    candidateId: "react-flow",
    scores: candidateRubric.map(({ criterionId }) => ({
      criterionId,
      score,
      evidence: "Fixture evidence",
    })),
  };
}

describe("evaluateCandidate", () => {
  it("requires complete evidence and all mandatory minimums", () => {
    const result = evaluateCandidate(completeEvaluation(3));

    expect(result.passing).toBe(true);
    expect(result.missingCriteria).toEqual([]);
    expect(result.failedMinimums).toEqual([]);
  });

  it("cannot hide an accessibility failure behind a high total score", () => {
    const evaluation = completeEvaluation(5);
    evaluation.scores = evaluation.scores.map((score) =>
      score.criterionId === "accessibility" ? { ...score, score: 2 } : score,
    );

    const result = evaluateCandidate(evaluation);

    expect(result.passing).toBe(false);
    expect(result.failedMinimums).toContain("accessibility");
  });
});

import { describe, expect, it } from "vitest";

import { rankedCandidateEvaluations } from "./candidate-evaluations";

describe("candidate evaluation evidence", () => {
  it("selects React Flow only after every mandatory minimum is met", () => {
    expect(
      rankedCandidateEvaluations.map(({ evaluation, result }) => ({
        candidateId: evaluation.candidateId,
        weightedScore: result.weightedScore,
        maximumWeightedScore: result.maximumWeightedScore,
        passing: result.passing,
        failedMinimums: result.failedMinimums,
      })),
    ).toEqual([
      {
        candidateId: "react-flow",
        weightedScore: 91,
        maximumWeightedScore: 100,
        passing: true,
        failedMinimums: [],
      },
      {
        candidateId: "rete",
        weightedScore: 70,
        maximumWeightedScore: 100,
        passing: false,
        failedMinimums: ["component-testability"],
      },
      {
        candidateId: "litegraph",
        weightedScore: 41,
        maximumWeightedScore: 100,
        passing: false,
        failedMinimums: ["accessibility", "component-testability"],
      },
    ]);
  });

  it("contains complete evidence for every candidate", () => {
    for (const { evaluation, result } of rankedCandidateEvaluations) {
      expect(evaluation.scores).toHaveLength(9);
      expect(result.missingCriteria).toEqual([]);
      expect(
        evaluation.scores.every(({ evidence }) => evidence.trim().length > 0),
      ).toBe(true);
    }
  });
});

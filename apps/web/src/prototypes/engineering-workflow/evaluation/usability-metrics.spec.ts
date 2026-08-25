import { describe, expect, it } from "vitest";

import {
  comprehensionConcepts,
  evaluateComprehensionGate,
  type ComprehensionTrial,
} from "./usability-metrics";

function scores(
  incorrect: (typeof comprehensionConcepts)[number][] = [],
): ComprehensionTrial["correct"] {
  return Object.fromEntries(
    comprehensionConcepts.map((concept) => [
      concept,
      !incorrect.includes(concept),
    ]),
  ) as ComprehensionTrial["correct"];
}

function passingTrials(): ComprehensionTrial[] {
  const rivetTimes = [100, 110, 120, 130, 140];
  const prototypeTimes = [60, 70, 80, 90, 100];

  return rivetTimes.flatMap((elapsedSeconds, index) => {
    const participantId = `P${index + 1}`;
    return [
      {
        participantId,
        surface: "rivet" as const,
        sequence: index % 2 === 0 ? (1 as const) : (2 as const),
        elapsedSeconds,
        coached: false,
        correct: scores(),
      },
      {
        participantId,
        surface: "prototype" as const,
        sequence: index % 2 === 0 ? (2 as const) : (1 as const),
        elapsedSeconds: prototypeTimes[index],
        coached: false,
        correct: scores(index === 4 ? ["toolActions"] : []),
      },
    ];
  });
}

describe("evaluateComprehensionGate", () => {
  it("passes five paired trials at 80% full comprehension and 30% improvement", () => {
    const result = evaluateComprehensionGate(passingTrials());

    expect(result.passed).toBe(true);
    expect(result.pairedParticipantCount).toBe(5);
    expect(result.rivet?.medianSeconds).toBe(120);
    expect(result.prototype?.medianSeconds).toBe(80);
    expect(result.prototype?.fullyCorrectRate).toBe(0.8);
    expect(result.medianTimeImprovement).toBeCloseTo(1 / 3);
    expect(result.reasons).toEqual([]);
  });

  it("does not turn an incomplete or coached review into a passing result", () => {
    const trials = passingTrials().filter(
      ({ participantId }) => participantId !== "P5",
    );
    trials[0] = { ...trials[0], coached: true };

    const result = evaluateComprehensionGate(trials);

    expect(result.passed).toBe(false);
    expect(result.pairedParticipantCount).toBe(3);
    expect(result.reasons).toEqual(
      expect.arrayContaining([
        expect.stringContaining("coached trial"),
        expect.stringContaining("at least 5"),
      ]),
    );
  });

  it("rejects duplicate surface trials instead of selecting a favorable one", () => {
    const trials = passingTrials();

    expect(() => evaluateComprehensionGate([...trials, trials[0]])).toThrow(
      "Duplicate comprehension trial",
    );
  });
});

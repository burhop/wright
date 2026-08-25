export const comprehensionConcepts = [
  "phases",
  "inputs",
  "toolActions",
  "reviewGates",
  "feedbackPath",
  "artifacts",
] as const;

export type ComprehensionConcept = (typeof comprehensionConcepts)[number];
export type ComprehensionSurface = "rivet" | "prototype";

export interface ComprehensionTrial {
  participantId: string;
  surface: ComprehensionSurface;
  sequence: 1 | 2;
  elapsedSeconds: number;
  coached: boolean;
  correct: Record<ComprehensionConcept, boolean>;
}

export interface SurfaceComprehensionSummary {
  surface: ComprehensionSurface;
  participantCount: number;
  fullyCorrectCount: number;
  fullyCorrectRate: number;
  medianSeconds: number;
  conceptCorrectRates: Record<ComprehensionConcept, number>;
}

export interface ComprehensionGateResult {
  passed: boolean;
  pairedParticipantCount: number;
  rivet: SurfaceComprehensionSummary | null;
  prototype: SurfaceComprehensionSummary | null;
  medianTimeImprovement: number | null;
  reasons: string[];
}

function fullyCorrect(trial: ComprehensionTrial): boolean {
  return comprehensionConcepts.every((concept) => trial.correct[concept]);
}

function median(values: number[]): number {
  const ordered = [...values].sort((left, right) => left - right);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 === 0
    ? (ordered[middle - 1] + ordered[middle]) / 2
    : ordered[middle];
}

function validateTrials(trials: readonly ComprehensionTrial[]): void {
  const identities = new Set<string>();

  for (const trial of trials) {
    if (!trial.participantId.trim()) {
      throw new Error("Comprehension trials require a participant ID.");
    }
    if (!Number.isFinite(trial.elapsedSeconds) || trial.elapsedSeconds <= 0) {
      throw new Error("Comprehension elapsed time must be positive.");
    }

    const identity = `${trial.participantId}:${trial.surface}`;
    if (identities.has(identity)) {
      throw new Error(`Duplicate comprehension trial ${identity}.`);
    }
    identities.add(identity);

    for (const concept of comprehensionConcepts) {
      if (typeof trial.correct[concept] !== "boolean") {
        throw new Error(`Trial ${identity} is missing score ${concept}.`);
      }
    }
  }
}

function summarizeSurface(
  surface: ComprehensionSurface,
  trials: readonly ComprehensionTrial[],
): SurfaceComprehensionSummary {
  const fullyCorrectCount = trials.filter(fullyCorrect).length;
  const conceptCorrectRates = Object.fromEntries(
    comprehensionConcepts.map((concept) => [
      concept,
      trials.filter((trial) => trial.correct[concept]).length / trials.length,
    ]),
  ) as Record<ComprehensionConcept, number>;

  return {
    surface,
    participantCount: trials.length,
    fullyCorrectCount,
    fullyCorrectRate: fullyCorrectCount / trials.length,
    medianSeconds: median(trials.map(({ elapsedSeconds }) => elapsedSeconds)),
    conceptCorrectRates,
  };
}

/**
 * Evaluates the CP2 gate using only uncoached, within-participant pairs.
 * Results never imply that a missing or non-equivalent Rivet baseline passed.
 */
export function evaluateComprehensionGate(
  trials: readonly ComprehensionTrial[],
): ComprehensionGateResult {
  validateTrials(trials);

  const reasons: string[] = [];
  const coached = trials.filter((trial) => trial.coached);
  if (coached.length > 0) {
    reasons.push(
      `${coached.length} coached trial(s) were excluded and must be rerun without coaching.`,
    );
  }

  const eligible = trials.filter((trial) => !trial.coached);
  const byParticipant = new Map<
    string,
    Partial<Record<ComprehensionSurface, ComprehensionTrial>>
  >();
  for (const trial of eligible) {
    const participant = byParticipant.get(trial.participantId) ?? {};
    participant[trial.surface] = trial;
    byParticipant.set(trial.participantId, participant);
  }

  const paired = [...byParticipant.values()].filter(
    (
      participant,
    ): participant is Record<ComprehensionSurface, ComprehensionTrial> =>
      participant.rivet !== undefined && participant.prototype !== undefined,
  );
  if (paired.length < 5) {
    reasons.push(
      `Need at least 5 uncoached paired participants; recorded ${paired.length}.`,
    );
  }

  if (paired.length === 0) {
    return {
      passed: false,
      pairedParticipantCount: 0,
      rivet: null,
      prototype: null,
      medianTimeImprovement: null,
      reasons,
    };
  }

  const rivet = summarizeSurface(
    "rivet",
    paired.map((participant) => participant.rivet),
  );
  const prototype = summarizeSurface(
    "prototype",
    paired.map((participant) => participant.prototype),
  );
  const medianTimeImprovement =
    (rivet.medianSeconds - prototype.medianSeconds) / rivet.medianSeconds;

  if (prototype.fullyCorrectRate < 0.8) {
    reasons.push(
      `Prototype full-comprehension rate is ${(prototype.fullyCorrectRate * 100).toFixed(1)}%; need at least 80%.`,
    );
  }
  if (medianTimeImprovement < 0.3) {
    reasons.push(
      `Prototype median-time improvement is ${(medianTimeImprovement * 100).toFixed(1)}%; need at least 30%.`,
    );
  }

  return {
    passed:
      paired.length >= 5 &&
      prototype.fullyCorrectRate >= 0.8 &&
      medianTimeImprovement >= 0.3,
    pairedParticipantCount: paired.length,
    rivet,
    prototype,
    medianTimeImprovement,
    reasons,
  };
}

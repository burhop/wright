import {
  evaluateCandidate,
  type CandidateEvaluation,
  type CandidateEvaluationResult,
} from "./candidate-rubric";

export const candidateEvaluations: readonly CandidateEvaluation[] = [
  {
    candidateId: "react-flow",
    scores: [
      {
        criterionId: "visual-fidelity",
        score: 4,
        evidence:
          "Reference-size capture preserves the accepted shell and block anatomy; generic step edges still need custom feedback-rail polish.",
      },
      {
        criterionId: "phase-and-feedback-grammar",
        score: 4,
        evidence:
          "Phase lanes, ports, labels, direction, and non-color feedback cues render from the neutral projection.",
      },
      {
        criterionId: "accessibility",
        score: 4,
        evidence:
          "Vitest verifies semantic phase/connection summaries, keyboard selection, focus, and zero detectable axe violations; color contrast remains a browser/manual check.",
      },
      {
        criterionId: "canonical-separation",
        score: 5,
        evidence:
          "Only the adapter imports React Flow; Wright owns IDs, roles, positions, semantics, selection, and persistence boundaries.",
      },
      {
        criterionId: "component-testability",
        score: 5,
        evidence:
          "Real-library component, scale, semantic, keyboard, and axe checks run deterministically in Vitest/jsdom.",
      },
      {
        criterionId: "scale",
        score: 5,
        evidence:
          "25 blocks render/select/focus in 399.1 ms and 100 blocks in 548.6 ms in the recorded development-machine run.",
      },
      {
        criterionId: "maintenance-and-security",
        score: 5,
        evidence:
          "Current MIT package pinned at 12.11.3; no candidate advisory; single primary package and React 19 compatibility.",
      },
      {
        criterionId: "bundle-cost",
        score: 3,
        evidence:
          "Lazy chunk is 181.29 kB minified and 58.53 kB gzip, excluding the shared shell.",
      },
      {
        criterionId: "deletion-cost",
        score: 5,
        evidence:
          "Delete one adapter directory, two focused evaluation imports, one lazy route/import pair, and one dependency; canonical fixtures and shell remain.",
      },
    ],
  },
  {
    candidateId: "rete",
    scores: [
      {
        criterionId: "visual-fidelity",
        score: 4,
        evidence:
          "Reference-size capture is strong, but required custom socket and SVG connection renderers to reach it.",
      },
      {
        criterionId: "phase-and-feedback-grammar",
        score: 5,
        evidence:
          "Custom rails preserve phase lanes, labels, direction, and feedback paths particularly well.",
      },
      {
        criterionId: "accessibility",
        score: 3,
        evidence:
          "The same keyboard and axe checks passed with zero detectable violations, but the 6.73 s run emitted roughly 2,000 lines of independent-root act warnings.",
      },
      {
        criterionId: "canonical-separation",
        score: 5,
        evidence:
          "Rete remains a disposable renderer over the Wright projection and is not used for persistence.",
      },
      {
        criterionId: "component-testability",
        score: 2,
        evidence:
          "25-block interaction took 4.53 s with extensive React act warnings; the 100-block selection did not settle inside 20 s.",
      },
      {
        criterionId: "scale",
        score: 2,
        evidence:
          "25 blocks completed, but the 100-block interaction failed the bounded benchmark.",
      },
      {
        criterionId: "maintenance-and-security",
        score: 4,
        evidence:
          "MIT v2 ecosystem with no candidate advisory, but the representative integration requires six pinned packages.",
      },
      {
        criterionId: "bundle-cost",
        score: 4,
        evidence:
          "Lazy chunk is 110.31 kB minified and 33.03 kB gzip, smaller than React Flow.",
      },
      {
        criterionId: "deletion-cost",
        score: 3,
        evidence:
          "Adapter isolation is good, but removal includes six dependencies and more candidate-specific rendering code.",
      },
    ],
  },
  {
    candidateId: "litegraph",
    scores: [
      {
        criterionId: "visual-fidelity",
        score: 2,
        evidence:
          "Canvas cards lose approved anatomy, gate shapes, readable density, and DOM component reuse.",
      },
      {
        criterionId: "phase-and-feedback-grammar",
        score: 2,
        evidence:
          "Phase and feedback overlays require parallel custom Canvas2D drawing outside native graph grammar.",
      },
      {
        criterionId: "accessibility",
        score: 1,
        evidence:
          "Native canvas nodes need a duplicate off-screen DOM interface; required keyboard-plus-axe evidence was not achievable in the T1 tier.",
      },
      {
        criterionId: "canonical-separation",
        score: 4,
        evidence:
          "A pure projection keeps Wright canonical, although the parallel accessibility DOM risks presentation drift.",
      },
      {
        criterionId: "component-testability",
        score: 1,
        evidence:
          "Real runtime needs Canvas2D emulation or a browser; jsdom can cover only the pure projection.",
      },
      {
        criterionId: "scale",
        score: 1,
        evidence:
          "Not promoted to the shared scale interaction after failing earlier mandatory requirements.",
      },
      {
        criterionId: "maintenance-and-security",
        score: 2,
        evidence:
          "MIT and no npm advisory, but older maintenance/type signals and direct eval in every supplied bundle reduce confidence.",
      },
      {
        criterionId: "bundle-cost",
        score: 1,
        evidence:
          "Lazy chunk is 507.87 kB minified and 125.16 kB gzip and independently triggers the 500 kB warning.",
      },
      {
        criterionId: "deletion-cost",
        score: 4,
        evidence:
          "One primary dependency and isolated directory are removable, despite custom canvas and accessibility projections.",
      },
    ],
  },
] as const;

export interface RankedCandidateEvaluation {
  evaluation: CandidateEvaluation;
  result: CandidateEvaluationResult;
}

export const rankedCandidateEvaluations: readonly RankedCandidateEvaluation[] =
  candidateEvaluations
    .map((evaluation) => ({
      evaluation,
      result: evaluateCandidate(evaluation),
    }))
    .sort(
      (left, right) => right.result.weightedScore - left.result.weightedScore,
    );

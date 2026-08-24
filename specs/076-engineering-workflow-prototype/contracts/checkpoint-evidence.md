# Contract: Prototype Checkpoint Evidence

Every checkpoint creates a short, reviewable evidence record tied to an exact commit.

Required fields:

- checkpoint ID and hypothesis;
- commit and environment;
- acceptance criteria with pass/fail/deferred status;
- commands, durations, outcomes, and failure classification;
- screenshots or recordings for visual claims;
- usability participants/tasks/observations when applicable;
- dependency/license/bundle observations for library decisions;
- known limitations and explicit non-goals;
- decision: continue, change, stop, or defer;
- named human reviewer and review date;
- bounded next checkpoint.

Failure classes are `product`, `test`, `environment`, or `unknown`. Retrying an environment failure does not erase the original result.

Checkpoint evidence is committed under the feature spec. Raw large browser artifacts remain ignored unless needed to substantiate a decision.

No checkpoint is considered accepted because tests passed alone. CP1, CP2, CP4, CP5, CP6, and CP7 require human review of the relevant UI or decision record.

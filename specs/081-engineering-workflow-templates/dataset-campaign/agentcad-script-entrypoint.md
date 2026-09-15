# AgentCAD script entry point

Bracket case01 attempt003, run `29bc105d877b4725a7968167115364cd`, authored
source with `if __name__ == '__main__': main()`. Its body never ran in the
selected AgentCAD environment. Read-only package inspection confirmed the exact
installed versions: AgentCAD 0.6.0, build123d 0.10.0 and NumPy 2.5.2. The installed
`agentcad/runners/build123d.py` declares `__name__='__agentcad_script__'`, injects
the real `show_object` callback and executes the source with those globals.

The evidence at
`.local-run/feature-081-live/campaign-execution/bracket003-entrypoint-diagnosis.json`
records installed runner and failed-source hashes, the actual declaration line,
source-tail AST and unchanged failed source. A pure-Python probe using the
AST-derived execution context reproduced zero callback captures for the old
guard and one for an unconditional module-scope `main()` call. This imports no
CAD and constructs no geometry. The test excerpt is a snapshot of the selected
runner's actual execution seam, not an alternative production runner.

`scripts/agentcad_source_contract.py` provides shared future-authoring guidance:
invoke `main()` at module scope if using a main function; use the actual injected
`show_object`; never replace it with a stub, import or no-op fallback; fail if
the callback is unavailable. The guidance applies to bracket, heat, jig source
and independent inspection, and Pi CAD preparers. It does not edit previously
enrolled sources or guarantee that a future model-authored program will obey
the instructions; real native execution and output checks remain required.

Fresh bracket attempt004 for all three datasets is normally instantiated,
mapped, saved and enrolled in
`.local-run/feature-081-live/campaign-execution/bracket-attempt-004.json`.
Its companion staging-verification file records current pins, exact source and
policy identities, complete input maps, all original stage IDs and edges, and
absence of declared generated outputs. All twelve stages remain, including four
explicit native field/reaction expansions and the original final comparison.
Only private init CLI operations ran; no CAD or solver was dispatched.

Twenty-seven focused tests passed, including executable callback-contract
probes, missing-callback failure, changed runner-seam rejection, canonical
preparation and negative input mapping. Ruff passed. Old bracket003 files/grants
and active batch009 remain unchanged. No API or Hermes restart is required.

The remaining queued CAD-authoring cases were subsequently prepared as new
immutable retries: jig attempt007 (three), heat attempt007 (three), and Pi visual
attempt005 (three). Their combined replacement manifest is
`.local-run/feature-081-live/campaign-execution/entrypoint-nine-replacements.json`.
`entrypoint-nine-staging-verification.json` records all preserved IDs/edges,
current pins, complete mapped inputs, entry-point guidance and absence of
generated outputs. All private initialization commands exited successfully.
`entrypoint-nine-normal-preparation-verification.json` additionally records nine
successful ordinary policy/source preparations through a lifecycle that rejects
all tool dispatch. Thirty related executable-contract, preparer and input-map
tests passed. The jig circle-center guidance, heat direct-solver/result-inspection
stages and Pi visual/context-paging fixes remain in every applicable new source.
The prior jig/heat006 and Pi004 grants and files remain unchanged; bracket004
was not prepared again. No native generation, model or solver ran in this work.

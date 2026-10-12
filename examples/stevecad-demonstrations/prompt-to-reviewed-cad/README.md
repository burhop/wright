# Prompt to reviewed CAD

One reusable process with seven engineering stages. Start with the supplied
four-hole block prompt, then run the same accepted source with the six-hole
prompt. Later prompts introduce complex parts, mating assemblies, motion and a
small 3D-printable industrial-style robot arm. The retained revision-7 arm now
has native CAD images, rendered views, a design/export package and two MP4 clips.
Its failed and unverified engineering findings remain explicit. At the user's
12 October check-in request, additional design runs are stopped for this code
checkpoint; see [check-in scope](../../../docs/demos/stevecad-check-in.md).

The completed v19 four-hole block is the end-to-end proof. The six-hole prompt
reuses exactly the same accepted source and routing. The bracket also completes,
with separately retained wall-thickness measurements and a corrected top-render
addendum. The current native source contains the prospective v20 top-camera
correction, compiled and qualified on the actual bracket scene; a full v20
workflow run has not been performed. Historical source revisions stay retained.

The original v13 source has one design-prompt input and eight execution tasks.
The native-render successor retains the same seven stages, replacing the three
AI image edits with an explicit CAD export, private file transfer, validated
mesh and native three-view rendering. It has sixteen execution tasks and five
AI-authored document/CAD stages. The current
editor uses standard individual nodes; custom source-created grouping is not
claimed to work.

## Prepare and use

1. Use this branch's Wright runtime, the connected SteveCAD MCP, a configured
   text/tool-capable agent and qualified native image output. The isolated local
   instance is `http://wright.localhost:8891/`.
2. `python examples/stevecad-demonstrations/prompt-to-reviewed-cad/prepare.py`
   renders and checks the reusable source. This script prepares source only.
3. Save/open `prompt-to-reviewed-cad.workflow.wflow` through Wright's workflow
   source service/editor. The local attempts use explicitly versioned paths
   under `workflows/`; older revisions and run records remain unchanged.
4. Open the working view. Supply **What should we build?**, check readiness and
   start. Input overrides are run inputs; editing the source is unnecessary.
5. Find each run's documents and images under `design-reviews/<run-id>/` and its
   exact results in the working view. The review HTML references sibling images.
6. For the reuse check, choose `prompts/02-six-hole-block.txt` as the input value
   on the same accepted source. Confirm a new run/output directory and changed
   measured dimensions and hole pattern.

The robot package is a digital prototype. Servo choices, complete hardware
contacts, load capability, printing, physical assembly and operation are not
qualified. No hardware motion, printing or public posting is performed.

For the native successor, run `prepare_native.py` and open
`prompt-to-reviewed-cad-native.workflow.wflow`. The preparer preserves the v13
instruction bodies and embeds the native template plus qualified provider
bindings. Review any local provider substitution and rediscover schema digests.
The scoped mounts must match `native-render-bindings.json` and the usage guides.
Documents and all six images use
`render-proofs/native-chain-001/renders/<run-id>/`; exact STEP, GLB and handoff
receipts use `render-proofs/native-chain-001/automatic-transfer-001/<run-id>/`.
The original v13 outputs remain under `design-reviews/`.

Native v14's first live run stopped after correcting its CAD because a redundant
document read hit the existing repeat-call guard. Its source/run remain intact.
V15 adds explicit top-face hole anchoring and uses completed write/generate
receipts instead of redundant reads. This is a visible authoring revision, not
an automatic bypass or a change to saved run instructions. Consult the progress
record for current live completion evidence.

The accepted v7 source regenerates from the original default
`prompts/01-drilled-block.txt`. The clarified four-hole run input is retained in
`prompts/01-drilled-block-clarified.txt`; six-hole reuse uses
`prompts/02-six-hole-block.txt`; the next exercise uses `prompts/03-l-bracket.txt`.
Run input changes do not change accepted source. Consult the
[SteveCAD guide](../../../docs/mcp-catalog/usage-guides/stevecad-mcp.md) before
new tool work.

## Image handoff contract

An ordinary MCP agent task may declare `settings.mcp_image_outputs` as a JSON
object or JSON-encoded string. Use the string form for the existing editor.
Each key identifies an already-declared workspace-file output:

```json
{"top_capture":{"tool":"inspect_model","arguments":{"view":"top"},"image_index":0}}
```

The selected tool must be in `mcp_task_tools`. Its argument subset must identify
exactly one successful image-bearing response in that task. `image_index` selects
the zero-based image within that response. The file must also appear in
`expected_files` and `expected_file_ports` with a PNG/JPEG extension matching its
actual bytes. Boundaries and image hashes are checked before publication.

The normal file/result owners save the returned bytes and expose exact output
ports to downstream tasks. A run event retains the tool-call number, content
index, output path and digest. Missing/ambiguous responses, wrong formats,
changed bytes and existing destinations fail. The model cannot create evidence
by claiming that an image exists. Run paths and subsequent file hashes retain
the existing invalidation and review rules. No external download or additional
executor is introduced.

## Evidence and limits

The source and supporting image handoff are under active local verification.
Live attempts and failed runs are retained in
`artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/`; UI walkthroughs are
under `artifacts/ui-walkthrough/prompt-to-reviewed-cad/`.

Actual CAD captures and numerical observations support geometric checks.
Photorealistic images are presentation derivatives. A process completion or
model-generated PASS is not human engineering acceptance; the final review must
retain unverified and failed requirements. Native image transport availability
does not by itself prove a successful render or geometric fidelity.

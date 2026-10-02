# Heat-spreader proof progress

**Status:** preparation implemented; live engineering and UI proof pending.
**Checkpoint:** 2 October 2026 UTC.

The new example at `examples/process-interfaces/heat-spreader-sizing/` prepares a
connected source using the original three substantive stages and unchanged
`heat-spreader-sizing-01` assignment. It copies original input bytes with their
frozen digests and pins the original full 082 profile. Exact selected provider
IDs, fresh Wright tool/schema identities, native project path and solver mount
are supplied explicitly. No new provider executor or vendor wrapper is introduced.

The prepared definition connects authored CAD source to its native operation and
each actual exported STEP/measurement file to the recorded solver call. The
existing numerical operation checks reopened CAD measurements and STEP hashes
before rectangular meshing. It preserves both candidates, actual coarse/fine
fields, original analytical/refinement/balance thresholds, 45 °C decision limit,
`critic_approved=false`, current assessment and declared reviews.

`tests/test_process_interface_examples.py`: **7 passed**, 2.35 seconds, no skips.
Command:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_process_interface_examples.py --basetemp=.local-run/process-interfaces-083/t046-preparation-tests-006 -o cache_dir=.local-run/process-interfaces-083/pytest-cache-t046 --tb=short --junitxml=.local-run/process-interfaces-083/t046-preparation-tests-006.xml -q
```

The fixture project manifest and tool hashes establish **declarative checks only**.
No model, CAD host, solver, accepted live run, rendered browser, synthetic reviewer,
human engineering acceptance or physical operation was exercised by this suite.
It checks compilation and exact full-profile subjects, original-byte preservation,
missing-tool preflight, mount constraints, exact/fresh project identity, and
preservation of existing attempts. Ruff checks pass on the three added Python files.

Failed test roots remain private. Compiler requirements were retained: source IDs
were normalized, every staged input connected, direct tool references bound as
actual file dependencies, and original source-copy bytes preserved without newline
normalization. These fixes do not relax engineering checks.

Provider qualification is separately described in
[provider-qualification.md](provider-qualification.md). AgentCAD read-back is
qualified; its creation-response formatter warning remains explicit. The prepared
workflow retains the raw creation response and performs separate actual read-back,
without relabeling the response or blindly replaying creation.

Pending T046/T047: run the accepted prepared definition through Wright's normal
owner/API with fresh native providers and an exact isolated test policy; retain
real waiting/resume and current 082 assessments; compose/generate/update/save/reuse
both common and tailored views from actual outputs. These preparation checks do
not complete the engineering proof.

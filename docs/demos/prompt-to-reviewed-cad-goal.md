Build and demonstrate one reusable Wright workflow that turns an engineering design prompt into a verified SteveCAD design and an illustrated design review. Begin with a drilled block, increase complexity gradually, and finish with a small 3D-printable industrial-style robot arm assembly.

Continue the existing work in:
D:\repos\wright\.local-run\stevecad-engineering-demos
Branch: codex/stevecad-engineering-demos

First read AGENTS.md, the required architecture guidance, and the existing prompt-to-reviewed-cad implementation and evidence. Inspect existing runs before starting anything new. Preserve completed work and useful failure evidence. This replaces the earlier three-demo portfolio objective; do not resume its protected runs.

Implement and prove this seven-stage process:
1. Accept a natural-language design prompt.
2. Produce an engineering design document specifying geometry, dimensions, units, materials or presentation finishes, interfaces, assumptions, and measurable requirements.
3. Produce a test plan before creating the CAD model, with requirement IDs, acceptance criteria, and verification methods.
4. Create the design in SteveCAD from that document.
5. Execute the test plan against the actual CAD geometry and record measured results, model revision, and supporting evidence.
6. Capture three useful CAD orientations and create three ultrarealistic renderings derived from those captures.
7. Produce an illustrated design review linking requirements, test results, original captures, renderings, limitations, and deliverable files.

Finish the simplest example end to end before increasing complexity. Prove reuse with another design prompt using the same accepted workflow. Then progress through a bracket, a small joint assembly, and the printable robot arm. Change the input prompt rather than creating a separate workflow for every example. Make workflow revisions only when a demonstrated general limitation requires them.

For the robot arm, include printable parts, assembly instructions, a bill of materials, declared joint ranges, and appropriate fit and interference checks. Declare hardware and printing assumptions. Produce verified export files. Distinguish digital validation from physical print, assembly, or operating tests.

Toward the end, capture actual CAD assembly or motion video and prepare an unpublished marketing package with selected images, video, and accurate captions. Renderings are presentation assets; they do not establish dimensional correctness.

Keep execution inside Wright’s existing durable runtime, gateway, validation, results, and workspace UI. Preserve recorded model settings for existing runs. Avoid extra orchestration layers, unnecessary approval gates, and repeated speculative retries. Resolve routine choices autonomously; retain genuine engineering reviews and required external-action authority.

Maintain a discoverable SteveCAD MCP best-practices document for future agents, and establish the same documentation practice for every MCP server used. Record verified examples, capabilities, pitfalls, recovery procedures, versions, and evidence links.

Investigate suspected SteveCAD bugs carefully. Separate our code, assumptions, and integration errors from provider defects. Report confirmed bugs through SteveCAD’s supported channel with a minimal reproduction, expected and observed behavior, exact inputs, relevant versions, and redacted evidence. Preserve report IDs and avoid duplicate submissions.

Post concise progress updates and occasional actual images. Track elapsed time and recurring blockers so the workflow becomes faster and more dependable.

Complete with a reusable workflow, verified progressively richer examples, the robot-arm design package, three final renderings, captured video where supported, an illustrated review, and maintained MCP guidance. State clearly what passed, failed, remains unverified, or requires physical testing. Do not publish marketing material, release software, or claim user acceptance without authorization.
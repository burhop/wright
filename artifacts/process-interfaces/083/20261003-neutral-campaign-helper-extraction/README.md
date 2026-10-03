# Neutral engineering campaign helpers

Eleven existing declaration/staging functions now live in a shared helper file.
Eleven other example preparers and their input-binding fixture load that file
directly, removing their dependency on the printing-specific preparer. The latter
also loads the exact helper file rather than relying on an installed scripts
namespace. Every extracted function AST and all other example preparation
function bodies are unchanged; original campaign bindings/evidence are preserved.

The first direct-launch check exposed an import-namespace defect; the corrected
launch works even with an unrelated scripts namespace. The first regression run
records five passes and twenty-four temporary-directory permission setup errors.
Fresh workspace-confined test directories pass thirty-five helper/original-input
checks and thirty-nine affected example checks, with no skips. Three owning files
pass Ruff; denied shared cache writes are non-fatal warnings, not test failures.

This is preparatory migration work. Vendor slicing implementations remain active
in their two actual preparers/probe until deliberate replacement, and T048/T049
remain open. No vendor executor, protocol or device wrapper was moved into the
neutral helper. The retained AgentCAD entrypoint guidance is existing metadata.
No engineering process, protected review or physical operation ran.

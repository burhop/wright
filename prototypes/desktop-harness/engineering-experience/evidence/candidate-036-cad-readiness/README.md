# Candidate CAD readiness clarification

Read-only candidate Connections inspection reports SteveCAD not installed,
inactive, not enabled and without local validation. Compatibility is uncertain.
This fresh isolated workspace must complete setup; prior installed-workspace
credentials or protocol evidence do not establish its readiness. The catalog's
credentials_missing=false is not proof of successful authentication.

The compiler still rejects unconfigured steps. Its user-facing correction now
asks to configure the required tool/task while preserving required checks and
reviews, instead of suggesting replacing the step with an AI prompt. All 22
workflow-source execution tests pass, including the named unconfigured-step
case. No provider invocation, account change, credential copy or installation
occurred. Installed desktop plugin and candidate frozen backend are unchanged;
this message improvement needs the planned coherent candidate build.

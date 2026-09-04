# Native saved-process API checkpoint

September 4, 2026. T009–T011 implementation is present. Migration 17 adds native
document/request/run/event/step/artifact tables without modifying legacy rows.
Document create/update uses explicit BEGIN IMMEDIATE, conditional tokens and one
commit for the current/previous envelopes and original idempotent response.
Workspace-authorized service calls and strict bounded HTTP requests share the
same authoritative validator. Caller-supplied MCP bindings cannot establish
readiness until actual gateway verification is implemented.

Focused precommit results: 20 repository/migration checks passed, including two
competing writers, fault injection between envelope and request insertion,
original-result replay after later saves, workspace scoping, interrupted upgrade,
predecessor rejection without modification, a verified backup restored to a
separate schema16 root, and forward reopening of retained native work. Ten API
checks passed using actual SQLite/service and existing workspace authorization,
including programmatic/API parity, role/token checks, strict duplicate-key and
size rejection, stale writers and safe trace-linked errors. The initial API
test invocation hit a host sandbox denial while discovering the unrelated Hermes
CLI; explicit empty test config paths and a private temporary directory resolved
the harness issue. Scoped Ruff lint/format passed.

Independent foundation review found an inherited Decimal exponent/trap issue on
78d0d5af. Commit `1d0cd0798130fa5c3e7c8a0e78655090ac95f5d9` uses a complete private
context; the independent reviewer closed the finding after rerunning the failing
probes and regression. This review does not yet cover these persistence/API files.

Actual editor/backend browser parity, runtime, real MCP, human validation,
packaged predecessor verification and dev integration remain pending.

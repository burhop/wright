# Saved UI revision compatibility â€” scoped owner/API proof

The primary audit reproduced an implementation gap: compatibility compared the
saved manifest to the exact source digest before checking its declared bindings.
A valid managed-source CAS with matching required input bindings was rejected.
Updating after a source change was already supported; that initial suspicion
was corrected rather than recorded as a new defect.

The existing owners now distinguish immutable build origin from current
presentation context. Only saved UIs in the same workspace/source family can
reuse origin bytes after bindings are checked against the current accepted
catalog. Native grants and the bridge use the exact current process. Draft
generation/preview/save, runs, evidence, reviews and actions retain their existing
revision checks. Required schema changes block presentation/activation; a focused
update saves a new current revision with original parent/source/build provenance.
Optional absent bindings keep their declared fallback.

## Verified scope

The final 14-module group passes **242 cases, no failures/errors/skips**.
Six new primary cases inspect actual managed-source creation/CAS, immutable
revision owners, native presentations/grants, bridge and HTTP dispatch, required
and optional binding checks, focused update/preview/save and denied rollback.
Model/compiler/runtime responses are controlled; affected fixed-builder tests
retain their individual compiler scope. No live model/MCP engineering run,
engineering review, physical or supplier operation was submitted.

- [Exact command and source hashes](attempt-007-command.json)
- [Result](attempt-007-result.json) and [case assertions](primary-assertions.json)
- [Case index](attempt-007-case-index.json) and [JUnit](attempt-007-results.xml)
- [Checked ownership/preservation scope](checked-scope.json)
- [Contract](../../../../specs/083-process-working-interfaces/contracts/ui-authoring-and-hosting.md)

The earlier 240-case group is a subset, not another disjoint total. First attempt
001 failed because the reused fixture wrote outside managed storage and changed
Windows line endings. Attempt002 reproduced the compatibility defect; its second
case also exposed guessed input metadata (READINESS_UNSUPPORTED), corrected to
the existing version/value_schema contract. Attempt003 passes the first two cases.
Attempt004 passes240. Attempt005 has241 passes and one bridge-fixture failure:
it attempted to transplant current authority into the same old presentation.
The corrected fixture creates a fresh isolated presentation/runtime identity as
the native owner does, while revoking the old view. Attempt006 checks that
correction and007 reruns the whole affected group. All original failures remain
in the linked records and are not relabelled as passing behavior.

## Remaining work and resources

No new installed/browser proof of this correction is claimed. Prior installed
evidence retains its original wheel and behavior. Rebuild and verify the saved
reuse/incompatible-update/common-fallback journey through the normal workspace
entry before closing the broader compatibility obligation. The cumulative
semantic ledger remains **36 proved /146 awaiting review /182 total**; T056/T057
stay open and the goal remains active.

Owned prior hosts90330 (thermal, port63271) and46681 (printed, port50062) were
revalidated running and left untouched at their original build scope. The new
tests start no persistent host/provider. Protected engineering reviews remain
held; 550 engineering/UI files and unrelated work are verified by the local
commit guard. No push, merge, release or public promotion is authorized.

Publication note: pytest records remain byte-exact in the private capture. Public
text uses LF line endings to match repository blob normalization; JSON/XML/log
content and assertion results are unchanged. The first commit guard rejected
CRLF-versus-LF artifact hash differences before committing. Only its54 owned
paths were unstaged for this bounded publication correction.

The second guard retained four pytest diagnostic lines with trailing spaces in
public log/XML text. Their trailing whitespace is trimmed for repository lint;
original raw captures, failure status and assertion text remain preserved.

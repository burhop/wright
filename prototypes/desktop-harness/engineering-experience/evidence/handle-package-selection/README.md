# Passive comparison and proposed package selection

Local reference operation: `scripts/engineering/compare_handle_slices.py`.
The existing package inspector reads each exact oriented mesh, package, profiles,
and recorded provider response. The comparison retains measured toolpath counts,
original package identity and native preview identity. Counts do not establish
support contact area, material usage, time, strength or manufacturing acceptance.

A separate explicit selection retains its rationale and comparison hash, rechecks
both alternatives' meshes/packages/previews, and copies the selected package and
preview byte-for-byte to fresh outputs. It neither slices nor prints nor approves.
Backend file dependency checks, independent engineering validation and human
review remain required. Hash consistency is not authenticity or review authority.

Tests use synthetic packages through the actual recorded-observation producer,
package inspector and toolpath reader. They cover preserved original files,
exact copies, changed selected and unselected inputs, changed comparison,
missing rationale, destination escape/alias/collision and overwrite rejection.
These tests do not qualify a real handle or Windows display.

This operation is not yet bound in accepted candidate revision 7 or installed.
The independent provider must receive inspectable pinned operation dependencies;
no host source paths may be assumed. Interrupted writes retain partial evidence
and fail on retry into the same outputs; automatic replay is not authorized.

Independent review found two gaps before binding: legacy responses were admitted,
and mesh/package paths could be swapped independently of observed arguments.
Both are now rejected in preflight, with negatives proving no inspection outputs
are published. The qualified reference assumes the invocation and inspection
share the declared workspace mount; a different mount needs an explicit supported
mapping, never basename matching. Focused source re-review found no remaining
blocker; it did not establish engineering execution.

Final affected suite: **189 passed** (`pytest-final.txt`); Ruff and diff checks pass.
The earlier sandboxed suite stalled near completion and was interrupted; its
partial `pytest.txt` is retained. Final tests ran outside the sandbox against
isolated fixtures, without provider execution or live configuration changes.

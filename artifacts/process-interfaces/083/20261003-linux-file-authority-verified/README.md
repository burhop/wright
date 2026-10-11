# Linux file-boundary authority verification

The three symlink security cases skipped by the current Windows affected suite
run and pass on Linux: document writes cannot follow a directory symlink outside
the attempt; reads reject a source symlink outside the attempt; copies reject
an existing source symlink and preserve the external bytes. These use actual
Linux symlinks and current shared production sources, not replacement shims.

Four owning modules pass 95 checks with one Windows-only case skipped on Linux.
That exact Windows case passed in the retained 746-pass Windows suite. Counts
overlap earlier coverage and must not be added as distinct tests.

Attempt002 failed before tests because the neutral image's user could not write
the selected dependency directory. Fresh003 installed pinned pytest9.0.3 and
pytest-asyncio1.4.0 in writable temporary storage; all three symlink cases passed,
but one broader gateway test lacked its fixture module in the source snapshot.
Fresh004 includes that existing fixture and reuses the verified selected test
environment. Both failures are preserved; no product guard or test was weakened.

The runtime is offline, with one read-only current-source snapshot mount and
writable Linux temporary test files. Exact source hashes match the checkout
before/after execution; imported shared packages resolve to that snapshot.
The immutable base image is unchanged. Five exact owned containers across the
attempts are stopped and revalidated. No MCP/model/engineering/physical operation
ran. This is selected Linux source-test evidence, not fresh product installation,
browser acceptance, provider qualification, or completion of T053/Feature083.

# Local WebKit host limitation

A minimal cached Playwright WebKit2336 launch aborts before page creation, inside
and outside the sandbox. Private pinned libraries resolved all missing linker
dependencies; the launcher version control succeeds. No shared packages or
browser-cache files were modified.

A bounded debugger trace now establishes the cause for this exact WPE build:
`WTF::pageSize()` calls `sysconf(_SC_PAGESIZE)`, then compares its result with
`0x4 << 12` (16384). This host returns65536. The branch reaches the retained
`PageBlock.cpp` assertion at line65. The exact cached library digest, ELF
instructions, source/function strings and debugger logs are recorded in
[the diagnosis](../../../artifacts/first-contact/084/provider-readiness/gate-preparation/webkit-page-limit-001/diagnosis.json).
The trace's stripped return address points immediately after that assertion call;
the decoded preceding branch and line number identify the failed check.

[Upstream's page-size contract](https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WTF/wtf/PageBlock.h)
explains that its compile-time ceiling must accommodate actual system pages.
That current source is explanatory reference; exact cached-build attribution
comes from the retained binary observation. No assertion was disabled, binary
patched or incompatible build relabelled as qualified.

This is a local browser prerequisite limitation. No WebKit application test or
full browser gate passed. The merge script permits a documented local browser
limitation via `SKIP_PLAYWRIGHT=1`; if used, its other gates and separately runnable
Chromium coverage still need actual results, and supported-host/CI browser
qualification remains separate. The goal's final gate evidence must state this
limitation explicitly rather than treating an absent suite as green.

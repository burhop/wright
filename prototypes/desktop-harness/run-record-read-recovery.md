# Windows run-record observation correction

Status: isolated local implementation on `codex/desktop-record-read-recovery`,
base dfa853a999aef15e01dc825b3af5a0f3c541ceff. Not pushed or installed.

PR156 Windows job116319245177 failed while cancellation read the exact durable
record: Python file open raised PermissionError errno13. Cancellation correctly
returned OUTCOME_UNKNOWN. The originating native handle was not observed;
sharing contention is the tested failure-class hypothesis, not a proven handle
identity. Preserve the CI log and never convert unreadable evidence to success.

The existing recorder reader now retries access-denied reads only on Windows,
with five fixed waits totaling0.5 seconds. Every attempt rechecks the existing
workspace confinement and reads a complete bounded body. Missing files, other
I/O failures, malformed JSON and identity violations remain failures. Persistent
access denial remains an error. No workflow mutation or provider call is retried.

The deterministic test failed against the old reader and passes with this change.
32 focused recorder/cancellation/observation checks pass on the host; two actual
Windows file-sharing tests are skipped on GB10 and must pass native Windows CI.
The earlier sandbox invocation passed the five read tests but timed out before
the provider fixture entered; it was explicitly interrupted after failure and
retained. The unchanged host fixture passes. Lint, formatting and diff checks pass.

Evidence: /tmp/wright-run-record-read-recovery-20261015/{red.log,green.log,green-host.log}.
Microsoft documents exclusive handle sharing and release semantics in
[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

Next: consolidate with the download fix only after the frozen running gate
finishes; run current-candidate repository gates and all Windows checks. This
correction does not complete desktop acceptance or any engineering demonstration.

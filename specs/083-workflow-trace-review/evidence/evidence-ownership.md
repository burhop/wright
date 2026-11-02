# Evidence Ownership

Feature 083 does not call validators. The API accepts strict version-1 producer
envelopes, rejects unsupported schemas and mismatched runs, and stores the
producer, version, record identity, exact subjects, statement, outcome, links,
and supersession identity verbatim.

The UI labels this material "Producer-supplied evidence" and states that Trace
does not run validators or create an acceptance verdict. Artifact-to-evidence
navigation is bidirectional when the producer supplies an exact artifact subject.
Unmatched requirements, approvals, inputs, and assumptions remain attributable
text rather than being attached by inference.

Validation work may proceed independently and can integrate through the
implemented producer envelope; it is not a feature-083 completion dependency.
Deferred feature-081 content validation remains disabled.

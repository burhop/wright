# Complete assembly observations at the model boundary

11 October 2026. The engineer's process must carry actual multi-part geometry,
editable source and validation results into its later stages. The first robot
exposed a real boundary problem: its native build result was larger than one
Hermes text part, and the recovery's read response included a large duplicate
JSON text copy. Both runs stopped before another model request, retaining their
actual effects and errors. This is a Wright transport issue, not a SteveCAD bug.

The existing bridge now partitions oversized JSON containers at structural
boundaries. Hermes may join those text parts with whitespace; parsing still
produces the same complete values. Source strings and numeric tokens remain
indivisible. An oversized scalar still fails before submission. Tool visibility,
argument validation, model locks, permission checks and instruction bodies are
unchanged; no new executor or provider protocol is introduced.

The existing model-facing observation projection also omits a host envelope's
redundant `text` only when strict JSON parsing proves that it is the complete
same `result`. All native fields remain. Differing numeric tokens, booleans,
extra error prose, duplicate keys, ambiguous JSON and opaque text are retained.
No cross-call comparison is used. Original envelopes and gateway observations
remain in durable run evidence; this changes only their model-facing encoding.

126 owning/affected tests pass, including installed Hermes normalization,
retained feature failures and negative controls. Passive replay of the exact
terminal `robot-arm-002` decision input passes with 123684 transport bytes,
three parts, maximum part length 64565 characters, and complete equality of
both retained native results. See
`artifacts/stevecad-demonstrations/qualification/assembly-observation-transport/robot-recovery-input-proof.json`.
This is not an actual model/provider continuation or a successful robot run.
Live v10 correction subsequently saved revision 2 and received its complete
93-kilobyte native fit/motion metadata, but exceeded the bridge's existing
200000-byte total decision-input budget on the following model call. Passive
qualification of that exact input at 400000 bytes retains all eleven native
results: 274017 transport bytes, six parts, maximum 65534 characters. See
`robot-large-failure-input-proof.json` in the same evidence directory.

The accepted v11 adds the typed `mcp_context_budget_bytes: 400000` only to its
creation and inspection tasks. The compiler admits strict integers 16384–1048576
only for MCP-agent tasks; unsupported decision adapters fail before dispatch.
The existing decision bridge and invocation evidence receive this setting.
The executor's per-tool envelope guard also respects the explicit budget: the
observed 286333-byte complete read envelope had exceeded its separate default
262144-byte guard. Unspecified settings retain both earlier defaults. Neither
case removes native failure fields, changes model routing, or authorizes edits.

149 affected checks passed for the saved budget; 137 passed after the separate
envelope-guard correction (overlapping scopes). Tests preserve default rejection
and explicit-budget retention of the complete failure data. Live `robot-arm-005`
then passed the actual large read, one revision-checked write, full native build,
and subsequent model decision on v11. It stopped honestly on revision-3 CAD
interference, rather than on these transport limits. This proves that observed
continuation scope, not completion of the robot or unrestricted provider support.
A substantially different existing live workflow remains a qualification before
broad integration.

Accepted v9 and v10 sources retain their saved instruction bodies. v10 increases
the document/test-plan space to support multi-part specifications, allows one
revision-checked batch correction of an explicitly owned multi-file document,
and permits declared materials with native finish/color. It stays inside the
existing 32-call and 600-second task limits. Preserve earlier failed runs and
their omitted/unperformed checks; never turn recorded animation metadata into
an assertion that collision checking ran.

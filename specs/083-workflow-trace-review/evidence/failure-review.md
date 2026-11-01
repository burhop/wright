# Failure Review

Source adapters and page tests cover failed, blocked, cancelled, interrupted,
and legacy checkpoint states. Failed/stopped reports keep partial outputs,
recorded error codes, failed-step labels, recovery text, and possible external
residue. No missing completion time is invented and no incomplete run receives a
success label.

Browsing uses read-only inspection/projection calls. The only execution control
shown for a terminal Rivet failure is the existing explicit full-rerun command;
opening a report, graph element, prompt, artifact, or evidence record performs no
retry, tool call, approval change, or validation.

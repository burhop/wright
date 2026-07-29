# Data Model: CodeQL Security Hardening

No persistent schema changes are required. The feature introduces transient security value objects and evidence records.

## Health Probe Target

- **Logical URL**: normalized original HTTP/HTTPS destination used for Host, redirect, and reporting semantics.
- **Scheme / host / port / path / query**: structurally parsed URL fields.
- **Trusted local origin**: whether a non-global local destination is authorized by loopback rules or the exact configured Wright LLM/health origin.
- **Resolved addresses**: bounded, deduplicated canonical IP literals from one resolution.
- **Address class**: loopback, private IPv4, IPv6 ULA, global, or prohibited class.
- **Pinned address**: one validated numeric address used as the actual request host.
- **Redirect count / visited logical URLs**: state enforcing hop and loop bounds.

### State Transitions

`raw -> parsed -> origin-authorized -> resolved -> addresses-approved -> pinned -> requested -> healthy/unhealthy`

Any invalid syntax, unauthorized origin, prohibited address, unsafe redirect, timeout, or bounded-resource failure transitions directly to a sanitized `unhealthy` result without contacting a prohibited destination.

## Vault Object

- **Storage key**: generated UUID plus optional allowlisted extension; never derived as a path from the client filename.
- **Display filename**: sanitized client-facing basename retained as metadata only.
- **Vault root**: canonical configured storage root.
- **Canonical file**: resolved candidate proven to be a direct child/contained regular file beneath the root.

## Session Workspace Authorization

- **Requested workspace**: optional client string treated only as a lookup reference.
- **Registered workspace**: SQLite record containing the authoritative canonical local path.
- **Managed generated workspace**: UUID-named child of the canonical Wright workspace root, created only when no workspace was supplied.
- **Authorization outcome**: registered-existing, generated-managed, or rejected.

## Package Reference

- **Manager**: uv/uvx/pip/python/npm.
- **Source kind**: distribution identity, scoped npm identity, or structurally parsed VCS requirement.
- **Validated package identity**: manager-specific normalized name safe for registry paths and argv values.
- **Executable identity**: validated tool token following a VCS requirement when applicable.

## Safe Client Error

- **Generic message**: stable user-actionable text with no internal exception detail.
- **Trace ID**: correlation identifier returned in the body/event and response header where applicable.
- **Protected diagnostic**: complete structured server log entry containing exception type/context.

## Alert Disposition Evidence

- **Alert number and rule**
- **Feature/dev commit**
- **Focused regression tests**
- **CodeQL state**: fixed, dismissed-used-in-tests, or dismissed-false-positive
- **Dismissal explanation**: required only for #2 and, conditionally, #13
- **Branch distinction**: dev result separated from any remaining main instance

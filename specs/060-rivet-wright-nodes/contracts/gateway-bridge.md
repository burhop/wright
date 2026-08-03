# Gateway bridge contract

`invoke(invocation)` validates immutable run scope and delegates only to
`GatewayService`. Denial, approval required, expiry, revocation, unavailable
tool, and tool failure are typed results, not bypasses.

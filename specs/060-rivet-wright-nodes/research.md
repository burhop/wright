# Research

`GatewayService` already evaluates required workspace approvals and builds an
approval context from server session identity. The bridge must invoke this path
and never reuse Rivet external-call names as authority.

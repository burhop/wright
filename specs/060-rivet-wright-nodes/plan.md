# Plan

Create a workspace-service `RivetGatewayBridge` port over `GatewayService`.
It accepts only immutable run scope and declared tool inputs, derives gateway
session context server-side, and returns bounded typed results. It must not be
reachable from the Node fixture until the runner gains a separately approved
protocol update. Program-wide approval applies.

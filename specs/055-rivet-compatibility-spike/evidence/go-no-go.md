# Decision: conditional go

Proceed only to the workspace-persistence slice, which must prove a workspace-scoped editor IO/dataset adapter and a Wright-owned runner bridge. Do not adopt the Rivet editor bundle or publish a production dependency yet.

Blocking adoption condition: the upstream v1.25.0 source cannot rebuild offline on Windows because its committed Yarn cache omits required platform artifacts. Resolve this through a verified, immutable Wright build supply chain before editor packaging.

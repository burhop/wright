# Tool Metadata Contract

## Discovery Projection

For every valid child `tools/list` entry, Wright stores and projects:

- `name`,
- optional `title`,
- optional `description`,
- `inputSchema`,
- optional `outputSchema`,
- standard `annotations`.

Wright may namespace the outward name to prevent collisions, but it must retain the original tool name for child calls and must not remove tools because of provider identity.

## Trust Boundary

- Descriptions, titles, schemas, and annotations originate at the server and are untrusted input.
- Wright may validate call inputs and outputs against advertised schemas.
- Standard annotations are forwarded as descriptive hints only.
- Approval requirements, user enablement, workspace authorization, and destructive-action policy come only from trusted Wright configuration.
- Trusted approval requirements are stored separately from advertised annotations and may be exposed in Wright-owned `_meta` fields.

## Compatibility

- Missing titles, output schemas, or annotations are valid.
- Older cached rows default missing fields to `null` or `{}`.
- Refreshing a server replaces cached metadata with the latest advertised contract.
- Servers that advertise two otherwise identical tool contracts receive identical Wright behavior regardless of name, source URL, category, or vendor.

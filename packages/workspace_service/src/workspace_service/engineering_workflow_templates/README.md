# Engineering workflow template resources

This package contains immutable seed material for Wright's canonical workspace workflow editor. A template is never an editable or executable authority. Instantiation validates the exact packaged version, replaces semantic identities, and exclusively creates a new workspace-owned `.workflow.wflow` source plus separate layout and origin metadata.

Required resources:

- `catalog.yaml`: exactly ten versioned engineering entries in display order.
- `templates/<id>.workflow.wflow`: canonical editable seed source.
- `layouts/<id>.json`: presentation positions keyed by seed semantic IDs.
- `previews/<id>.svg`: project-created local preview assets; alt text and reuse rights are catalog metadata.
- `inputs/<id>/`: distributable fixture identity, attribution, and rights records where supplied.

Catalog validation fails closed on an unknown field shape, duplicate or unsafe ID, invalid version, missing or invalid source/layout, absolute or escaping resource path, missing rights record, unsupported readiness state, or credential-valued fields. Instantiation also rejects a source digest that changed after preview.

Readiness is derived from separate facts. Packaged fixtures and template validity do not prove configuration, MCP qualification, current availability, real backend execution, Wright execution, engineering verification, external receipt, physical completion or user acceptance.

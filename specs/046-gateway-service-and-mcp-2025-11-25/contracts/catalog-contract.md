# Canonical Catalog Contract

The packaged YAML resource is the sole authored catalog source and validates against the packaged JSON schema before use.

Required entry fields include canonical ID, name, category, transport/setup metadata, provenance, validation status/evidence/date, platform constraints, safety metadata, and aliases. A passed validation state requires complete clean-container evidence. Duplicate IDs/aliases and unknown required enum values fail loading.

API, gateway, plugin export, and generated Python projections must have exact canonical ID/count/metadata parity. Wheel and sdist tests must prove both resource and schema are included.

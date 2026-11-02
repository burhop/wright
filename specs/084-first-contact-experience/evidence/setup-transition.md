# Starter setup transition

The shipped template's static readiness previously remained a permanent run
block on every accepted revision of an instantiated source. Feature 084 records
the exact instantiated source digest in the existing immutable origin metadata.
A differing, accepted semantic revision now reaches the existing compiler,
input/tool checks, frozen model routing and authority preflight. This transition
does not issue an integration grant or establish engineering readiness.

The original instance, format-only edits, a revision restored to its original
bytes and legacy origins without an exact instantiated digest retain the catalog
gate. A stale supplied source digest is rejected. Existing source-copy behavior
still drops template lineage and qualifies the copied source through ordinary
preflight; a copy is not an engineering qualification.

Scoped verification: 15 tests passed in 1.72 seconds in
`artifacts/first-contact/084/setup-transition-final-tests.xml`. Tests exercise real
source storage, compiler and preflight, including absent model/tool capabilities,
unchanged provenance, stale identity, placeholder/cosmetic changes and copies.
No model/provider calls or durable run creation occur. The first attempt's two
failures came from test fixtures missing mandatory editor fields; the unchanged
authoring validator correctly rejected them. That raw result is retained in
`setup-transition-tests.xml`; only the fixtures were corrected.

The API/editor transition and installed native verification remain separate
work in T007/T018. A useful configured handle source, exact provider binding and
fresh engineering run are still required.

# Independent standard 3MF geometry reader

Status: implemented and focused tests verified; no handle execution or acceptance
claim. The native package regression is the actual tiny Orca 2.4.2 ARM fixture
retained in [provider readiness](provider-readiness.md). Its original diagnostic
used a 0.000001 mm comparison threshold and observed error below 1e-12 mm.

The added passive reader accepts a binary original STL, prepared Core3MF and
actual native 3MF. It checks unchanged prepared model triangles, the explicitly
declared rigid build transform, all composed native component/build transforms,
world triangle correspondence and inverse reconstruction in original model axes.
Triangle matching retains multiplicity, requires finite nondegenerate normals
with positive agreement, and rejects reversed winding even for triangles smaller
than the coordinate tolerance. Source, prepared and final package hashes remain
distinct evidence identities. No engine, provider, runner or protocol is added.

The new profile declares a **0.0001 mm numerical serialization bound**, matching
the earlier orientation-study conversion bound and allowing float32 recentering
at handle scale. This does not change the original 118/28/34 mm envelope or any
feature requirement. The existing coarse-bin ordering is conservative: geometry
near bin boundaries or tied coordinates can be rejected despite equivalence.
Such rejection must be diagnosed, not silently accepted or retried with a larger
tolerance. The earlier tiny fixture is not described as having used this bound.

Parsing is bounded by archive/member/expanded-byte/ratio limits, original STL
counts, total triangle/XML entity limits, recursion depth and resource budgets.
It rejects unsafe or duplicate members, cycles, non-millimetre units, nonfinite
coordinates/composition overflow, encoded XML declarations/entities and multiple
build instances. Budget/cancellation failures retain their existing authority.
Literal package-header inspection and opt-in prepared-digest lineage are additive
operations; original checks and the original profile remain unchanged.

Focused verification on 23 October 2026:

```text
/tmp/wright084-quality-venv/bin/python -m pytest \
  tests/external/process_validation/test_three_mf_geometry.py \
  tests/external/process_validation/test_printing.py \
  tests/external/process_validation/test_printed_profiles.py -q
47 passed, 4 skipped in 2.25s
```

The four existing skips require optional local retained full-profile artifacts;
they are not new test waivers. New portable tests retain only the three small
actual fixture files and provenance hashes. Tests convert the ASCII fixture to
binary STL in memory; that derived subject has a different digest and is not
claimed as the provider's original byte receipt. The actual native member name
is deliberately not Printed02's required `3D/Objects/object_1.model`; the new
recipe must prove its authored object name in a real run without relaxing that
original inventory check.

Independent review found and corrected matrix overflow/NaN false acceptance,
encoded XML declarations, and tiny reversed-triangle acceptance within a numeric
coordinate tolerance. Final independent read-only review reported no remaining
blocking finding and retained the conservative ordering limitation above.

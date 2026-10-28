# CAD-derived structural field qualification

Fresh isolated Linux ARM64 gateway job `80f2f335` consumed the retained CAD-derived mesh from [meshing qualification](../cad-mesh-qualification/README.md). This is a synthetic numerical prerequisite, not a replacement-handle strength assessment or an accepted engineering review.

The existing OASiS/scikit-fem backend solved 1 N and 2 N cases on the same 934-node, 2,872-tetrahedron mesh. The fixture uses isotropic E=1000 MPa, Poisson ratio 0.3, fixed translations at x-min and distributed downward force at x-max. These values are test inputs, not an approved PETG material or handle load/support specification.

| Independent check | Result |
|---|---|
| Recorded file digests and finite fields | PASS, eight exact files |
| Supports and force balance | PASS, maximum imbalance below 4e-13 N |
| Load/displacement energy identity | PASS |
| Doubling load doubles every recorded displacement/stress component | PASS |
| Existing Wright structural CSV readers | PASS, 934 nodes and 11,488 stress samples per case |
| Mesh convergence, appropriate material/support model, strength compliance | NOT ESTABLISHED |
| Durable handle workflow, human review, Windows acceptance | NOT ESTABLISHED |

Maximum displacement is 0.03643617 mm at 1 N and 0.07287233 mm at 2 N. Maximum recorded von Mises stress is 0.18302062 MPa and 0.36604125 MPa respectively. These are observations of the synthetic model, not safe-load claims. OASiS retained `trustworthy_result:false`; no critic approval was supplied.

`request.json` preserves the exact submitted input and restricted container command. `structural_probe.py` is a formatting-only copy. The output fields are compressed in `recorded-fields.tar.gz`, with their original individual hashes in `structural-check.json` and archive hash in `provenance.json`. To recheck offline, extract to a fresh temporary directory, copy `structural-check.json` there, and run `check_structural.py DIRECTORY` using the Wright development environment. No solver rerun is needed. The checker uses recorded CSVs and Wright's existing field readers; it does not decode VTU contents or confer approval.

No live enrollment, credentials, server lifecycle, historical workflow, CAD document or installed plugin changed. The original retained STEP and mesh hashes remain recorded. Next: apply a reviewed engineering basis to the actual handle and bind outputs/checks to its durable workflow; qualify manufacturing independently.

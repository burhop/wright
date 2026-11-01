# Measure local edges in supplied images

`measure_edge_profiles.py` is an Astra-authored, bounded measurement candidate.
It measures original-resolution grayscale gradients along normals to explicit
guide polylines. Guides identify search regions; they are never measured curves.
The general input is an image plus a small configuration, so the method can serve
reverse engineering of objects beyond the Roadster.

Use a new output directory for every execution:

```powershell
python measure_edge_profiles.py --image original.png --config measurement.json --output results/new-attempt
```

The configuration contains `parameters` and an `images` mapping. Each image entry
needs its actual SHA256, `dimensions_wh`, and up to two `features`. Features have
`id`, normalized `guide_uv`, `search_box_uv`, and `search_half_width_px`.
Version1.1 also accepts `gradient_polarity`: `either` (the default), `brightening`
or `darkening`. This is an explicit feature association. Sign follows increasing
distance along the guide normal `[-tangent_y, tangent_x]`; reversing a guide
reverses that normal. No selector is inferred from a component name. Opposite
peaks stay in the report and appear magenta in the overlay.
Normalized coordinates map to integer pixel centers using width minus one and
height minus one. The image hash selects exactly one entry. See the validation
in the script for parameter bounds; unsupported images and existing outputs fail.
Dependencies are the isolated OpenCV4.12 and NumPy2.2 environment. The utility
has no network access, CAD operations, workflow executor or vendor protocols.

The JSON output retains original/configuration/source hashes, versions, raw
sampled intensities, signed gradients, all candidate peaks, refinement residuals,
and threshold/blur sensitivity decisions. The full-resolution overlay distinguishes
provisional stable candidates, tentative/rejected peaks, guides and missing
observations. It does not connect gaps or invent unobserved geometry. Keep these
artifacts in existing Wright result/storage owners when binding a workflow.

The `frame` is descriptive metadata, not directly the typed validator object.
Version1.1 includes the seven explicitly named `ImageCoordinateFrame` fields plus
additional diagnostic metadata. A checked adapter projects those seven fields
and validates their values; it must not pass the extra metadata as a typed frame.
Version1.0 requires mapping its explicit original-pixel-center convention
to [image-coordinate validation](../../docs/workflows/image-coordinate-validation.md)
and bind the exact image before submitting pixel constraints. Do not infer
compatibility merely from field names. No UI change is required: saved reports,
images and findings remain available through existing results/common views.

## Qualification and limits

The Windows pilot executed known horizontal, vertical and slanted smooth-step
controls with maximum residual0.0115 original pixels against a predeclared0.75px
bookkeeping bound. Constant black/gray/white and competing-edge controls return
no stable coordinates; existing output directories are rejected. Two earlier
control configurations exceeded the area/support limits and were retained, then
corrected without changing the method or numerical bound.

Version1.1 exactly preserves version1.0's numerical observations with `either`.
Signed two-edge and reversed-normal controls select the intended boundary with
maximum residual0.00411px under the unchanged0.75px control bound. Two competing
edges of the same polarity remain ambiguous. Opposite edges are retained, not
deleted. Thresholds, blur, stability, guide regions and caps remain unchanged.

These synthetic checks do not establish accuracy on photographs. Applied to six
localized regions in three supplied Roadster images, version1.0 produced115 stable
candidates from238 stations. Every rear-lamp station was ambiguous because both
edges of the bright strip compete. The explicit upper-edge polarity proposals in
version1.1 produced236 stable candidates from the same238 stations: canopy73/73,
nose29/30, front lip50/50, front lamp6/6, rear lamp68/68 and plate border10/11.
Two additional local overhead shoulder regions produced40 candidates. Those
regions are disjoint and do not establish matched width sections or a complete
plan-form outline. Original observations, images and ambiguity remain retained.
Semantic identity, shadows, highlights,
occlusion, camera uncertainty, object configuration and physical scale remain
separate. A stable gradient is not a CAD acceptance result.

Historical version1.0 source SHA256:
`a7b9bfcbbba22424047b5e26e40460fab4fc2eed5fe14253fd75af1ae17e4500`.
Current formatted version1.1 source SHA256:
`82366edaae4ba67609d6da0ee2fac19b76bbedcb28c57d0a709094e5b9aed6e3`.
Actual authoring used isolated `gpt-6-astra` with high reasoning. The source is
retained verbatim in pilot evidence; the executable version1.1 has mechanical
import/format cleanup followed by numerical requalification. Runtime receipts
and private photographs remain in pilot state.
This is local method qualification, not a released provider or a complete
reverse-engineering workflow.

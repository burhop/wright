# Studio desktop-computer brief

## Product research and intended user
The fictional Stillwater Objects studio wants a visually quiet computer for an illustrator's desk. Internal product goals are tactile rounded edges, a small footprint, no top-facing screws, replaceable boards, and a subtle power-light opening. Mood words are river pebble, warm ceramic, soft shadow, and orderly cable exit. These are author-created design goals, not measured consumer-study findings. Target first prototype quantity is two, and target shell material is printed PETG in matte ivory.

Before design, retrieve an official Raspberry Pi 5 mechanical source and record its URL, revision or publication identity, retrieval time, and extracted dimensional table. Verify board outline, mounting-hole centers/diameters, connector envelopes, required insert/plug access, and the selected cooling accessory envelope. If a dimension is absent, label it unresolved; do not silently infer it from the sketch. The reference URL is a discovery pointer, not cached evidence.

## Envelope and construction
Maximum outer envelope: 112 mm long by 86 mm wide by 39 mm high. Use a two-part base/lid with a 2.4 mm nominal shell wall, 2 mm minimum inside corner radius, and four underside fasteners. Keep 8 mm free behind the connector face for plug insertion before bend routing is considered. Assume four non-slip feet lift the underside 5 mm. Manufacturer board mounting dimensions govern the internal posts; supplier insert specifications must be selected and sourced before modeling them. A nominal 85 by 56 mm board rectangle in the sketch is only a planning placeholder, not verified geometry.

## Thermal case
Use an intentionally simplified steady enclosure-air comparison at 25 degrees C ambient, total internal heat 6 W, modeled as one 18 by 18 mm source patch on a board surrogate. The patch center is nominally 45 mm from the board's left edge and 28 mm from its lower edge; this is a synthetic model input, not the actual Pi processor position. Shell conductivity for the study is 0.20 W/(m K), a declared assumed constant. Air model, buoyancy direction, radiation treatment, boundary distances, and solver material properties must be stated explicitly. No fan is installed in the initial comparison.

Variant A uses lower side slots and rear exhaust totaling at least 450 square mm of nominal opening. Variant B uses the same inlet and twelve rounded top slots, nominally 2 by 20 mm before end radii. Preserve an identical board, source, feet, domain extent, and material model across alternatives. Internal target is source-patch maximum below 65 degrees C; this is a product goal, not a Raspberry Pi rating. Use matched CFD domains and record computed fields, convergence, and flow/thermal summaries.

## Business rules and review
The design document and styling/vent compromise require review before CAD. Physical temperature accuracy, plastic performance, EMC, and electrical safety are not validated by output-file tests. No standards certification or sealed-enclosure rating is requested. CAD and solver outputs must be real outputs of the configured tools; missing backends must be reported. External reference lookup is permitted; publication, purchasing, and manufacturing dispatch are not.

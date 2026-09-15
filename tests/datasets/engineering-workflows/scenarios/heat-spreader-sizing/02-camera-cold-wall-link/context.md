# Camera-to-frame thermal link

## Packaging problem and operating basis
Valecrest's fictional tabletop vision fixture has a temperature-controlled frame rail. The team needs an early sizing study for a solid conduction link connecting a camera mounting block to that rail. The 9 W end load represents a synthetic upper operating estimate; no real camera datasheet or measured dissipation is supplied. The camera, optics, contact pads, and frame cooling system are not modeled in this case.

## Geometry and model
X is the conduction direction, from the cold rail at X=0 to the source block at X=80 mm. All candidates have 3 mm constant thickness and widths 30, 45, or 60 mm. Model each as a solid unperforated rectangular plate. Keep within a 64 mm width and 84 mm length envelope. Apply uniform total 9 W to the X=80 full cross-section, set X=0 to 30 degrees C, and insulate every remaining face. There is no contact resistance, radiation, or convection in this first study.

Use the supplied constant k=167 W/(m K) and density=2700 kg/m3, both internal synthetic assumptions for an aluminum-like material. They are not certified properties or a sourced alloy rating. If later material data replace them, preserve a separate revision rather than editing the evidence for the current run. The ideal one-dimensional temperature rise is defined by heat input times L/(k W t); computed solver fields must remain distinct from that analytical baseline.

## Design goals and capabilities
Internal hot-end temperature target is <=56 degrees C. Among compliant alternatives, prefer smaller material volume, then lower maximum temperature if volume ties. A 3 mm profile-cut plate is the proposed process. A future assembly may use screws outside the thermal span, but no hole or fastening feature is specified here. Do not add them by inference, since they alter the modeled cross-section.

## Reporting and company rules
Return a STEP file for each width, solver temperature data, a heat-balance record, and a sizing decision identifying each candidate. Describe boundary names, unit conversion, chosen solver materials, and coarse/fine mesh sequence. Field-derived values, analytical comparison, and unresolved product-level assumptions must be separated. Current integration scoring checks that outputs exist; it does not establish their numerical correctness. Temperature claims apply only to the synthetic conduction link and cannot establish chip junction temperature, thermal-contact performance, camera calibration, safe touch temperature, or standards compliance. No hardware operation or supplier submission is authorized.

# Greenhouse gateway design brief

## Field context and research
Alderbend's fictional test bay records humidity and soil-sensor data using a Raspberry Pi 5. It is mounted beneath an indoor bench canopy, beyond the assumed splash reach, with monthly service. No actual field measurements are supplied. This is a concept for protected installation, not environmental certification.

Retrieve official Pi 5 mechanical geometry and connector dimensions before writing the design document. Record citations for extracted dimensions. Ask the tool to separate verified manufacturer facts from the nominal board silhouette and customer assumptions. The nominal internal planning board is 85 by 56 mm, but the retrieved drawing must govern. Any proposed cable gland, filter medium, or insert must have source dimensions recorded if used; do not invent a supplier rating.

## Mounting and service requirements
Maximum enclosure body is 130 by 95 by 60 mm. Two external mounting ears attach to a dry shelf bracket at 145 mm centers along the long axis using 4.5 mm clearance holes. Ear centers lie in the base plane; ears must remain outside the lid-removal path. Provide a lid removable with one common hex-driver size and captive screw design only if a sourced part can be accommodated. Nominal printed PETG wall is 2.8 mm. Keep a rectangular 30 by 18 mm cable-exit region below the connector side and 35 mm free outside it for a drip loop. This is clearance intent, not a waterproof gland specification. Permit status-light viewing without opening the lid.

## Thermal and flow inputs
Analyze a simplified steady 8 W load at 35 degrees C ambient with gravity toward the enclosure base. Represent 6 W on a board heat patch and 2 W on a nearby 25 by 20 mm sensor-interface block separated by 12 mm of air. Their nominal positions appear in thermal-loads.csv and are synthetic modeling assumptions. Treat walls with an assumed 0.20 W/(m K) conductivity. State the air property model and radiation assumption. Compare a lower side inlet plus downward-louver exhaust against the same inlet with a 20 mm tall top chimney; both must fit the height envelope. Target component-patch maximum is 70 degrees C for this project. It is not a supplier's operating limit.

Treat insect screen as a documented optional resistance assumption only if the solver supports it. Otherwise run a clear-opening comparison and mark screen pressure loss unresolved. The results must not assert ingress protection, contamination exclusion, UV durability, or moisture safety.

## Organization policy
Retain a reviewable design basis, measurable CAD, matching fluid domain per variant, and CFD comparison from actual computed fields. Design choices and assumption gaps stay visible. Test automation may approve local design reviews; physical manufacture, networked device commands, and supplier transactions are excluded. Initial acceptance checks the existence of outputs, not thermal correctness.

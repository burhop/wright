# Robot arm STL kit — revision 7

This package contains 18 unique STL files for 28 printed pieces of the digital
tabletop robot-arm assembly. Files use millimetres, are individually oriented
according to the saved native print metadata, and sit at XYZ zero. The STEP
assembly and original component coordinates remain separate.

Source: SteveCAD document `167ef21f-6679-4e4d-8917-14dc067893d6`, revision 7,
build `780f3196-07b2-4590-b102-1cdd9a73b6cf`.

Use `printed-bom.csv` for the print quantities and orientations. Use
`complete-modeled-bom.csv` for all 110 modeled printed/purchased instances.
`manifest.json` identifies the source STEP, transforms, bounds and hashes;
`verification.json` records the independent checks. Each unique STL is closed,
has one connected solid and positive winding, fits the assumed 220 × 220 × 250 mm
build volume, and preserves its STEP-derived geometry within the declared
tessellation and transform checks. Maximum local native-envelope discrepancy is
0.010568 mm. These checks establish digital file integrity.

Printing assumptions are PETG, a 0.4 mm nozzle, nominal structural walls of at
least 3 mm and a 1.2 mm screening threshold. The native whole-design FDM screen
used +Z and did not establish every declared orientation. Support generation,
bridge feasibility, surface finish, slicer settings and physical fit remain
unverified. Through bores and servo cavities may need removable supports and
calibrated cleanup. Inspect slicer previews and make fit coupons before producing
the complete set.

The user supplied CM5 and the official CM5 IO Board. MG996R ×3 and MG90S ×2 are
provisional body references. Horn/spline interfaces, mounting ears and mechanical
drive transmissions require actual hardware measurements. Strength, payload,
stability, motor sizing and powered operation remain unverified. The visible
servo/board models are explicitly simplified reference envelopes.

See `assembly.md` for the proposed sequence, fastener stacks and unresolved
interfaces. This package records digital design/export verification; physical
printing, assembly and operating tests have not been performed. Marketing files
remain unpublished and no human acceptance is recorded.

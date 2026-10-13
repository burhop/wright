# SteveCAD visibility and drawn-instance metadata defect

Status: reproduced; report prepared, not submitted. No report ID exists yet.

Document: 17b6718f-d0e5-4a13-bcf7-48f3d963b7e8, revision 1.
Full build: 627de50c-cdf4-40f5-ac77-7bccbd4e8b9d, succeeded, two solids and no feature/design errors.
Qualification STEVE CAD 4.0.10; native build CadQuery 2.8.0. Hosted deployment is not pinned. Current api_reference("inspect_model") is included.

## Minimal reproduction

Use main.py and components/marker.py in this packet. They create one 10 x 20 x 30 mm Component with two instances: first_marker at X=0 and second_marker at X=100. Save as a design and generate that exact revision.

Call inspect_model(document_id=..., view="isometric", checks=[], show=["second_marker"]). Expected drawn.instances=["second_marker"], extent=[100,0,0,110,20,30] mm. Observed extent is correct but drawn.instances=["first_marker"].

Control: show=["first_marker"]. Expected extent=[0,0,0,10,20,30]. Observed extent=[0,0,0,110,20,30], which includes both instances; returned labels still contain only first_marker. The corresponding native images are included.

The live tool contract says show selects instances and summary.drawn identifies what is drawn. Original native JSON text and structuredContent agree on the wrong labels; the source/build records have correct distinct names and placements. Wright's evidence exporter did not rename instances. This is not a claim about physical fit, nor a claim that the arm's separate collision failures are provider bugs.

## Impact and report handling

A focused image may carry the wrong instance identity or unintentionally include repeated instances. For engineering review, retain exact build/revision, drawn extents and native source placements; do not infer a verified selected instance from this label alone.

Submit once using signed-in Feedback > Report a bug. Inspect What's sent with your report. Attach this small owned source/reproduction packet rather than the full robot or credentials. Record the receipt ID/status; Saved / Waiting to send is queued acceptance and must not be resubmitted. No supported MCP report operation was discovered, and no signed-in Studio browser automation capability was available in this session. The prepared packet does not count as a submitted report.

# Exact handle construction and measurement

Scope: fresh digital geometry qualification, not engineering or physical
acceptance. The original dimensions, feature requirements and validator remain.

The native `d333528aaea64d02b2204826e3922541` attempt stopped on two
degenerate BMesh faces before source export. Declared 1e-6 mm numerical cleanup
now removes degenerate edges after triangulation; both construction and repair
also reject degenerate exported loop triangles. No voxel remesh or threshold
relaxation was introduced.

The next run, `1b2f6e08667146ad85abe0686346fd36`, passed topology but stopped
at the original mounting-bore gate. Its retained native object was exported
separately as `failed-diagnostic.stl`, never as an expected successful output.
The diagnostic mesh SHA-256 is
`a4c442a9b5894e42386caf8a4cbeca703883274583a44845d435811387d1d96b`.
Independent all-triangle ray intersections and exact triangle/plane sections
agree for every one of the 128 directions per bore (maximum discrepancy
4.9e-15 mm). Both bore centers and diameters meet the existing numerical bounds.
The original native ray observation missed a surface; no provider bug report or
broader Blender defect is inferred.

The revised operation intersects every current loop triangle with the exact
Z=2.5 mm plane in Python double precision. It deduplicates section edges, joins
endpoints at a declared 1e-9 mm representation bound, rejects open or branching
contours, includes shared ray endpoints, and retains all 128 original directions.
It additionally measures the complete inner contour's minimum point-to-segment
radius and maximum vertex radius. These continuous bounds use the same original
diameter limits and catch intrusions between the sample directions. The original
17 axial observations and all other feature/topology gates remain.

Fourteen focused pure/static controls pass, including translated 96 mm seams,
shared vertices, wrong size/offset, open/branching contours and an inward notch
between all original ray directions. Both operation assets pass the pinned
provider's safe-mode AST policy. The failed mesh also passes the revised
measurement independently; that does not turn a failed run into a passed run.

Fresh accepted revision 5, digest
`9cd2acc8b36df3abea002a9e62b3171a8df0fc1b5c327eb35bdd20e047caeaef`,
starts run `3735dcf5678847219bc88ca2c80cedc8`. Construction has produced a
source STL and repair has produced a distinct repaired STL. Native preview,
exact root/round inspection and the declared geometry review remain pending.
No slice has been authorized. Midplane and sparse axial checks alone do not
establish full-volume bore clearance, washer fit, self-intersection freedom,
all required radii or physical strength.

Retained attempt reports, exact records, diagnostic export receipts, STL,
independent observations and section plot:
`artifacts/first-contact/084/native-handle-geometry-attempt-003/` and
`artifacts/first-contact/084/native-handle-geometry-attempt-004/`.

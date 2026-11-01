"""Independent standard-library parsing of retained ASCII Gmsh volume mesh."""

import hashlib
import json
import math
import sys
from pathlib import Path

root = Path(sys.argv[1])
lines = (root / "cad-mesh.msh").read_text().splitlines()
i = lines.index("$Nodes")
n = int(lines[i + 1])
nodes = {}
for row in lines[i + 2 : i + 2 + n]:
    values = row.split()
    key = int(values[0])
    xyz = tuple(map(float, values[1:]))
    assert key not in nodes and len(xyz) == 3 and all(map(math.isfinite, xyz))
    nodes[key] = xyz
i = lines.index("$Elements")
count = int(lines[i + 1])
volumes = []
seen = set()
for row in lines[i + 2 : i + 2 + count]:
    v = list(map(int, row.split()))
    assert v[0] not in seen
    seen.add(v[0])
    if v[1] != 4:
        continue
    ids = v[3 + v[2] :]
    assert len(ids) == 4 and len(set(ids)) == 4
    a, b, c, d = [nodes[k] for k in ids]
    u = [b[j] - a[j] for j in range(3)]
    v = [c[j] - a[j] for j in range(3)]
    w = [d[j] - a[j] for j in range(3)]
    volume = (
        abs(
            u[0] * (v[1] * w[2] - v[2] * w[1])
            - u[1] * (v[0] * w[2] - v[2] * w[0])
            + u[2] * (v[0] * w[1] - v[1] * w[0])
        )
        / 6
    )
    assert volume > 1e-12
    volumes.append(volume)
assert volumes
reported = json.loads((root / "mesh-check.json").read_text())
assert n == reported["nodes"] and len(volumes) == reported["tetrahedra"]
assert math.isclose(
    sum(volumes), reported["mesh_volume_coordinate_units_cubed"], rel_tol=1e-12
)
for name, digest in reported["files"].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
source = Path(
    "artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/bracket-native-001/handoff/design.step"
)
assert hashlib.sha256(source.read_bytes()).hexdigest() == reported["source_sha256"]
result = {
    "status": "PASS",
    "boundary": "independent ASCII mesh connectivity, finite coordinates, positive tetra volumes, recorded output digests and retained STEP identity; not CAD compliance or strength",
    "nodes": n,
    "tetrahedra": len(volumes),
    "volume_coordinate_units_cubed": sum(volumes),
    "source_sha256": reported["source_sha256"],
}
(root / "independent-check.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result))

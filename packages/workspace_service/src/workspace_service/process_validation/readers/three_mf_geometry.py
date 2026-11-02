"""Bounded passive STL/3MF Core geometry correspondence, independent of slicers.

Row-vector matrices follow 3MF Core. This module can also be frozen as an authored
inspection asset for an existing external Python capability; it never executes
package contents or invokes an application.
"""

from collections import Counter, deque
import io
from itertools import product
import math
from pathlib import PurePosixPath
import struct
import xml.etree.ElementTree as ET
from zipfile import ZipFile

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PRODUCTION = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
MAX_TRIANGLES = 80000
MAX_BYTES = 64 * 1024 * 1024
MAX_MATCH_CANDIDATES = 250000
MAX_MATCH_WORK = 1000000


def identity():
    return [[float(i == j) for j in range(4)] for i in range(4)]


def multiply(a, b):
    result = [
        [sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)
    ]
    if not all(math.isfinite(v) for row in result for v in row):
        raise ValueError("Nonfinite composed 3MF matrix")
    return result


def transform(points, matrix):
    result = [
        tuple(sum((*point, 1)[k] * matrix[k][i] for k in range(4)) for i in range(3))
        for point in points
    ]
    if not all(math.isfinite(v) for p in result for v in p):
        raise ValueError("Nonfinite transformed 3MF geometry")
    return result


def matrix(raw):
    result = identity()
    if raw is not None:
        values = [float(v) for v in raw.split()]
        if len(values) != 12 or not all(math.isfinite(v) for v in values):
            raise ValueError("Invalid 3MF affine matrix")
        for i in range(4):
            result[i][:3] = values[3 * i : 3 * i + 3]
    return result


def stl_triangles(content, checkpoint=lambda **_: None):
    if len(content) < 84:
        raise ValueError("A complete binary STL is required")
    count = struct.unpack_from("<I", content, 80)[0]
    if not 4 <= count <= MAX_TRIANGLES or len(content) != 84 + 50 * count:
        raise ValueError("Binary STL count/size exceeds the declared bound")
    checkpoint(entities=count)
    triangles = []
    for record in struct.iter_unpack("<12fH", content[84:]):
        if not all(math.isfinite(v) for v in record[:12]):
            raise ValueError("Nonfinite STL geometry")
        triangles.append(
            tuple(tuple(record[offset : offset + 3]) for offset in (3, 6, 9))
        )
    return triangles


def bounds(triangles):
    return [
        [fn(p[i] for t in triangles for p in t) for i in range(3)] for fn in (min, max)
    ]


def expected_transform(triangles, rotation, center):
    if (
        not isinstance(rotation, list)
        or len(rotation) != 3
        or any(not isinstance(row, list) or len(row) != 3 for row in rotation)
        or not isinstance(center, list)
        or len(center) != 2
        or not all(
            type(x) in (int, float) and math.isfinite(x)
            for row in rotation
            for x in row
        )
        or not all(type(x) in (int, float) and math.isfinite(x) for x in center)
    ):
        raise ValueError("Declare a finite rotation and build center")
    for i in range(3):
        for j in range(3):
            if (
                abs(sum(rotation[i][k] * rotation[j][k] for k in range(3)) - (i == j))
                > 1e-12
            ):
                raise ValueError("The build transform must be a rigid rotation")
    a, b, c = rotation
    determinant = (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )
    if abs(determinant - 1) > 1e-12:
        raise ValueError("Mirrored build transforms are forbidden")
    result = identity()
    for i in range(3):
        result[i][:3] = rotation[i]
    box = bounds([transform(t, result) for t in triangles])
    result[3][:3] = [
        center[0] - (box[0][0] + box[1][0]) / 2,
        center[1] - (box[0][1] + box[1][1]) / 2,
        -box[0][2],
    ]
    return result


def archive_members(content):
    if len(content) > MAX_BYTES:
        raise ValueError("3MF compressed input exceeds its bound")
    with ZipFile(io.BytesIO(content)) as archive:
        entries = archive.infolist()
        if not 1 <= len(entries) <= 256:
            raise ValueError("Unsupported 3MF member count")
        seen, result, total = set(), {}, 0
        for entry in entries:
            name = entry.filename
            if (
                name in seen
                or not name
                or "\\" in name
                or name.startswith("/")
                or any(p in ("..", ".") for p in name.split("/"))
                or ":" in name
                or entry.flag_bits & 1
            ):
                raise ValueError("Unsafe or duplicate 3MF member")
            seen.add(name)
            total += entry.file_size
            if total > MAX_BYTES or (
                entry.file_size
                and (
                    not entry.compress_size
                    or entry.file_size / entry.compress_size > 200
                )
            ):
                raise ValueError("3MF expansion exceeds its bound")
            result[name] = archive.read(entry)
        return result


def read_package(content, checkpoint=lambda **_: None):
    members = archive_members(content)
    documents = {}
    total_entities = 0

    def document(name):
        nonlocal total_entities
        if name not in documents:
            raw = members[name]
            if b"\0" in raw or "<!" in raw.decode("utf-8-sig"):
                raise ValueError("3MF declarations/entities are not supported")
            try:
                parser = ET.iterparse(io.BytesIO(raw), events=("start",))
                root = None
                for _, node in parser:
                    if root is None:
                        root = node
                    total_entities += 1
                    if total_entities > 400000:
                        raise ValueError("3MF XML entity bound exceeded")
                    if total_entities % 1024 == 0:
                        checkpoint(entities=total_entities)
            except ET.ParseError as exc:
                raise ValueError("Invalid 3MF XML") from exc
            if (
                root.tag != f"{{{CORE}}}model"
                or root.get("unit", "millimeter") != "millimeter"
            ):
                raise ValueError("Require millimetre 3MF Core models")
            checkpoint(entities=total_entities)
            objects = root.findall(f"{{{CORE}}}resources/{{{CORE}}}object")
            ids = [node.get("id") for node in objects]
            if None in ids or len(ids) != len(set(ids)):
                raise ValueError("Ambiguous 3MF object identity")
            documents[name] = root, dict(zip(ids, objects))
        return documents[name]

    triangles, records = [], []

    def visit(name, object_id, parent, stack):
        key = (name, object_id)
        if len(stack) >= 8 or key in stack:
            raise ValueError("3MF component recursion/cycle is unsupported")
        _, objects = document(name)
        obj = objects[object_id]
        mesh = obj.find(f"{{{CORE}}}mesh")
        components = obj.find(f"{{{CORE}}}components")
        if (mesh is None) == (components is None):
            raise ValueError("Require one mesh or component list per 3MF object")
        if mesh is not None:
            vertices = [
                tuple(float(v.attrib[k]) for k in ("x", "y", "z"))
                for v in mesh.findall(f"{{{CORE}}}vertices/{{{CORE}}}vertex")
            ]
            faces = [
                tuple(int(t.attrib[k]) for k in ("v1", "v2", "v3"))
                for t in mesh.findall(f"{{{CORE}}}triangles/{{{CORE}}}triangle")
            ]
            if (
                not faces
                or len(triangles) + len(faces) > MAX_TRIANGLES
                or len(vertices) > 3 * MAX_TRIANGLES
            ):
                raise ValueError("3MF triangle/vertex bound exceeded")
            if not all(math.isfinite(v) for p in vertices for v in p):
                raise ValueError("Nonfinite 3MF geometry")
            if any(i < 0 or i >= len(vertices) for f in faces for i in f):
                raise ValueError("3MF face references an invalid vertex")
            original = [tuple(vertices[i] for i in face) for face in faces]
            transformed = [tuple(transform(t, parent)) for t in original]
            triangles.extend(transformed)
            records.append(
                dict(
                    part=name,
                    object_id=object_id,
                    matrix=parent,
                    model_triangles=original,
                )
            )
        else:
            children = components.findall(f"{{{CORE}}}component")
            if not children:
                raise ValueError("Empty 3MF component list")
            for child in children:
                reference = child.get(f"{{{PRODUCTION}}}path")
                target = name if reference is None else reference.lstrip("/")
                if (
                    target not in members
                    or ".." in PurePosixPath(target).parts
                    or "\\" in target
                    or ":" in target
                ):
                    raise ValueError("Invalid 3MF component reference")
                visit(
                    target,
                    child.attrib["objectid"],
                    multiply(matrix(child.get("transform")), parent),
                    (*stack, key),
                )
        checkpoint(entities=total_entities + len(triangles))

    main = "3D/3dmodel.model"
    root, _ = document(main)
    build = root.findall(f"{{{CORE}}}build/{{{CORE}}}item")
    if len(build) != 1 or build[0].get("printable", "1") != "1":
        raise ValueError(
            "This correspondence requires exactly one printable build instance"
        )
    item = build[0]
    visit(main, item.attrib["objectid"], matrix(item.get("transform")), ())
    return triangles, records


def match_error(expected, actual, tolerance, checkpoint=lambda **_: None):
    if len(expected) != len(actual):
        raise ValueError("3MF triangle count differs from source")
    if (
        not expected
        or len(expected) > MAX_TRIANGLES
        or not all(
            math.isfinite(v)
            for mesh in (expected, actual)
            for t in mesh
            for p in t
            for v in p
        )
    ):
        raise ValueError("Require bounded finite nonempty geometry")
    if type(tolerance) not in (int, float) or not 0 <= tolerance <= 1e-4:
        raise ValueError("Declare a bounded geometry correspondence tolerance")
    checkpoint(entities=len(expected) + len(actual))

    def canonical(triangle):
        triangle = tuple(tuple(p) for p in triangle)
        return min(triangle[i:] + triangle[:i] for i in range(3))

    def normal(triangle):
        p, q, r = triangle
        u, v = [q[i] - p[i] for i in range(3)], [r[i] - p[i] for i in range(3)]
        vector = (
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        )
        length = math.hypot(*vector)
        if not math.isfinite(length) or length <= 0:
            raise ValueError("Degenerate or nonfinite oriented triangle")
        return tuple(value / length for value in vector)

    counts = [Counter(canonical(t) for t in mesh) for mesh in (expected, actual)]
    groups = [sorted(counter) for counter in counts]
    normals = []
    for mesh in groups:
        values = []
        for index, triangle in enumerate(mesh):
            if index % 1024 == 0:
                checkpoint()
            values.append(normal(triangle))
        normals.append(values)
    if counts[0] == counts[1]:
        return 0.0
    if tolerance == 0:
        raise ValueError("3MF oriented triangles do not match the original geometry")

    # A matching triangle's componentwise minima differ by at most tolerance.
    # Neighboring cells only select candidates; full cyclic coordinates decide.
    # Exact rational cell division avoids floating quantization boundary ordering.
    width_n, width_d = (2.0 * tolerance).as_integer_ratio()

    def cell(triangle):
        result = []
        for axis in range(3):
            numerator, denominator = float(
                min(p[axis] for p in triangle)
            ).as_integer_ratio()
            result.append((numerator * width_d) // (denominator * width_n))
        return tuple(result)

    buckets = {}
    for index, triangle in enumerate(groups[0]):
        buckets.setdefault(cell(triangle), []).append(index)
    work = 0

    def account():
        nonlocal work
        work += 1
        if work > MAX_MATCH_WORK:
            raise ValueError("3MF correspondence search exceeds its work bound")
        if work % 1024 == 0:
            checkpoint()

    candidates = []
    candidate_count = 0
    winding_conflict = False
    for right_index, triangle in enumerate(groups[1]):
        location = cell(triangle)
        selected = {}
        for offset in product((-1, 0, 1), repeat=3):
            key = tuple(location[i] + offset[i] for i in range(3))
            for left_index in buckets.get(key, ()):
                account()
                left = groups[0][left_index]
                error = min(
                    max(
                        abs(x - y)
                        for p, q in zip(left, triangle[start:] + triangle[:start])
                        for x, y in zip(p, q)
                    )
                    for start in range(3)
                )
                if not math.isfinite(error) or error > tolerance:
                    continue
                alignment = sum(
                    x * y
                    for x, y in zip(normals[0][left_index], normals[1][right_index])
                )
                if not math.isfinite(alignment) or alignment <= 0:
                    winding_conflict = True
                    continue
                selected[left_index] = error
                candidate_count += 1
                if candidate_count > MAX_MATCH_CANDIDATES:
                    raise ValueError("3MF correspondence candidates exceed their bound")
        candidates.append(dict(sorted(selected.items())))

    # Capacitated bipartite matching preserves duplicate multiplicity without
    # expanding identical triangles into a quadratic candidate graph. Augmenting
    # paths can move an earlier assignment when a later triangle has fewer choices.
    available = [counts[0][triangle] for triangle in groups[0]]
    assigned = [{} for _ in groups[1]]
    owners = [{} for _ in groups[0]]
    for root, triangle in enumerate(groups[1]):
        remaining = counts[1][triangle]
        while remaining:
            queue = deque([root])
            parent_right = {root: None}
            parent_left = {}
            finish = None
            while queue and finish is None:
                right = queue.popleft()
                for left in candidates[right]:
                    account()
                    if left in parent_left:
                        continue
                    parent_left[left] = right
                    if available[left]:
                        finish = left
                        break
                    for previous in sorted(owners[left]):
                        account()
                        if previous not in parent_right:
                            parent_right[previous] = left
                            queue.append(previous)
            if finish is None:
                if winding_conflict:
                    raise ValueError("3MF triangle winding differs from source")
                raise ValueError(
                    "3MF oriented triangles do not match the original geometry"
                )
            amount = min(remaining, available[finish])
            left = finish
            while parent_left[left] != root:
                right = parent_left[left]
                previous = parent_right[right]
                amount = min(amount, assigned[right][previous])
                left = previous
            left = finish
            while True:
                right = parent_left[left]
                assigned[right][left] = assigned[right].get(left, 0) + amount
                owners[left][right] = owners[left].get(right, 0) + amount
                if right == root:
                    break
                previous = parent_right[right]
                assigned[right][previous] -= amount
                owners[previous][right] -= amount
                if assigned[right][previous] == 0:
                    del assigned[right][previous]
                    del owners[previous][right]
                left = previous
            remaining -= amount
            available[finish] -= amount
    if any(available):
        raise ValueError("3MF triangle multiplicity differs from source")
    checkpoint()
    return max(
        candidates[right][left]
        for right, matches in enumerate(assigned)
        for left in matches
    )


def correspondence(
    source,
    prepared,
    package,
    rotation,
    center,
    tolerance=1e-4,
    checkpoint=lambda **_: None,
):
    if type(tolerance) not in (int, float) or not 0 < tolerance <= 1e-4:
        raise ValueError("Declare a bounded geometry correspondence tolerance")
    original = stl_triangles(source, checkpoint)
    expected = expected_transform(original, rotation, center)
    prepared_world, prepared_records = read_package(prepared, checkpoint)
    actual_world, actual_records = read_package(package, checkpoint)
    if len(prepared_records) != 1:
        raise ValueError("Prepared 3MF must retain one original model mesh")
    raw_error = match_error(
        original, prepared_records[0]["model_triangles"], 0, checkpoint
    )
    matrix_error = max(
        abs(x - y)
        for a, b in zip(expected, prepared_records[0]["matrix"])
        for x, y in zip(a, b)
    )
    if matrix_error > 1e-12:
        raise ValueError("Prepared build transform differs from declared selection")
    expected_world = [tuple(transform(t, expected)) for t in original]
    input_error = match_error(expected_world, prepared_world, tolerance, checkpoint)
    output_error = match_error(expected_world, actual_world, tolerance, checkpoint)
    inverse = identity()
    for i in range(3):
        for j in range(3):
            inverse[i][j] = expected[j][i]
    inverse[3][:3] = [
        -sum(expected[3][k] * inverse[k][j] for k in range(3)) for j in range(3)
    ]
    inverse_error = match_error(
        original,
        [tuple(transform(t, inverse)) for t in actual_world],
        tolerance,
        checkpoint,
    )
    return dict(
        triangle_count=len(original),
        source_model_bounds_mm=bounds(original),
        build_bounds_mm=bounds(actual_world),
        build_matrix=expected,
        inverse_matrix=inverse,
        prepared_model_error_mm=raw_error,
        prepared_world_error_mm=input_error,
        native_world_error_mm=output_error,
        inverse_model_error_mm=inverse_error,
        native_component_matrices=[
            dict(part=r["part"], object_id=r["object_id"], matrix=r["matrix"])
            for r in actual_records
        ],
    )

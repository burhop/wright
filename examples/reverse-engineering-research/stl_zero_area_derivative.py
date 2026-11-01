"""Create a separate STL dropping only explicitly bounded exact-zero records.

Positive-area records remain byte-for-byte identical. This changes topology and
does not establish a valid or accepted mesh; independently remeasure the result.
"""

from pathlib import Path
import hashlib


def derive(
    source: Path, expected_sha256: str, output: Path, maximum_removed: int
) -> dict:
    import numpy as np

    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Input artifact changed.")
    if output.exists():
        raise FileExistsError("Preserve existing outputs.")
    if maximum_removed < 0:
        raise ValueError("Declare a nonnegative removal bound.")
    count = int.from_bytes(raw[80:84], "little")
    if len(raw) != 84 + count * 50:
        raise ValueError("Expected complete binary STL records.")
    dtype = np.dtype(
        [("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")]
    )
    records = np.frombuffer(raw, dtype=dtype, count=count, offset=84)
    v = records["vertices"].astype(np.float64)
    if not np.isfinite(v).all():
        raise ValueError("Non-finite coordinates.")
    cross = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    zero = np.all(cross == 0, axis=1)
    removed = int(zero.sum())
    if removed > maximum_removed:
        raise ValueError("Exact-zero removal exceeds the declared bound.")
    retained = records[~zero].tobytes()
    output.write_bytes(raw[:80] + int(count - removed).to_bytes(4, "little") + retained)
    assert output.read_bytes()[84:] == retained
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_sha256
    return dict(
        schema="wright.exact_zero_STL_derivative/1",
        source=str(source),
        source_sha256=expected_sha256,
        output=str(output),
        output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        input_triangles=count,
        removed_exact_zero_triangles=removed,
        maximum_removed=maximum_removed,
        retained_triangles=count - removed,
        positive_area_records_byte_identical=True,
        positive_area_triangles_removed=0,
        component_selection_performed=False,
        scope="A separate topology-changing derivative; exact mesh checks remain required.",
    )

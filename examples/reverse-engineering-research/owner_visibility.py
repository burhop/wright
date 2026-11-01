"""Opaque owner diagnostics for existing qualified rasterizer outputs.

No rasterization, camera fitting, geometry changes, I/O or mutable state.
Software contract choices (assumptions, not engineering requirements):
* layers is a nonempty list/tuple; H and W are positive.
* depth/shade are plain numpy ndarrays with native float64/uint8 dtype.
* color is a list, tuple or plain ndarray of three non-boolean integers.
* return (owner, nearest_depth, rgb, report); RGB uses numpy.rint.
* counts are pixels, not faces, area, physical fidelity or feature ownership.

Depth and epsilon use the input rasterizer's nominal mm convention; no
physical scale is verified or inferred here. Epsilon is numerical near-tie
classification only, never a physical or engineering tolerance.
"""

import numpy as np


def compose(layers, depth_epsilon_mm=0.0):
    """Return owner(int32), nearest_depth(float64), rgb(uint8), report(dict).

    At each foreground pixel let m be the smallest finite positive depth.
    Candidates are precisely layers with finite depth d and d - m <= epsilon.
    One candidate owns the pixel; two or more produce owner -2. Background
    is owner -1, NaN depth and black. Ties are magenta regardless of shade.
    Near-tie membership is relative to m, not pairwise/transitive clustering.

    A layer's projected pixels partition into uniquely_visible, nearest_tied
    and occluded. nearest_tied counts only that layer's participation in a
    nearest tie; layers farther than epsilon are occluded even at tie pixels.
    Global tie counts count pixels once, not participating layers.

    Owner indices follow input order; report layers retain IDs and indices.
    Inputs are never modified. TypeError denotes unsupported types/dtypes;
    ValueError denotes invalid values, missing fields or incompatible shapes.
    """
    if isinstance(depth_epsilon_mm, (bool, np.bool_)) or not isinstance(
        depth_epsilon_mm, (int, float, np.integer, np.floating)
    ):
        raise TypeError("depth_epsilon_mm must be a real numeric scalar")
    try:
        epsilon = float(depth_epsilon_mm)
    except (OverflowError, ValueError) as exc:
        raise ValueError("epsilon must be representable as finite float64") from exc
    if not np.isfinite(epsilon) or epsilon < 0.0:
        raise ValueError("epsilon must be finite and nonnegative")
    if not isinstance(layers, (list, tuple)):
        raise TypeError("layers must be a list or tuple")
    if not layers:
        raise ValueError("at least one layer is needed to establish shape")
    if len(layers) > int(np.iinfo(np.int32).max):
        raise ValueError("too many layers for int32 owner indices")

    shape = None
    seen = set()
    checked = []
    for layer in layers:
        if not isinstance(layer, dict):
            raise TypeError("each layer must be a dict")
        if not all(key in layer for key in ("id", "depth", "shade", "color_rgb")):
            raise ValueError("layer requires id, depth, shade and color_rgb")
        identifier = layer["id"]
        if not isinstance(identifier, str):
            raise TypeError("layer id must be a string")
        if not identifier:
            raise ValueError("layer id must be nonempty")
        if identifier in seen:
            raise ValueError("duplicate layer id: " + identifier)
        seen.add(identifier)
        depth, shade = layer["depth"], layer["shade"]
        if type(depth) is not np.ndarray or type(shade) is not np.ndarray:
            raise TypeError("depth and shade must be plain numpy ndarrays")
        if depth.dtype != np.dtype(np.float64):
            raise TypeError("depth dtype must be native float64")
        if shade.dtype != np.dtype(np.uint8):
            raise TypeError("shade dtype must be uint8")
        if depth.ndim != 2 or shade.ndim != 2:
            raise ValueError("depth and shade must be HxW")
        if min(depth.shape) <= 0 or shade.shape != depth.shape:
            raise ValueError("depth/shade require equal positive HxW shapes")
        if shape is None:
            shape = depth.shape
        elif depth.shape != shape:
            raise ValueError("all layers must have the same HxW shape")
        if np.any(np.isinf(depth)) or np.any(depth <= 0.0):
            raise ValueError("depth must be finite positive or NaN background")
        color = layer["color_rgb"]
        if not isinstance(color, (list, tuple)) and type(color) is not np.ndarray:
            raise TypeError("color_rgb must be a list, tuple or plain ndarray")
        if type(color) is np.ndarray and color.ndim != 1:
            raise ValueError("color_rgb must have shape (3,)")
        if len(color) != 3:
            raise ValueError("color_rgb must contain exactly three channels")
        channels = []
        for channel in color:
            if isinstance(channel, (bool, np.bool_)) or not isinstance(
                channel, (int, np.integer)
            ):
                raise TypeError("color channels must be non-boolean integers")
            channel = int(channel)
            if channel < 0 or channel > 255:
                raise ValueError("color channels must be in 0..255")
            channels.append(channel)
        checked.append((identifier, depth, shade, np.array(channels, dtype=np.float64)))

    # fmin ignores one NaN and leaves two NaNs as NaN, without an all-NaN
    # reduction warning. No infinities or inf-inf subtraction are introduced.
    nearest_depth = np.full(shape, np.nan, dtype=np.float64)
    for _, depth, _, _ in checked:
        np.fmin(nearest_depth, depth, out=nearest_depth)
    foreground = np.isfinite(nearest_depth)
    candidate_count = np.zeros(shape, dtype=np.int64)
    owner = np.full(shape, -1, dtype=np.int32)

    for index, (_, depth, _, _) in enumerate(checked):
        valid = np.isfinite(depth)
        candidate = np.zeros(shape, dtype=bool)
        # Every valid input pixel has a finite nearest depth. Subtract only
        # those finite values, with the global minimum already fixed.
        candidate[valid] = (depth[valid] - nearest_depth[valid]) <= epsilon
        first = candidate & (candidate_count == 0)
        owner[first] = index
        candidate_count[candidate] += 1
    ties = candidate_count > 1
    owner[ties] = -2

    rgb = np.zeros(shape + (3,), dtype=np.uint8)
    rgb[ties] = (255, 0, 255)
    records = []
    for index, (identifier, depth, shade, color) in enumerate(checked):
        valid = np.isfinite(depth)
        candidate = np.zeros(shape, dtype=bool)
        candidate[valid] = (depth[valid] - nearest_depth[valid]) <= epsilon
        unique = owner == index
        projected = int(np.count_nonzero(valid))
        visible = int(np.count_nonzero(unique))
        tied = int(np.count_nonzero(candidate & ties))
        rgb[unique] = np.rint(
            (shade[unique].astype(np.float64)[:, None] / 255.0) * color
        ).astype(np.uint8)
        records.append(
            {
                "id": identifier,
                "index": index,
                "projected": projected,
                "uniquely_visible": visible,
                "occluded": projected - visible - tied,
                "nearest_tied": tied,
            }
        )

    report = {
        "shape": [int(shape[0]), int(shape[1])],
        "array_shapes": {
            "depth": [int(shape[0]), int(shape[1])],
            "shade": [int(shape[0]), int(shape[1])],
            "owner": [int(shape[0]), int(shape[1])],
            "nearest_depth": [int(shape[0]), int(shape[1])],
            "rgb": [int(shape[0]), int(shape[1]), 3],
        },
        "depth_epsilon_mm": epsilon,
        "epsilon_role": "Numerical near-tie classification, not physical tolerance.",
        "count_units": "pixels",
        "layers": records,
        "global": {
            "foreground": int(np.count_nonzero(foreground)),
            "ties": int(np.count_nonzero(ties)),
            "uniquely_visible": int(np.count_nonzero(owner >= 0)),
            "background": int(np.count_nonzero(~foreground)),
        },
        "definitions": {
            "projected": "Finite positive input depth pixels, before inter-layer composition.",
            "uniquely_visible": "Pixels owned uniquely by this layer.",
            "nearest_tied": "Pixels where this layer is within epsilon of the minimum and at least two layers qualify.",
            "occluded": "Projected pixels outside the nearest candidate set.",
            "tie_rule": "d - minimum <= epsilon, inclusive; no transitive chaining.",
            "owner_codes": "-1 background; -2 ambiguous nearest tie; otherwise input layer index.",
            "rgb_rounding": "numpy.rint nearest integer; halfway cases to even.",
            "coordinates": "Unchanged input array [row, column]; no resampling or image-coordinate transform.",
        },
        "limitations": [
            "Visibility is conditional on fixed cameras, exact input geometry and opaque double-sided rasterization.",
            "Composition does not verify cameras, geometry identity, rasterizer provenance or physical scale.",
            "Pixel-layer ownership is not whole-feature ownership, physical fidelity, lamp depth or optics.",
            "Coverage is limited by input raster resolution, clipping and rasterizer sampling.",
            "Self-occlusion within a layer was already resolved upstream and is not reported here.",
            "All competing geometry must be supplied; omitted occluders can change ownership.",
            "RGB is an opaque diagnostic, not material appearance; black or magenta colors do not encode ownership reliably.",
            "Epsilon is numerical classification only; nearest_depth always retains the actual minimum.",
        ],
        "software_assumptions": [
            "Nonempty list/tuple; positive HxW; plain native float64 and uint8 ndarrays.",
            "Color list/tuple/ndarray has three non-boolean integer channels; extra layer fields are ignored.",
            "Tuple return order: owner, nearest_depth, rgb, report; pixel counts partition projected coverage.",
        ],
    }
    return owner, nearest_depth, rgb, report

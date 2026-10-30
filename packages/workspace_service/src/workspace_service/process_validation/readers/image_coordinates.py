"""Bind image-coordinate observations to an exact related raster artifact."""

import io
import warnings

from PIL import Image, UnidentifiedImageError

from .base import ValidationIssue


def verify_image_frame(frame, check, context):
    role = check.parameters.get("image_subject_role")
    images = [s for s in context.related_snapshots if s.subject.role == role]
    if not isinstance(role, str) or len(images) != 1:
        raise ValidationIssue(
            "measurement.image_subject",
            "Bind the exact reference image through image_subject_role and related_roles.",
            state="inconclusive",
            category="missing_evidence",
        )
    image = images[0]
    if image.subject.kind != "file" or image.subject.sha256 != frame.image_sha256:
        raise ValidationIssue(
            "measurement.frame",
            "The observed image frame does not identify the bound raster bytes.",
            state="inconclusive",
            category="source_conflict",
        )
    context.checkpoint()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(image.content)) as raster:
                raster.verify()
            with Image.open(io.BytesIO(image.content)) as raster:
                if (
                    raster.width * raster.height * 4
                    > context.budget.memory_limit_mb * 1024 * 1024 // 4
                ):
                    raise ValidationIssue(
                        "reader.image_memory_limit",
                        "The reference raster exceeds the configured inspection memory budget.",
                        category="capability_unavailable",
                        action="restore_capability",
                    )
                if (
                    raster.size != (frame.width_px, frame.height_px)
                    or getattr(raster, "n_frames", 1) != 1
                    or raster.getexif().get(274, 1) != 1
                ):
                    raise ValidationIssue(
                        "measurement.frame",
                        "Image dimensions differ or the raster needs explicit frame/orientation normalization.",
                        state="inconclusive",
                        category="source_conflict",
                    )
    except (
        OSError,
        ValueError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        if isinstance(exc, ValidationIssue):
            raise
        raise ValidationIssue(
            "measurement.image_content",
            "The bound reference image could not be verified as a bounded raster.",
            state="inconclusive",
            category="missing_evidence",
        ) from exc
    context.checkpoint()
    return f"subject:{image.subject.id}@{image.subject.sha256}"

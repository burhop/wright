"""Identity of a measured image coordinate system, independent of camera models."""

from typing import Annotated, Literal

from pydantic import Field

from .process_validation import Contract, Digest, canonical_digest


class ImageCoordinateFrame(Contract):
    schema_version: Literal["wright.image-coordinate-frame/1"] = (
        "wright.image-coordinate-frame/1"
    )
    image_sha256: Digest
    width_px: Annotated[int, Field(strict=True, gt=0)]
    height_px: Annotated[int, Field(strict=True, gt=0)]
    axes: Literal["x-right-y-down", "x-right-y-up"]
    origin: Literal["top-left", "bottom-left"]
    pixel_reference: Literal["centers", "edges"]

    def identifier(self) -> str:
        return "image-frame:" + canonical_digest(self)

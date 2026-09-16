"""Bounded in-memory MCP image observations with metadata-only run evidence."""

from __future__ import annotations

import base64
import binascii
import hashlib
import struct


MAX_IMAGE_BASE64_BYTES = 4 * 1024 * 1024
MAX_IMAGES_PER_RESULT = 4
MAX_IMAGES_PER_TASK = 8
# Installed Hermes' request-body cap is 10,000,000 bytes. Reserve headroom for
# the bounded textual transcript, schemas and JSON encoding below that cap.
MAX_TASK_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_EDGE = 4096


def _dimensions(raw, mime):
    if mime == "image/png":
        if len(raw) < 33 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
            raise ValueError("invalid_image_header")
        return struct.unpack(">II", raw[16:24])
    if mime != "image/jpeg" or not raw.startswith(b"\xff\xd8\xff"):
        raise ValueError("invalid_image_header")
    offset = 2
    while offset + 3 < len(raw):
        if raw[offset] != 0xFF:
            raise ValueError("invalid_image_header")
        while offset < len(raw) and raw[offset] == 0xFF:
            offset += 1
        if offset >= len(raw):
            break
        marker = raw[offset]
        offset += 1
        if marker in {0xD8, 0x01, *range(0xD0, 0xD8)}:
            continue
        if marker in {0xD9, 0xDA} or offset + 2 > len(raw):
            break
        length = int.from_bytes(raw[offset : offset + 2], "big")
        if length < 2 or offset + length > len(raw):
            break
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            if length < 8:
                break
            height, width = struct.unpack(">HH", raw[offset + 3 : offset + 7])
            return width, height
        offset += length
    raise ValueError("invalid_image_header")


def image_observation(content):
    """Detach native ImageContent bytes before any result can enter a run record.

    Images stay in a private return value only for model transport. Rejections
    retain a bounded static reason, never the malformed/unbounded payload.
    Header dimensions bound decoding work at the receiving vision provider;
    this is transport validation, not an engineering image-content assessment.
    """
    safe_content, images, evidence, errors = [], [], [], []
    for index, part in enumerate(content):
        if part.get("type") != "image":
            safe_content.append(part)
            continue
        data, mime = part.get("data"), part.get("mimeType")
        metadata = {"type": "image", "content_index": index, "base64_omitted": True}
        try:
            if not isinstance(mime, str) or mime not in {"image/png", "image/jpeg"}:
                raise ValueError("unsupported_image_type")
            metadata["mimeType"] = mime
            if not isinstance(data, str) or not data:
                raise ValueError("invalid_image_base64")
            metadata["encoded_bytes"] = len(data)
            if len(evidence) >= MAX_IMAGES_PER_RESULT:
                raise ValueError("image_count_limit")
            if len(data) > MAX_IMAGE_BASE64_BYTES:
                raise ValueError("image_size_limit")
            try:
                raw = base64.b64decode(data, validate=True)
            except (binascii.Error, ValueError):
                raise ValueError("invalid_image_base64") from None
            width, height = _dimensions(raw, mime)
            if not 0 < width <= MAX_IMAGE_EDGE or not 0 < height <= MAX_IMAGE_EDGE:
                raise ValueError("image_dimension_limit")
            metadata.update(
                sha256=hashlib.sha256(raw).hexdigest(),
                size_bytes=len(raw),
                width=width,
                height=height,
                disposition="available_for_model",
            )
            images.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{data}",
                        "detail": "high",
                    },
                }
            )
        except ValueError as error:
            reason = str(error)
            metadata.update(disposition="rejected", reason=reason)
            errors.append(reason)
        safe_content.append(metadata)
        evidence.append(metadata)
    return safe_content, images, evidence, errors

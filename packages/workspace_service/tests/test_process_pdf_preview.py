import base64
import hashlib
import io
import subprocess

import pypdfium2
import pytest
from PIL import Image

from workspace_service.process_interfaces import pdf_preview as reader
from workspace_service.process_interfaces.representations import (
    RepresentationUnavailable,
)


def pdf_bytes():
    with pypdfium2.PdfDocument.new() as doc:
        doc.new_page(300, 200).close()
        doc.new_page(200, 300).close()
        stream = io.BytesIO()
        doc.save(stream)
        return stream.getvalue()


def test_actual_pdf_pages_keep_exact_source_and_raster_dimensions():
    data = pdf_bytes()
    sha = hashlib.sha256(data).hexdigest()
    for page, expected in [(1, (900, 600)), (2, (600, 900))]:
        view = reader.read_pdf_page(data, sha, page=page)
        assert view["source_sha256"] == sha
        assert view["page"] == page and view["page_count"] == 2
        with Image.open(io.BytesIO(base64.b64decode(view["png_base64"]))) as image:
            assert image.format == "PNG" and image.size == expected
        assert (view["width"], view["height"]) == expected


@pytest.mark.parametrize("page", [0, 201, True, 1.5, "1"])
def test_invalid_page_does_not_launch_renderer(monkeypatch, page):
    monkeypatch.setattr(
        reader.subprocess, "run", lambda *a, **kw: pytest.fail("Renderer launched")
    )
    data = pdf_bytes()
    with pytest.raises(RepresentationUnavailable):
        reader.read_pdf_page(data, hashlib.sha256(data).hexdigest(), page=page)


def test_identity_and_size_are_checked_before_renderer(monkeypatch):
    monkeypatch.setattr(
        reader.subprocess, "run", lambda *a, **kw: pytest.fail("Renderer launched")
    )
    data = pdf_bytes()
    with pytest.raises(RepresentationUnavailable):
        reader.read_pdf_page(data, "0" * 64)
    monkeypatch.setattr(reader, "MAX_PDF_BYTES", len(data) - 1)
    with pytest.raises(RepresentationUnavailable):
        reader.read_pdf_page(data, hashlib.sha256(data).hexdigest())


def test_bad_pdf_or_missing_page_has_explicit_fallback():
    for data, page in [(b"%PDF-broken", 1), (pdf_bytes(), 3)]:
        with pytest.raises(RepresentationUnavailable):
            reader.read_pdf_page(data, hashlib.sha256(data).hexdigest(), page=page)


def test_renderer_timeout_is_bounded_and_does_not_forward_credentials(monkeypatch):
    monkeypatch.setenv("WRIGHT_API_TOKEN", "test-do-not-forward")

    def timeout(args, **options):
        assert options["timeout"] == 12
        assert "WRIGHT_API_TOKEN" not in options["env"]
        assert options["input"].startswith(b"%PDF-")
        raise subprocess.TimeoutExpired(args, 12)

    monkeypatch.setattr(reader.subprocess, "run", timeout)
    data = pdf_bytes()
    with pytest.raises(RepresentationUnavailable):
        reader.read_pdf_page(data, hashlib.sha256(data).hexdigest())

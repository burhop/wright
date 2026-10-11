"""Passive PDF page rendering from already-authorized bytes, in a bounded child.

PDFium is not thread-safe. A short-lived renderer isolates concurrent readers;
it receives no file path, application token, form action or process authority.
"""

import base64
import hashlib
import io
import json
import math
import os
import subprocess
import sys

from .representations import RepresentationUnavailable

MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_PAGES = 200
MAX_VIEW_BYTES = 8 * 1024 * 1024


def read_pdf_page(content, source_sha256, *, page=1):
    if (
        type(page) is not int
        or not 1 <= page <= MAX_PAGES
        or not 0 < len(content) <= MAX_PDF_BYTES
        or not content.startswith(b"%PDF-")
        or hashlib.sha256(content).hexdigest() != source_sha256
    ):
        raise RepresentationUnavailable("The PDF identity, page or size is invalid.")
    try:
        response = subprocess.run(
            [sys.executable, "-m", __name__, "--page", str(page)],
            input=content,
            capture_output=True,
            timeout=12,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            env={
                key: value
                for key, value in os.environ.items()
                if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
            },
        )
        if len(response.stdout) > MAX_VIEW_BYTES:
            raise ValueError("PDF preview exceeds its output bound")
        document = json.loads(response.stdout)
        if document["source_sha256"] != source_sha256 or document["page"] != page:
            raise ValueError("PDF preview identity mismatch")
        return document
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
        raise RepresentationUnavailable(
            "The PDF page could not be rendered within its supported bounds."
        ) from error


def _render(content, number):
    import pypdfium2 as pdfium

    if not 0 < len(content) <= MAX_PDF_BYTES:
        raise ValueError("PDF size exceeds preview bound")
    with pdfium.PdfDocument(content) as document:
        count = len(document)
        if not 1 <= number <= count <= MAX_PAGES:
            raise ValueError("PDF page count is outside preview bounds")
        page = document[number - 1]
        width, height = page.get_size()
        if not all(math.isfinite(n) and 0 < n <= 14400 for n in (width, height)):
            raise ValueError("PDF page dimensions are outside preview bounds")
        # No forms, scripts, links or attachments are opened. Render one page.
        scale = min(3, 1800 / max(width, height))
        bitmap = page.render(scale=scale, draw_annots=True)
        try:
            png = io.BytesIO()
            with bitmap.to_pil() as image:
                image.save(png, format="PNG")
            return {
                "format": "wright.pdf.page.v1",
                "source_sha256": hashlib.sha256(content).hexdigest(),
                "page": number,
                "page_count": count,
                "width": bitmap.width,
                "height": bitmap.height,
                "png_base64": base64.b64encode(png.getvalue()).decode("ascii"),
            }
        finally:
            bitmap.close()
            page.close()


if __name__ == "__main__":
    try:
        assert len(sys.argv) == 3 and sys.argv[1] == "--page"
        data = _render(sys.stdin.buffer.read(MAX_PDF_BYTES + 1), int(sys.argv[2]))
        encoded = json.dumps(data, separators=(",", ":")).encode("utf-8")
        assert len(encoded) <= MAX_VIEW_BYTES
        sys.stdout.buffer.write(encoded)
    except Exception:
        # Do not leak document content or renderer paths in an error response.
        raise SystemExit(2)

"""Versioned confined primary-reference retrieval with actual rendered observations."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import threading
import urllib.parse
import urllib.request

import pi_reference_mcp as original

PRODUCT_URL = "https://www.ruthex.de/products/ruthex-gewindeeinsatz-m2-5-70-stuck-rx-m2-5x5-7-messing-gewindebuchsen"
SUPPLIER_REFERENCES = (
    ("insert-product.html", PRODUCT_URL),
    ("insert-dimensions.jpg", "https://www.ruthex.de/cdn/shop/files/1Tabelle.PT05_eb2a30fa-5c34-46f8-b557-a6c432354560_800x.jpg?v=1748341911"),
    ("insert-installation.jpg", "https://www.ruthex.de/cdn/shop/files/2Beispielbild_89e9a32b-7812-4470-b706-f2e5af5770ef_800x.jpg?v=1748341911"),
)
VIEWS = {"full": (0, 0, 1, 1), "top_left": (0, 0, .5, .5), "top_right": (.5, 0, 1, .5),
         "bottom_left": (0, .5, .5, 1), "bottom_right": (.5, .5, 1, 1)}
MAX_PNG_BYTES = 3 * 1024 * 1024  # Base64 transport remains at most4MiB.
RENDER_LOCK = threading.Lock()


def scope(root, source_document, research_directory):
    root = Path(root).resolve()
    source = original.confined(root, source_document)
    research = original.confined(root, research_directory)
    if source.parent.name != "inputs" or source.read_bytes() != Path(__file__).read_bytes():
        raise ValueError("Exact visual operation source must be a same-attempt input")
    base_source = source.parent / "pi_reference_mcp.py"
    if base_source.read_bytes() != Path(original.__file__).read_bytes():
        raise ValueError("Exact retrieval dependency must also be a same-attempt input")
    if research != source.parent.parent / "artifacts" / "research":
        raise ValueError("References must stay within this attempt's research output")
    return root, source, base_source, research


def checked_supplier_url(url):
    if url not in {value for _, value in SUPPLIER_REFERENCES}:
        raise ValueError("Only the fixed supplier primary-reference URLs are permitted")
    return url


class SupplierRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        checked_supplier_url(newurl)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def retrieve(root, operation_source_document, output_directory):
    root, source, base_source, output = scope(root, operation_source_document, output_directory)
    result = original.retrieve(root, base_source.relative_to(root).as_posix(), output_directory)
    opener = urllib.request.build_opener(SupplierRedirect())
    rows = []
    for filename, url in SUPPLIER_REFERENCES:
        request = urllib.request.Request(checked_supplier_url(url), headers={"User-Agent": "WrightPiReference/2.0"})
        with opener.open(request, timeout=45) as response:
            checked_supplier_url(response.url)
            data = response.read(original.MAX_BYTES + 1)
        if not data or len(data) > original.MAX_BYTES:
            raise ValueError("Supplier reference is empty or exceeds the byte limit")
        (output / filename).write_bytes(data)
        row = {"path": filename, "url": url, "sha256": original.digest(data), "bytes": len(data),
               "retrieved_at": datetime.now(timezone.utc).isoformat()}
        if filename.endswith(".html"):
            parser = original.HtmlText()
            parser.feed(data.decode("utf-8"))
            text = "\n".join(parser.parts)
            if "RX-M2.5x5.7" not in text:
                raise ValueError("Supplier product identity is missing")
            (output / (filename + ".txt")).write_text(text, encoding="utf-8")
            row["text_path"] = filename + ".txt"
            row["text_sha256"] = original.digest(text.encode())
        else:
            from PIL import Image
            with Image.open(io.BytesIO(data)) as picture:
                if picture.width * picture.height > 20_000_000:
                    raise ValueError("Supplier source image exceeds the pixel limit")
                picture.verify()
        rows.append(row)
    manifest = {"operation_sha256": original.digest(source.read_bytes()), "dependency_sha256": original.digest(base_source.read_bytes()),
                "selection": "Candidate ruthex RX-M2.5x5.7; workflow must inspect actual source geometry before selection",
                "sources": rows, "scope": "Primary source bytes; no operator-extracted dimensions or rating claims"}
    (output / "supplier-evidence.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {**result, "supplier_manifest": "supplier-evidence.json", "supplier_sources": rows,
            "visual_observation": "Call observe_pi_primary_page for actual board drawing and supplier drawing images"}


def read_text(root, operation_source_document, research_directory, document_name, page_number, offset=0):
    root, source, base_source, research = scope(root, operation_source_document, research_directory)
    if document_name != "insert-product.html":
        return original.read_page(root, base_source.relative_to(root).as_posix(), research_directory, document_name, page_number, offset)
    if page_number != 1 or isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 100000:
        raise ValueError("Supplier HTML has one bounded text page")
    record = supplier_record(source, research, document_name)
    data = (research / record["text_path"]).read_bytes()
    if original.digest(data) != record["text_sha256"]:
        raise ValueError("Supplier extracted text changed")
    text = data.decode("utf-8")
    end = min(offset + 4000, len(text))
    return {"document": document_name, "url": record["url"], "sha256": record["sha256"], "offset": offset,
            "text": text[offset:end], "next_offset": end if end < len(text) else None}


def supplier_record(source, research, document_name):
    manifest = json.loads((research / "supplier-evidence.json").read_text(encoding="utf-8"))
    if manifest["operation_sha256"] != original.digest(source.read_bytes()):
        raise ValueError("Supplier reference operation identity changed")
    if document_name not in {name for name, _ in SUPPLIER_REFERENCES}:
        raise ValueError("Only the exact supplier primary references are readable")
    row = next(row for row in manifest["sources"] if row["path"] == document_name)
    if original.digest((research / document_name).read_bytes()) != row["sha256"]:
        raise ValueError("Supplier reference bytes changed")
    return row


def observe(root, operation_source_document, research_directory, document_name, page_number=1, view="full"):
    from PIL import Image
    import pypdfium2

    root, source, base_source, research = scope(root, operation_source_document, research_directory)
    if view not in VIEWS or isinstance(page_number, bool) or not isinstance(page_number, int):
        raise ValueError("Select one bounded page and a fixed full/quadrant view")
    with RENDER_LOCK:
        if document_name in {name for name, _ in original.REFERENCES}:
            record = original.read_page(root, base_source.relative_to(root).as_posix(), research_directory, document_name, page_number)
            with pypdfium2.PdfDocument(str(research / document_name)) as pdf:
                page = pdf[page_number - 1]
                scale = (2200 if view == "full" else 4400) / max(page.get_size())
                bitmap = page.render(scale=scale)
                picture = bitmap.to_pil().copy()
                bitmap.close()
                page.close()
        elif document_name in {name for name, _ in SUPPLIER_REFERENCES if not name.endswith(".html")}:
            if page_number != 1:
                raise ValueError("Supplier drawing images contain one page")
            record = supplier_record(source, research, document_name)
            picture = Image.open(research / document_name).convert("RGB")
        else:
            raise ValueError("Only actual selected primary drawings can be observed")
        if picture.width * picture.height > 20_000_000:
            raise ValueError("Rendering exceeds the pixel limit")
        bounds = VIEWS[view]
        box = tuple(round(value * (picture.width if i % 2 == 0 else picture.height)) for i, value in enumerate(bounds))
        picture = picture.crop(box)
        picture.thumbnail((2200, 2200))
        buffer = io.BytesIO()
        picture.save(buffer, format="PNG", optimize=True)
        data = buffer.getvalue()
        if len(data) > MAX_PNG_BYTES:
            raise ValueError("Actual rendered image exceeds the encoded byte limit")
        relative = f"observations/{document_name}.page-{page_number}.{view}.png"
        destination = research / relative
        destination.parent.mkdir(exist_ok=True)
        if destination.exists() and destination.read_bytes() != data:
            raise ValueError("Existing rendered observation changed")
        if not destination.exists():
            destination.write_bytes(data)
        receipt = {"document": document_name, "source_url": record["url"], "source_sha256": record["sha256"],
                   "page": page_number, "view": view, "normalized_crop": bounds, "width": picture.width, "height": picture.height,
                   "image_sha256": original.digest(data), "image_bytes": len(data), "image_path": destination.relative_to(root).as_posix(),
                   "operation_sha256": original.digest(source.read_bytes()), "scope": "Actual source pixels; no inferred dimensions or operator annotation"}
        destination.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        return receipt, data


def main():
    from mcp.server.fastmcp import FastMCP
    from mcp.types import CallToolResult, ImageContent, TextContent

    root = os.environ["WRIGHT_PI_REFERENCE_WORKSPACE"]
    app = FastMCP("wright-pi-primary-visual-v2")

    @app.tool()
    def retrieve_pi_primary_references(operation_source_document: str, output_directory: str) -> dict:
        """Retrieve fixed Pi PDFs and candidate insert supplier references into this exact attempt."""
        return retrieve(root, operation_source_document, output_directory)

    @app.tool()
    def read_pi_primary_text(operation_source_document: str, research_directory: str, document_name: str, page_number: int, offset: int = 0) -> dict:
        """Read at most4000characters of an exact retrieved primary source, preserving its identity."""
        return read_text(root, operation_source_document, research_directory, document_name, page_number, offset)

    @app.tool()
    def observe_pi_primary_page(operation_source_document: str, research_directory: str, document_name: str, page_number: int = 1, view: str = "full"):
        """Observe actual source pixels: fixed full/top_left/top_right/bottom_left/bottom_right page view."""
        receipt, data = observe(root, operation_source_document, research_directory, document_name, page_number, view)
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(receipt)), ImageContent(type="image", mimeType="image/png", data=base64.b64encode(data).decode("ascii"))])

    app.run(transport="stdio")


if __name__ == "__main__":
    main()

"""Fixed primary Raspberry Pi retrieval; no CAD, shell, solver or arbitrary URL tool."""
from __future__ import annotations

from datetime import UTC, datetime
import gzip
import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path, PurePosixPath
import urllib.parse
import urllib.request

REFERENCES = (
    ("manufacturer-drawing.pdf", "https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf"),
    ("manufacturer-product-brief.pdf", "https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-008348-DS-6-raspberry-pi-5-product-brief.pdf"),
    ("manufacturer-cooler-drawing.pdf", "https://pip-assets.raspberrypi.com/categories/993-raspberry-pi-active-cooler/documents/RP-008187-DS-1-raspberry-pi-active-cooler-mechanical-drawing.pdf"),
)
ORIGINS = {"pip-assets.raspberrypi.com", "www.raspberrypi.com"}
MAX_BYTES = 12 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def confined(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("Use an explicit relative POSIX path")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part.startswith(".") for part in path.parts):
        raise ValueError("Hidden, absolute and parent paths are unavailable")
    result = (root/path).resolve()
    if not result.is_relative_to(root):
        raise ValueError("Path escapes configured workspace")
    return result


def checked_url(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ORIGINS or parts.username or parts.password or parts.port not in (None, 443):
        raise ValueError("Only configured public manufacturer origins are allowed")
    return url


class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class HtmlText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.hidden = max(0, self.hidden-1)

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def retrieve(root, operation_source_document, output_directory):
    from pypdf import PdfReader
    import importlib.metadata

    root = Path(root).resolve()
    source = confined(root, operation_source_document)
    if source.parent.name != "inputs" or source.read_bytes() != Path(__file__).read_bytes():
        raise ValueError("Exact executing operation must be an enrolled attempt input")
    output = confined(root, output_directory)
    if output != source.parent.parent/"artifacts"/"research":
        raise ValueError("Research output must be confined to this exact attempt")
    if output.exists():
        raise ValueError("Research output exists; preserve it and use a fresh attempt")
    output.mkdir(parents=True)
    opener = urllib.request.build_opener(Redirect())
    rows = []
    for filename, url in REFERENCES:
        request = urllib.request.Request(checked_url(url), headers={"User-Agent": "WrightPiReference/1.0"})
        with opener.open(request, timeout=45) as response:
            checked_url(response.url)
            raw = response.read(MAX_BYTES+1)
            final_url = response.url
            content_type = response.headers.get_content_type()
        compressed = raw.startswith(b"\x1f\x8b")
        data = gzip.decompress(raw) if compressed else raw
        if not data or len(raw) > MAX_BYTES or len(data) > MAX_BYTES:
            raise ValueError("Empty or oversized manufacturer document")
        pages = None
        if filename.endswith(".pdf"):
            if not data.startswith(b"%PDF"):
                raise ValueError("Manufacturer drawing is not a PDF")
            document = PdfReader(io.BytesIO(data))
            page_text = [page.extract_text() or "" for page in document.pages]
            text = "\n\n".join(page_text)
            pages = [{"page": index+1, "text": value} for index, value in enumerate(page_text)]
            if "Raspberry Pi" not in text or (filename == "manufacturer-drawing.pdf" and ("85" not in text or "56" not in text)):
                raise ValueError("Retrieved PDF does not expose expected Pi drawing identity")
        else:
            if content_type not in {"text/html", "application/xhtml+xml"}:
                raise ValueError("Manufacturer reference is not HTML")
            parser = HtmlText()
            parser.feed(data.decode("utf-8", errors="replace"))
            text = "\n".join(parser.parts)
            if "Raspberry Pi" not in text:
                raise ValueError("Manufacturer page identity is missing")
        (output/filename).write_bytes(data)
        text_path = output/(filename+".txt")
        text_path.write_text(text, encoding="utf-8")
        rows.append({"path": filename, "sha256": digest(data), "bytes": len(data), "url": url,
                     "final_url": final_url, "retrieved_at": datetime.now(UTC).isoformat(), "content_type": content_type,
                     "http_body_sha256": digest(raw), "gzip_decoded": compressed, "text_path": text_path.name,
                     "extracted_text_sha256": digest(text.encode()), "pages": pages})
    manifest = {"operation": "retrieve_pi_manufacturer_references", "operation_sha256": digest(source.read_bytes()),
                "pypdf_version": importlib.metadata.version("pypdf"), "sources": rows,
                "scope": "Actual reference retrieval and text extraction, not a completed engineering design",
                "limits": ["Manufacturer drawing dimensions are approximate reference information",
                           "Omitted components and accessory keepouts remain unresolved; consult physical board",
                           "Customer synthetic heat loads and fan curve are not manufacturer ratings"],
                "content_validation": "not_measured"}
    (output/"manufacturer-evidence.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    return {"output_directory": output_directory, "manifest": "manufacturer-evidence.json",
            "sources": [{key: row[key] for key in ("path", "sha256", "bytes", "text_path")} for row in rows],
            "limits": manifest["limits"], "pypdf_version": manifest["pypdf_version"]}


def read_page(root, operation_source_document, research_directory, document_name, page_number, offset=0):
    root = Path(root).resolve()
    source = confined(root, operation_source_document)
    research = confined(root, research_directory)
    if source.parent.name != "inputs" or source.read_bytes() != Path(__file__).read_bytes():
        raise ValueError("Exact executing source must be this attempt input")
    if research != source.parent.parent/"artifacts"/"research":
        raise ValueError("Only this attempt's retrieved references are readable")
    if document_name not in {row[0] for row in REFERENCES}:
        raise ValueError("Only the three exact primary PDFs are readable")
    if isinstance(page_number, bool) or not isinstance(page_number, int) or not 1 <= page_number <= 30:
        raise ValueError("Select a one-based bounded PDF page")
    if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 100000:
        raise ValueError("Page text offset is outside the supported range")
    manifest = json.loads((research/"manufacturer-evidence.json").read_text())
    if manifest["operation_sha256"] != digest(source.read_bytes()):
        raise ValueError("Reference manifest source changed")
    record = next(row for row in manifest["sources"] if row["path"] == document_name)
    if digest((research/document_name).read_bytes()) != record["sha256"]:
        raise ValueError("Retrieved reference bytes changed")
    pages = record["pages"]
    if page_number > len(pages):
        raise ValueError("PDF page does not exist")
    text = pages[page_number-1]["text"]
    end = min(offset+4000, len(text))
    return {"document": document_name, "url": record["url"], "sha256": record["sha256"], "page": page_number,
            "page_count": len(pages), "offset": offset, "next_offset": end if end < len(text) else None,
            "page_text_characters": len(text), "text": text[offset:end], "limits": manifest["limits"]}


def main():
    from mcp.server.fastmcp import FastMCP
    root = Path(os.environ["WRIGHT_PI_REFERENCE_WORKSPACE"]).resolve()
    app = FastMCP("wright-pi-primary-reference")

    @app.tool()
    def retrieve_pi_manufacturer_references(operation_source_document: str, output_directory: str) -> dict:
        """Retrieve the three fixed official Pi references into this source-bound attempt."""
        return retrieve(root, operation_source_document, output_directory)

    @app.tool()
    def read_pi_reference_page(operation_source_document: str, research_directory: str, document_name: str, page_number: int, offset: int = 0) -> dict:
        """Read at most 4000 characters of one exact retrieved primary PDF page with lineage."""
        return read_page(root, operation_source_document, research_directory, document_name, page_number, offset)

    app.run(transport="stdio")


if __name__ == "__main__":
    main()

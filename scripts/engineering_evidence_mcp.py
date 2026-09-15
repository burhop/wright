"""Selected MCP for public engineering references and confined file manifests.

No script execution, arbitrary filesystem writes, supplier uploads or device calls.
Each operation requires an exact staged copy of this executing source.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from datetime import UTC, datetime
from html.parser import HTMLParser
import urllib.parse
import urllib.request

MAX_BYTES = 5 * 1024 * 1024
MAX_OBSERVATION_CHARS = 4000


class ReferenceText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def confined(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("Use a nonempty workspace-relative POSIX path")
    parts = PurePosixPath(relative).parts
    if PurePosixPath(relative).is_absolute() or any(p in {"..", "."} or p.startswith(".") for p in parts):
        raise ValueError("Hidden, parent and absolute paths are unavailable")
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Path escapes configured workspace")
    return target


def scope(root, source_document, output_root, *, create=True):
    source = confined(root, source_document)
    if source.read_bytes() != Path(__file__).read_bytes():
        raise ValueError("Staged operation source differs from executing source")
    if source.parent.name != "inputs":
        raise ValueError("Operation source must be an explicit attempt input")
    output = confined(root, output_root)
    if output != source.parent.parent / "artifacts":
        raise ValueError("Outputs must be in this attempt's sibling artifacts directory")
    if create:
        output.mkdir(parents=True, exist_ok=True)
    return output


def write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)
    return {"name": path.name, "bytes": len(data), "sha256": digest(data)}


def checked_url(url, origins):
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("Reference URL must be a bounded string")
    value = urllib.parse.urlsplit(url)
    if value.scheme != "https" or value.username or value.password or value.port not in {None, 443}:
        raise ValueError("Only public HTTPS references on configured origins are available")
    if f"https://{value.hostname}" not in origins:
        raise ValueError("Reference origin is not configured")
    return url


class ReferenceRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, origins):
        self.origins = origins

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_url(newurl, self.origins)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def retrieve(root, origins, source_document, output_root, urls):
    output = scope(root, source_document, output_root)
    if not isinstance(urls, list) or not 1 <= len(urls) <= 12:
        raise ValueError("Provide one to twelve exact reference URLs")
    urls = [checked_url(url, origins) for url in urls]
    destinations = [output / f"supplier-source-{i + 1}.html" for i in range(len(urls))]
    manifest_path = output / "supplier-evidence.json"
    text_destinations = [path.with_suffix(".txt") for path in destinations]
    if any(path.exists() for path in [*destinations, *text_destinations, manifest_path]):
        raise ValueError("Reference outputs already exist; inspect before using a fresh attempt")
    opener = urllib.request.build_opener(ReferenceRedirect(origins))
    rows = []
    for url, destination in zip(urls, destinations):
        request = urllib.request.Request(url, headers={"User-Agent": "WrightEngineeringReference/1.0"})
        with opener.open(request, timeout=40) as response:
            checked_url(response.url, origins)
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
                raise ValueError("Reference is not an HTML/text document")
            data = response.read(MAX_BYTES + 1)
            if not data or len(data) > MAX_BYTES:
                raise ValueError("Reference response is empty or too large")
            decoded = data.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            extracted = ReferenceText()
            extracted.feed(decoded)
            text = decoded if content_type == "text/plain" else "\n".join(extracted.parts)
            text_file = write_new(destination.with_suffix(".txt"), text.encode("utf-8"))
            rows.append({**write_new(destination, data), "url": url, "final_url": response.url,
                         "retrieved_at": datetime.now(UTC).isoformat(), "content_type": content_type,
                         "text_file": text_file, "text_characters": len(text), "preview": text[:120],
                         "text_truncated": False})
    result = {"operation": "retrieve_public_references", "sources": rows,
              "executing_source_sha256": digest(Path(__file__).read_bytes()),
              "supplier_acceptance": False, "content_validation": "not_measured"}
    saved = write_new(manifest_path, (json.dumps(result, indent=2) + "\n").encode())
    compact = {"operation": result["operation"], "evidence_file": manifest_path.name,
               "evidence_sha256": saved["sha256"], "executing_source_sha256": result["executing_source_sha256"],
               "sources": [{"source_index": i + 1, "bytes": row["bytes"],
                            "text_characters": row["text_characters"], "preview": row["preview"]}
                           for i, row in enumerate(rows)],
               "supplier_acceptance": False, "content_validation": "not_measured",
               "next_action": "Use read_reference_text with this evidence_sha256 and a source_index for bounded relevant excerpts."}
    if len(json.dumps(compact, indent=2)) > MAX_OBSERVATION_CHARS:
        for row in compact["sources"]:
            row.pop("preview")
    return compact


def read_reference(root, source_document, output_root, source_index, expected_evidence_sha256,
                   offset=0, max_chars=2000, query=None):
    """Read only hash-bound retained text, with optional literal forward search."""
    output = scope(root, source_document, output_root, create=False)
    if type(source_index) is not int or not 1 <= source_index <= 12:
        raise ValueError("Source index must be an integer from one to twelve")
    if type(offset) is not int or offset < 0 or type(max_chars) is not int or not 1 <= max_chars <= 3000:
        raise ValueError("Use a nonnegative character offset and one to 3000 excerpt characters")
    if query is not None and (not isinstance(query, str) or not 1 <= len(query) <= 120):
        raise ValueError("Search must be a literal string of one to 120 characters")
    manifest = confined(root, output_root + "/supplier-evidence.json")
    if not manifest.is_relative_to(output):
        raise ValueError("Evidence manifest escapes this attempt output scope")
    data = manifest.read_bytes()
    if len(data) > 128 * 1024 or digest(data) != expected_evidence_sha256:
        raise ValueError("Retained evidence manifest differs from requested exact identity")
    evidence = json.loads(data)
    if evidence["executing_source_sha256"] != digest(Path(__file__).read_bytes()):
        raise ValueError("Evidence belongs to a different executing operation source")
    if source_index > len(evidence["sources"]):
        raise ValueError("Source index was not retrieved in this evidence manifest")
    row = evidence["sources"][source_index - 1]
    text_path = confined(root, output_root + f"/supplier-source-{source_index}.txt")
    if not text_path.is_relative_to(output):
        raise ValueError("Retained text escapes this attempt output scope")
    raw = text_path.read_bytes()
    if len(raw) > 3 * MAX_BYTES or len(raw) != row["text_file"]["bytes"] or digest(raw) != row["text_file"]["sha256"]:
        raise ValueError("Retained source text changed after retrieval")
    text = raw.decode("utf-8")
    if offset > len(text):
        raise ValueError("Offset exceeds retained source text")
    # re.IGNORECASE preserves original character offsets, unlike case folding.
    import re
    match = re.search(re.escape(query), text[offset:], re.IGNORECASE) if query else None
    start = offset + match.start() if match else offset
    excerpt = text[start:start + max_chars] if query is None or match else ""
    answer = {"source_index": source_index, "evidence_sha256": expected_evidence_sha256,
              "text_sha256": row["text_file"]["sha256"], "total_characters": len(text),
              "match_found": bool(match) if query else None, "start_offset": start,
              "end_offset": start + len(excerpt), "text": excerpt,
              "next_offset": start + len(excerpt) if excerpt and start + len(excerpt) < len(text) else None}
    while len(json.dumps(answer, indent=2)) > MAX_OBSERVATION_CHARS:
        answer["text"] = answer["text"][:-100]
        answer["end_offset"] = start + len(answer["text"])
        answer["next_offset"] = answer["end_offset"]
    return answer


def collect(root, source_document, output_root, files):
    output = scope(root, source_document, output_root)
    if not isinstance(files, list) or not 1 <= len(files) <= 128:
        raise ValueError("Provide one to 128 actual output references")
    rows, seen = [], set()
    for item in files:
        relative, role = item["path"], item["role"]
        path = confined(root, relative)
        if not path.is_relative_to(output) or path == output or path.name == "final-artifact-manifest.json":
            raise ValueError("Only existing same-attempt engineering outputs may be collected")
        if path in seen or not isinstance(role, str) or not role or len(role) > 160:
            raise ValueError("Output paths must be unique with bounded explicit role labels")
        size = path.stat().st_size
        if not path.is_file() or not 0 < size <= 512 * 1024 * 1024:
            raise ValueError("Output must be a bounded nonempty file")
        hashed = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hashed.update(chunk)
        rows.append({"path": relative, "role": role, "bytes": size, "sha256": hashed.hexdigest()})
        seen.add(path)
    result = {"operation": "collect_artifact_manifest", "files": rows,
              "executing_source_sha256": digest(Path(__file__).read_bytes()),
              "content_validation": "not_measured"}
    write_new(output / "final-artifact-manifest.json", (json.dumps(result, indent=2) + "\n").encode())
    return result


def main():
    from mcp.server.fastmcp import FastMCP

    root = Path(os.environ["WRIGHT_EVIDENCE_WORKSPACE"]).resolve(strict=True)
    origins = frozenset(json.loads(os.environ["WRIGHT_EVIDENCE_ORIGINS"]))
    if not origins:
        raise ValueError("Explicit allowed origins are required")
    mcp = FastMCP("wright-engineering-evidence")

    @mcp.tool()
    def retrieve_public_references(operation_source_document: str, output_root: str, urls: list[str]) -> dict:
        """Retain complete public HTML/text evidence; return compact metadata/previews, never full pages."""
        return retrieve(root, origins, operation_source_document, output_root, urls)

    @mcp.tool()
    def read_reference_text(operation_source_document: str, output_root: str, source_index: int,
                            expected_evidence_sha256: str, offset: int = 0, max_chars: int = 2000,
                            query: str | None = None) -> dict:
        """Read retained source by exact evidence hash/index; optional literal forward search, response <=4000 characters.

        Offset is a character offset; next_offset continues the excerpt. Search
        is case-insensitive from offset, never a regex or network request.
        No-match returns empty text. Read only relevant excerpts, not all pages.
        """
        return read_reference(root, operation_source_document, output_root, source_index,
                              expected_evidence_sha256, offset, max_chars, query)
    @mcp.tool()
    def collect_artifact_manifest(operation_source_document: str, output_root: str, files: list[dict[str, str]]) -> dict:
        """Hash explicitly named nonempty same-attempt outputs into a new manifest; no content qualification."""
        return collect(root, operation_source_document, output_root, files)

    mcp.run()


if __name__ == "__main__":
    main()

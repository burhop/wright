import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "pi_visual_reference_tests", ROOT / "scripts/pi_reference_visual_mcp.py"
)
operation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operation)


@pytest.fixture
def staged(tmp_path):
    inputs = tmp_path / "campaign/case/attempt/inputs"
    inputs.mkdir(parents=True)
    for name in ("pi_reference_mcp.py", "pi_reference_visual_mcp.py"):
        (inputs / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    source = (inputs / "pi_reference_visual_mcp.py").relative_to(tmp_path).as_posix()
    output = inputs.parent / "artifacts/research"
    output.mkdir(parents=True)
    return tmp_path, source, output.relative_to(tmp_path).as_posix()


def test_exact_source_and_retrieval_dependency_are_both_required(staged):
    root, source, research = staged
    operation.scope(root, source, research)
    dependency = root / source
    dependency.write_bytes(dependency.read_bytes() + b"# changed")
    with pytest.raises(ValueError, match="Exact visual operation"):
        operation.scope(root, source, research)


def test_rejects_cross_attempt_research_and_foreign_supplier_urls(staged):
    root, source, _ = staged
    with pytest.raises(ValueError, match="within this attempt"):
        operation.scope(root, source, "campaign/other/attempt/artifacts/research")
    for url in (
        "https://www.ruthex.de/account",
        "https://evil.invalid/image.png",
        "file:///etc/passwd",
    ):
        with pytest.raises(ValueError, match="fixed supplier"):
            operation.checked_supplier_url(url)


def test_supplier_text_pages_are_bounded_and_identity_checked(staged):
    root, source, research = staged
    directory = root / research
    body = b"actual-response-contract-test"
    text = "x" * 8001
    (directory / "insert-product.html").write_bytes(body)
    (directory / "insert-product.html.txt").write_text(text, encoding="utf-8")
    row = {
        "path": "insert-product.html",
        "url": operation.PRODUCT_URL,
        "sha256": operation.original.digest(body),
        "text_path": "insert-product.html.txt",
        "text_sha256": operation.original.digest(text.encode()),
    }
    (directory / "supplier-evidence.json").write_text(
        json.dumps(
            {
                "operation_sha256": operation.original.digest(
                    (root / source).read_bytes()
                ),
                "sources": [row],
            }
        ),
        encoding="utf-8",
    )
    result = operation.read_text(root, source, research, "insert-product.html", 1)
    assert len(result["text"]) == 4000 and result["next_offset"] == 4000
    assert (
        operation.read_text(root, source, research, "insert-product.html", 1, 8000)[
            "next_offset"
        ]
        is None
    )
    (directory / "insert-product.html").write_bytes(body + b"tamper")
    with pytest.raises(ValueError, match="reference bytes changed"):
        operation.read_text(root, source, research, "insert-product.html", 1)


@pytest.mark.parametrize("page,offset", [(2, 0), (1, True), (1, -1), (1, 100001)])
def test_supplier_reader_rejects_invalid_ranges_before_reading(staged, page, offset):
    root, source, research = staged
    with pytest.raises(ValueError, match="bounded text page"):
        operation.read_text(root, source, research, "insert-product.html", page, offset)

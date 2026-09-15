"""Boundary regressions for the selected engineering source/collection tools."""
import importlib.util
import json
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/engineering_evidence_mcp.py"
spec = importlib.util.spec_from_file_location("engineering_evidence", SOURCE)
operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operations)


def staged(tmp_path):
    source = tmp_path / "campaign/case/attempt/inputs/operation.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(SOURCE.read_bytes())
    return source.relative_to(tmp_path).as_posix(), "campaign/case/attempt/artifacts"


def test_collect_real_files_and_preserve_existing_output(tmp_path):
    source, output = staged(tmp_path)
    root = tmp_path / output
    root.mkdir()
    (root / "part.step").write_bytes(b"actual test operation payload")
    files = [{"path": output + "/part.step", "role": "folded CAD"}]
    result = operations.collect(tmp_path, source, output, files)
    assert result["files"][0]["sha256"] == operations.digest((root / "part.step").read_bytes())
    assert result["content_validation"] == "not_measured"
    original = (root / "final-artifact-manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        operations.collect(tmp_path, source, output, files)
    assert (root / "final-artifact-manifest.json").read_bytes() == original


@pytest.mark.parametrize("path", ["../secrets", "/outside", "C:/outside", "campaign/.hidden", "a\\b"])
def test_reject_escape_paths(tmp_path, path):
    with pytest.raises(ValueError):
        operations.confined(tmp_path, path)


def test_source_change_and_other_attempt_are_denied(tmp_path):
    source, output = staged(tmp_path)
    with pytest.raises(ValueError, match="sibling"):
        operations.scope(tmp_path, source, "campaign/other/attempt/artifacts")
    (tmp_path / source).write_text("print('different source')")
    with pytest.raises(ValueError, match="differs"):
        operations.scope(tmp_path, source, output)


def test_input_files_cannot_be_relabelled_outputs(tmp_path):
    source, output = staged(tmp_path)
    with pytest.raises(ValueError, match="same-attempt"):
        operations.collect(tmp_path, source, output, [{"path": source, "role": "CAD"}])


@pytest.mark.parametrize("url", ["http://sendcutsend.com/x", "https://evil.example/x", "file:///tmp/x",
                                 "https://user:password@sendcutsend.com/x", "https://sendcutsend.com:444/x"])
def test_reference_and_redirect_origin_guard(url):
    with pytest.raises(ValueError):
        operations.checked_url(url, {"https://sendcutsend.com"})
    with pytest.raises(ValueError):
        operations.ReferenceRedirect({"https://sendcutsend.com"}).redirect_request(None, None, 302, "", {}, url)


def test_actual_reference_text_excludes_scripts():
    parser = operations.ReferenceText()
    parser.feed("<h1>Bending</h1><script>untrusted code</script><p>Retain 1:1 scale</p>")
    assert parser.parts == ["Bending", "Retain 1:1 scale"]


def retained(tmp_path, text):
    source, output = staged(tmp_path)
    root = tmp_path / output
    root.mkdir()
    raw = text.encode()
    (root / "supplier-source-1.txt").write_bytes(raw)
    metadata = {"executing_source_sha256": operations.digest(SOURCE.read_bytes()),
                "sources": [{"text_file": {"bytes": len(raw), "sha256": operations.digest(raw)}}]}
    data = json.dumps(metadata).encode()
    (root / "supplier-evidence.json").write_bytes(data)
    return source, output, operations.digest(data)


def test_reader_paginates_complete_unicode_text_without_exceeding_budget(tmp_path):
    text = ('Line \\"熱量\\"\n' * 2000) + 'Relevant bending requirement'
    source, output, sha = retained(tmp_path, text)
    offset, pieces = 0, []
    while offset is not None:
        page = operations.read_reference(tmp_path, source, output, 1, sha, offset, 3000)
        assert len(json.dumps(page, indent=2)) <= 4000
        assert page['text'] == text[page['start_offset']:page['end_offset']]
        pieces.append(page['text'])
        offset = page['next_offset']
    assert ''.join(pieces) == text
    found = operations.read_reference(tmp_path, source, output, 1, sha, query='BENDING')
    assert found['text'] == 'bending requirement'
    assert found['start_offset'] == text.index('bending')
    absent = operations.read_reference(tmp_path, source, output, 1, sha, query='missing alloy')
    assert absent['match_found'] is False and absent['text'] == '' and absent['next_offset'] is None


@pytest.mark.parametrize('change', ['manifest', 'text', 'source', 'other_attempt', 'index', 'offset', 'budget'])
def test_reader_rejects_drift_or_unscoped_requests(tmp_path, change):
    source, output, sha = retained(tmp_path, 'Exact reference text')
    kwargs = {}
    if change == 'manifest':
        (tmp_path / output / 'supplier-evidence.json').write_text('{}')
    elif change == 'text':
        (tmp_path / output / 'supplier-source-1.txt').write_text('Altered reference')
    elif change == 'source':
        (tmp_path / source).write_text('Different operation')
    elif change == 'other_attempt':
        output = 'campaign/other/attempt/artifacts'
    elif change == 'offset':
        kwargs['offset'] = -1
    elif change == 'budget':
        kwargs['max_chars'] = 4001
    with pytest.raises(ValueError):
        operations.read_reference(tmp_path, source, output, 2 if change == 'index' else 1, sha, **kwargs)


def test_reader_does_not_create_an_absent_output_directory(tmp_path):
    source, output = staged(tmp_path)
    with pytest.raises(FileNotFoundError):
        operations.read_reference(tmp_path, source, output, 1, '0' * 64)
    assert not (tmp_path / output).exists()


def test_retrieval_retains_entire_page_but_returns_compact_metadata(tmp_path, monkeypatch):
    source, output = staged(tmp_path)
    data = ('<h1>Engineering</h1><p>' + 'Full material specification. ' * 2000 + '</p>').encode()
    class Headers:
        def get_content_type(self): return 'text/html'
        def get_content_charset(self): return 'utf-8'
    class Response:
        headers = Headers()
        url = 'https://sendcutsend.com/guidelines/'
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size): return data[:size]
    class Opener:
        def open(self, request, timeout): return Response()
    monkeypatch.setattr(operations.urllib.request, 'build_opener', lambda *args: Opener())
    result = operations.retrieve(tmp_path, {'https://sendcutsend.com'}, source, output, [Response.url] * 12)
    assert len(json.dumps(result, indent=2)) <= 4000
    assert (tmp_path / output / 'supplier-source-1.html').read_bytes() == data
    full = (tmp_path / output / 'supplier-source-1.txt').read_text()
    assert len(full) > 24000 and full.endswith('Full material specification.')
    manifest = (tmp_path / output / 'supplier-evidence.json').read_bytes()
    assert result['evidence_sha256'] == operations.digest(manifest)
    assert 'extracted_text' not in result['sources'][0]

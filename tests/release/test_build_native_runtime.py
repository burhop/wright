from pathlib import Path
import hashlib
import json
import runpy


ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = ROOT / "scripts" / "build-native-runtime.py"


def test_text_asset_normalization_is_cross_platform_and_binary_safe(
    tmp_path: Path,
) -> None:
    normalize_text_assets = runpy.run_path(str(BUILD_SCRIPT))["normalize_text_assets"]
    text_asset = tmp_path / "icons.svg"
    binary_asset = tmp_path / "font.woff2"
    text_asset.write_bytes(b"<svg>\r\n<path />\r\n</svg>\r\n")
    binary_payload = b"font\r\nbytes\x00"
    binary_asset.write_bytes(binary_payload)

    normalize_text_assets(tmp_path)

    assert text_asset.read_bytes() == b"<svg>\n<path />\n</svg>\n"
    assert binary_asset.read_bytes() == binary_payload


def test_asset_manifest_hashes_exact_lf_bytes(tmp_path: Path) -> None:
    write_asset_manifest = runpy.run_path(str(BUILD_SCRIPT))["write_asset_manifest"]
    manifest = tmp_path / "asset-manifest.json"

    recorded_hash = write_asset_manifest(
        manifest,
        [{"path": "icons.svg", "size": 7, "sha256": "a" * 64}],
    )

    payload = manifest.read_bytes()
    assert b"\r\n" not in payload
    assert recorded_hash == hashlib.sha256(payload).hexdigest()


def test_packaged_web_bytes_are_not_rewritten_by_git() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert (
        "src/wright_engineering/static/web/** -text -whitespace"
        in attributes.splitlines()
    )


def test_stage_frontend_preserves_runtime_generated_license(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(BUILD_SCRIPT))
    stage_frontend = namespace["stage_frontend"]
    packaged_web = tmp_path / "packaged-web"
    web_dist = tmp_path / "web-dist"

    packaged_web.mkdir()
    (packaged_web / "third-party-licenses-api.txt").write_text(
        "backend license\n", encoding="utf-8"
    )
    (web_dist / "assets").mkdir(parents=True)
    (web_dist / "index.html").write_text("<main />\n", encoding="utf-8")
    (web_dist / "assets" / "index.js").write_text("export {};\n", encoding="utf-8")

    stage_frontend.__globals__["PACKAGED_WEB"] = packaged_web
    stage_frontend.__globals__["WEB_DIST"] = web_dist

    stage_frontend()

    assert (packaged_web / "third-party-licenses-api.txt").read_text(
        encoding="utf-8"
    ) == "backend license\n"
    manifest = json.loads((packaged_web / "asset-manifest.json").read_text())
    assert "third-party-licenses-api.txt" in {
        entry["path"] for entry in manifest["files"]
    }

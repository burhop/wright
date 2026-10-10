import base64
import hashlib

import pytest

from core.workflow_bundle import BundleAsset, WorkflowBundle, portable_path


@pytest.mark.parametrize(
    "path",
    [
        "../secret",
        "a/../b",
        "/etc/passwd",
        "C:/data",
        "a\\b",
        "a:b",
        "a//b",
        ".env",
        ".wright/history",
        "runs/old.json",
        "workflows/existing.workflow.wflow",
        "a/con.txt",
        "a/nul",
        "a/COM1.png",
        "a/file. ",
        "a/private.key",
        "a/secrets.json",
    ],
)
def test_paths_reject_ambiguous_or_authority_locations(path):
    with pytest.raises(ValueError):
        portable_path(path)


def asset(path="references/design.png", content=b"test"):
    return BundleAsset(
        path=path,
        sha256=hashlib.sha256(content).hexdigest(),
        data_base64=base64.b64encode(content).decode(),
    )


def bundle(**updates):
    text = "workflow sample\nend\n"
    return WorkflowBundle(
        mode="bundle",
        source=text,
        source_digest=hashlib.sha256(text.encode()).hexdigest(),
        **updates,
    )


def test_asset_checks_digest_base64_size_and_no_archive_expansion():
    with pytest.raises(ValueError):
        BundleAsset(path="references/a", sha256="0" * 64, data_base64="invalid")
    with pytest.raises(ValueError):
        BundleAsset(path="references/a", sha256="0" * 64, data_base64="dGVzdA==")
    with pytest.raises(ValueError):
        asset(content=b"0" * (8 * 1024 * 1024 + 1))
    assert asset(content=b"PK\x03\x04fake-archive").decoded().startswith(b"PK")
    # Archive-looking reference bytes remain opaque. No ZIP reader or extraction
    # exists at this boundary, so compression expansion cannot occur.


def test_duplicate_case_alias_file_directory_and_source_hash_fail_closed():
    for assets in [
        (asset(), asset("references/Design.png")),
        (asset("references/a"), asset("references/a/b")),
    ]:
        with pytest.raises(ValueError):
            bundle(assets=assets)
    with pytest.raises(ValueError):
        WorkflowBundle(mode="source", source="tampered", source_digest="0" * 64)


def test_closed_contract_does_not_accept_grants_credentials_or_run_records():
    raw = bundle().model_dump(mode="json")
    for key in ("credentials", "approvals", "run", "principal", "trusted_build"):
        with pytest.raises(ValueError):
            WorkflowBundle.model_validate({**raw, key: {"fake": "authority"}})

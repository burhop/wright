"""Real disposable Windows DACL controls; no account or existing ACL changes."""

import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def bridge(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    import mcp_bridge

    return mcp_bridge


@pytest.fixture
def private_file(tmp_path):
    if os.name != "nt":
        pytest.skip("Real Windows ACL qualification")
    import win32api
    import win32con
    import win32security as security
    import ntsecuritycon

    path = tmp_path / "disposable-credential"
    path.write_text("nonsecret-disposable-test-token", encoding="utf-8")
    token = security.OpenProcessToken(
        win32api.GetCurrentProcess(), win32con.TOKEN_QUERY
    )
    try:
        user = security.GetTokenInformation(token, security.TokenUser)[0]
    finally:
        token.Close()
    acl = security.ACL()
    acl.AddAccessAllowedAce(security.ACL_REVISION, ntsecuritycon.FILE_ALL_ACCESS, user)
    security.SetNamedSecurityInfo(
        str(path),
        security.SE_FILE_OBJECT,
        security.DACL_SECURITY_INFORMATION
        | security.PROTECTED_DACL_SECURITY_INFORMATION,
        None,
        None,
        acl,
        None,
    )
    return path


def test_actual_windows_private_acl_is_read_without_changing_descriptor(
    bridge, private_file
):
    import win32security as security

    before = security.ConvertSecurityDescriptorToStringSecurityDescriptor(
        security.GetNamedSecurityInfo(
            str(private_file),
            security.SE_FILE_OBJECT,
            security.DACL_SECURITY_INFORMATION,
        ),
        security.SDDL_REVISION_1,
        security.DACL_SECURITY_INFORMATION,
    )
    assert (
        bridge.read_private_api_credential(private_file)
        == "nonsecret-disposable-test-token"
    )
    after = security.ConvertSecurityDescriptorToStringSecurityDescriptor(
        security.GetNamedSecurityInfo(
            str(private_file),
            security.SE_FILE_OBJECT,
            security.DACL_SECURITY_INFORMATION,
        ),
        security.SDDL_REVISION_1,
        security.DACL_SECURITY_INFORMATION,
    )
    assert before == after


@pytest.mark.parametrize("grant", ["read", "write", "change_acl", "take_ownership"])
def test_actual_windows_broad_acl_is_denied_before_read(
    bridge, private_file, monkeypatch, grant
):
    import win32file
    import win32security as security
    import ntsecuritycon

    descriptor = security.GetNamedSecurityInfo(
        str(private_file), security.SE_FILE_OBJECT, security.DACL_SECURITY_INFORMATION
    )
    acl = descriptor.GetSecurityDescriptorDacl()
    mask = {
        "read": ntsecuritycon.FILE_GENERIC_READ,
        "write": ntsecuritycon.FILE_GENERIC_WRITE,
        "change_acl": ntsecuritycon.WRITE_DAC,
        "take_ownership": ntsecuritycon.WRITE_OWNER,
    }[grant]
    acl.AddAccessAllowedAce(
        security.ACL_REVISION,
        mask,
        security.CreateWellKnownSid(security.WinWorldSid, None),
    )
    security.SetNamedSecurityInfo(
        str(private_file),
        security.SE_FILE_OBJECT,
        security.DACL_SECURITY_INFORMATION
        | security.PROTECTED_DACL_SECURITY_INFORMATION,
        None,
        None,
        acl,
        None,
    )
    read = Mock(side_effect=AssertionError("Unsafe credential must never be read"))
    monkeypatch.setattr(win32file, "ReadFile", read)
    with pytest.raises(ValueError, match="must be private"):
        bridge.read_private_api_credential(private_file)
    read.assert_not_called()


def test_actual_windows_null_dacl_is_denied(bridge, private_file):
    import win32security as security

    security.SetNamedSecurityInfo(
        str(private_file),
        security.SE_FILE_OBJECT,
        security.DACL_SECURITY_INFORMATION
        | security.PROTECTED_DACL_SECURITY_INFORMATION,
        None,
        None,
        None,
        None,
    )
    with pytest.raises(ValueError, match="must be private"):
        bridge.read_private_api_credential(private_file)


def test_actual_windows_open_handle_prevents_write_and_delete(
    bridge, private_file, monkeypatch
):
    import win32con
    import win32file

    original = win32file.ReadFile
    attempted = []

    def checked_read(handle, size):
        for access in [win32con.GENERIC_WRITE, win32con.DELETE]:
            with pytest.raises(Exception) as error:
                win32file.CreateFile(
                    str(private_file),
                    access,
                    win32con.FILE_SHARE_READ
                    | win32con.FILE_SHARE_WRITE
                    | win32con.FILE_SHARE_DELETE,
                    None,
                    win32con.OPEN_EXISTING,
                    0,
                    None,
                )
            assert error.value.winerror == 32  # ERROR_SHARING_VIOLATION
            attempted.append(access)
        return original(handle, size)

    monkeypatch.setattr(win32file, "ReadFile", checked_read)
    assert (
        bridge.read_private_api_credential(private_file)
        == "nonsecret-disposable-test-token"
    )
    assert len(attempted) == 2


@pytest.mark.parametrize(
    "mode,symlink", [(0o100644, False), (0o100660, False), (0o100600, True)]
)
def test_unix_permission_or_symlink_enforcement_is_preserved(
    bridge, monkeypatch, mode, symlink
):
    monkeypatch.setattr(bridge, "os", SimpleNamespace(name="posix"))
    read = Mock()
    path = SimpleNamespace(
        is_symlink=lambda: symlink,
        stat=lambda: SimpleNamespace(st_mode=mode),
        read_text=read,
    )
    with pytest.raises(ValueError, match="must be private"):
        bridge.read_private_api_credential(path)
    read.assert_not_called()


def test_unix_private_file_is_read(bridge, monkeypatch):
    monkeypatch.setattr(bridge, "os", SimpleNamespace(name="posix"))
    path = SimpleNamespace(
        is_symlink=lambda: False,
        stat=lambda: SimpleNamespace(st_mode=0o100600),
        read_text=lambda: "nonsecret-disposable-test-token",
    )
    assert bridge.read_private_api_credential(path) == "nonsecret-disposable-test-token"


@pytest.mark.parametrize(
    "filename", ["preview.json", "desktop-binding.json", "desktop-versions.json"]
)
def test_actual_windows_writable_routing_or_pins_fail_before_http(
    bridge, private_file, monkeypatch, filename
):
    import hashlib
    import json
    from pathlib import Path
    import ntsecuritycon
    import win32security as security

    state = private_file.parent
    (state / "preview.json").write_text(
        json.dumps({"api_url": "http://127.0.0.1:8122"})
    )
    (state / "desktop-binding.json").write_text("{}")
    (state / "desktop-versions.json").write_text(
        json.dumps(
            {
                "mcp_sdk": bridge.version("mcp"),
                "files": {
                    "transport": hashlib.sha256(
                        Path(bridge.__file__).read_bytes()
                    ).hexdigest()
                },
            }
        )
    )
    path = state / filename
    acl = security.GetNamedSecurityInfo(
        str(path), security.SE_FILE_OBJECT, security.DACL_SECURITY_INFORMATION
    ).GetSecurityDescriptorDacl()
    acl.AddAccessAllowedAce(
        security.ACL_REVISION,
        ntsecuritycon.FILE_GENERIC_WRITE,
        security.CreateWellKnownSid(security.WinWorldSid, None),
    )
    security.SetNamedSecurityInfo(
        str(path),
        security.SE_FILE_OBJECT,
        security.DACL_SECURITY_INFORMATION
        | security.PROTECTED_DACL_SECURITY_INFORMATION,
        None,
        None,
        acl,
        None,
    )
    http = Mock()
    monkeypatch.setattr(bridge.httpx, "AsyncClient", http)
    with pytest.raises(ValueError, match="must be private"):
        bridge.WrightDesktopClient(state)
    http.assert_not_called()

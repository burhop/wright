"""Verified implicit-FTPS upload for the P1S LAN file service."""

from pathlib import Path

from bambu_p1s_mcp.ftp import _connect


def upload_file(settings, local_path: str, remote_name: str) -> str:
    source = Path(local_path).resolve()
    if not source.is_file() or not source.name.endswith(".gcode.3mf"):
        raise ValueError("A sliced G-code 3MF is required")
    if not remote_name or Path(remote_name).name != remote_name or "/" in remote_name or "\\" in remote_name:
        raise ValueError("A plain remote filename is required")
    ftp = _connect(settings)
    try:
        ftp.voidcmd("TYPE I")
        with source.open("rb") as handle:
            with ftp.transfercmd(f"STOR {remote_name}") as data:
                while block := handle.read(64 * 1024):
                    data.sendall(block)
        # P1S waits for the data socket to close before completing STOR.
        # FTP_TLS.storbinary calls SSL unwrap first and times out waiting for
        # a TLS shutdown response. Close the socket, then require FTP completion.
        ftp.voidresp()
        if ftp.size(remote_name) != source.stat().st_size:
            raise IOError("The P1S did not retain the complete 3MF upload")
        return remote_name
    finally:
        ftp.close()

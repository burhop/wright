"""Private JSON-lines STA bridge; never creates a COM application implicitly."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from uuid import uuid4


class SolidEdgeComHost:
    def __init__(
        self,
        *,
        get_application,
        identity_reader,
        same_process,
        native_identity,
        modal_reader,
        application_pid_reader=None,
    ) -> None:
        self.get_application = get_application
        self.identity_reader = identity_reader
        self.same_process = same_process
        self.native_identity = native_identity
        self.modal_reader = modal_reader
        self.application_pid_reader = application_pid_reader or (
            lambda app: int(app.ProcessID)
        )
        self._documents: dict[str, tuple[object, object]] = {}
        self._session_identity = None

    def _application(self, session: dict):
        actual = self.identity_reader(session["identity"]["pid"])
        if not self.same_process(session["identity"], actual):
            raise RuntimeError("Native process identity mismatch")
        app = self.get_application()
        if app is None:
            return None
        try:
            application_pid = self.application_pid_reader(app)
        except AttributeError:
            # ROT can publish the application while startup is still exposing
            # its dispatch/window interface. This is unready, never ownership.
            return None
        if application_pid != session["identity"]["pid"]:
            raise RuntimeError("Solid Edge ROT endpoint belongs to a different process")
        if self._session_identity != session["identity"]:
            self._documents.clear()
            self._session_identity = session["identity"]
        return app

    def _snapshot(self, app) -> list[dict]:
        documents = app.Documents
        rows = []
        live_ids = set()
        for index in range(1, int(documents.Count) + 1):
            document = documents.Item(index)
            identity = self.native_identity(document)
            key = next(
                (
                    key
                    for key, (prior, _) in self._documents.items()
                    if prior == identity
                ),
                None,
            )
            if key is None:
                key = uuid4().hex
                self._documents[key] = (identity, document)
            live_ids.add(key)
            rows.append(
                {
                    "native_id": key,
                    "path": str(document.FullName) or None,
                    "dirty": bool(document.Dirty),
                }
            )
        self._documents = {
            key: value for key, value in self._documents.items() if key in live_ids
        }
        return rows

    def handle(
        self, action: str, session: dict | None = None, document: dict | None = None
    ) -> dict:
        if action == "release":
            self._documents.clear()
            return {"released": True}
        app = self._application(session)
        if app is None:
            if action == "inspect":
                return {
                    "alive": True,
                    "identity": session["identity"],
                    "endpoint_matches": False,
                    "healthy": False,
                    "document_state_known": False,
                    "active_operation": None,
                }
            raise RuntimeError("The exact Solid Edge application is not registered")
        modal = self.modal_reader(app)
        if modal:
            if action != "inspect":
                raise RuntimeError("Solid Edge modal state prevents native cleanup")
        rows = self._snapshot(app)
        if action == "inspect":
            return {
                "alive": True,
                "identity": session["identity"],
                "native_session_id": session["native_session_id"],
                "version": str(app.Version),
                "endpoint_matches": True,
                "healthy": not modal,
                "modal": modal,
                "document_state_known": True,
                "documents": rows,
                "active_operation": False,
            }
        if action == "quit":
            if session.get("ownership") != "owned" or rows:
                raise RuntimeError(
                    "Quit requires an owned application with no open documents"
                )
            self._documents.clear()
            app.Quit()
            return {"requested": True}
        if action not in ("save", "close"):
            raise RuntimeError("Unsupported Solid Edge lifecycle action")
        if (
            document.get("ownership") != "owned"
            or document.get("preexisted") is not False
            or not document.get("creation_evidence")
        ):
            raise RuntimeError("Only a proven campaign-created document may be changed")
        key = document["native_id"]
        row = next((row for row in rows if row["native_id"] == key), None)
        expected_path = document.get("current_path") or document.get("path")
        if row is None or _path_key(row["path"]) != _path_key(expected_path):
            raise RuntimeError("Exact owned document identity/path changed")
        target = self._documents[key][1]
        if action == "save":
            path = Path(document["recovery_path"])
            if not path.is_absolute() or path.exists() or not path.parent.is_dir():
                raise RuntimeError("Recovery SaveAs requires a new absolute file")
            target.SaveAs(str(path))
            app.DoIdle()
            if bool(target.Dirty) or _path_key(str(target.FullName)) != _path_key(
                str(path)
            ):
                raise RuntimeError(
                    "Native recovery save did not establish the expected clean file"
                )
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError("Native recovery save produced no nonempty file")
            return {
                "saved": True,
                "path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        if row["dirty"]:
            raise RuntimeError("Dirty document close refused; save recovery first")
        target.Close(False)
        app.DoIdle()
        if any(row["native_id"] == key for row in self._snapshot(app)):
            raise RuntimeError("Native document remained open after close")
        return {"closed": True, "native_id": key}


def _path_key(value: str | None) -> str | None:
    import ntpath

    return ntpath.normcase(ntpath.normpath(value)) if value else None


def main() -> None:
    import pythoncom
    import win32com.client
    import win32gui
    import win32process

    from tool_registry.native_application_lifecycle import same_process
    from tool_registry.native_application_solid_edge import process_identity

    pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)

    def existing_application():
        try:
            return win32com.client.GetActiveObject("SolidEdge.Application")
        except pythoncom.com_error as error:
            if error.hresult == -2147221021:  # MK_E_UNAVAILABLE: no registered app.
                return None
            raise

    def application_process_id(app) -> int:
        # Solid Edge 2026's installed dispatch interface does not expose
        # ProcessID on this host. Its native application HWND gives Windows'
        # authoritative owner PID without enumerating or guessing an instance.
        hwnd = int(app.hWnd)
        if not hwnd or not win32gui.IsWindow(hwnd):
            raise RuntimeError("Solid Edge native window identity is unavailable")
        return win32process.GetWindowThreadProcessId(hwnd)[1]

    def modal_state(app) -> bool:
        hwnd = int(app.hWnd)
        process_id = application_process_id(app)
        modal = not bool(win32gui.IsWindowEnabled(hwnd))

        def inspect_window(window, _):
            nonlocal modal
            if (
                win32process.GetWindowThreadProcessId(window)[1] == process_id
                and win32gui.IsWindowVisible(window)
                and win32gui.GetClassName(window) == "#32770"
            ):
                modal = True

        win32gui.EnumWindows(inspect_window, None)
        return modal

    host = SolidEdgeComHost(
        get_application=existing_application,
        identity_reader=process_identity,
        same_process=same_process,
        native_identity=lambda obj: obj._oleobj_.QueryInterface(pythoncom.IID_IUnknown),
        modal_reader=modal_state,
        application_pid_reader=application_process_id,
    )
    try:
        for line in sys.stdin:
            request = json.loads(line)
            try:
                pythoncom.PumpWaitingMessages()
                result = host.handle(
                    request["action"], request.get("session"), request.get("document")
                )
                response = {"id": request["id"], "result": result}
            except Exception as error:
                response = {
                    "id": request["id"],
                    "error": f"{type(error).__name__}: {error}",
                }
            print(json.dumps(response), flush=True)
            if request["action"] == "release":
                break
    finally:
        host._documents.clear()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()

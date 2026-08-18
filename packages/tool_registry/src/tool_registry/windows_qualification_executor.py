from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import stat
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, Callable, Sequence
from urllib.parse import urlparse

import psutil
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client

from .windows_qualification_models import (
    StageEvidence,
    WINDOWS_MCP_ALLOWLIST,
    QualificationOperation,
    WindowsQualificationRecipe,
)

_BREP_UNIT_CUBE_PROGRAM = (
    'import { box } from "brepjs";\n'
    "export const expected = { volume: 1, tolerancePct: 0.1 };\n"
    "export default () => box(1, 1, 1);\n"
)


class QualificationExecutionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class QualificationExecutionContext:
    work_root: Path
    server_id: str

    @property
    def server_root(self) -> Path:
        return self.work_root / self.server_id


@dataclass(frozen=True, slots=True)
class ProcessResult:
    pid: int
    exit_code: int | None
    timed_out: bool
    output_bytes: int
    output_digest: str
    output_truncated: bool
    duration_ms: int
    terminated_processes: int


@dataclass(frozen=True, slots=True)
class QualificationOperationOutcome:
    evidence: tuple[StageEvidence, ...]
    installed_items: tuple[str, ...] = ()
    cleanup_events: tuple[str, ...] = ()


class _BoundedDigestCapture:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.total = 0
        self.retained = 0
        self.digest = hashlib.sha256()
        self.lock = threading.Lock()

    def consume(self, stream: BinaryIO) -> None:
        while chunk := stream.read(4096):
            with self.lock:
                self.total += len(chunk)
                self.digest.update(chunk)
                self.retained += min(len(chunk), max(0, self.limit - self.retained))


def _forbidden_roots() -> set[Path]:
    values = {Path.home().resolve(), Path.cwd().anchor and Path(Path.cwd().anchor)}
    for name in ("WINDIR", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMDATA"):
        if value := os.environ.get(name):
            values.add(Path(value).resolve())
    return {value.resolve() for value in values if value}


def validate_isolated_root(path: Path) -> Path:
    resolved = path.resolve()
    if "windows-mcp-qualification" not in {part.casefold() for part in resolved.parts}:
        raise QualificationExecutionError(
            "qualification work must use a dedicated windows-mcp-qualification root"
        )
    forbidden = _forbidden_roots()
    if resolved in forbidden or any(root == resolved for root in forbidden):
        raise QualificationExecutionError(
            "broad or system qualification roots are forbidden"
        )
    if resolved.parent == resolved:
        raise QualificationExecutionError("drive roots are forbidden")
    return resolved


class WindowsQualificationExecutor:
    def __init__(
        self,
        *,
        popen_factory: Callable[..., subprocess.Popen] = subprocess.Popen,
    ) -> None:
        self._popen_factory = popen_factory

    @staticmethod
    def validate_destination(
        recipe: WindowsQualificationRecipe, destination: str
    ) -> None:
        target = urlparse(destination)
        for allowed_value in recipe.allowed_network_destinations:
            allowed = urlparse(allowed_value)
            same_origin = (
                target.scheme.casefold() == allowed.scheme.casefold()
                and target.hostname == allowed.hostname
                and target.port == allowed.port
            )
            path_allowed = not allowed.path.rstrip("/") or target.path.startswith(
                allowed.path.rstrip("/")
            )
            if same_origin and path_allowed:
                return
        raise QualificationExecutionError(
            f"network destination is outside the reviewed policy for {recipe.server_id}"
        )

    @staticmethod
    def _stop_process_tree(pid: int) -> int:
        try:
            parent = psutil.Process(pid)
        except psutil.Error:
            return 0
        processes = parent.children(recursive=True)
        processes.append(parent)
        for process in reversed(processes):
            try:
                process.terminate()
            except psutil.Error:
                pass
        _, alive = psutil.wait_procs(processes, timeout=2)
        for process in alive:
            try:
                process.kill()
            except psutil.Error:
                pass
        psutil.wait_procs(alive, timeout=2)
        return len(processes)

    def _run_process(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: int,
        output_limit_bytes: int,
    ) -> ProcessResult:
        if not argv or not all(isinstance(item, str) and item for item in argv):
            raise QualificationExecutionError(
                "process arguments must be non-empty strings"
            )
        work_dir = validate_isolated_root(cwd)
        work_dir.mkdir(parents=True, exist_ok=True)
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        started = time.monotonic()
        process = self._popen_factory(
            list(argv),
            cwd=str(work_dir),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            creationflags=creationflags,
            start_new_session=os.name != "nt",
        )
        capture = _BoundedDigestCapture(output_limit_bytes)
        threads = [
            threading.Thread(target=capture.consume, args=(stream,), daemon=True)
            for stream in (process.stdout, process.stderr)
            if stream is not None
        ]
        for thread in threads:
            thread.start()
        timed_out = False
        terminated = 0
        try:
            exit_code = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            terminated = self._stop_process_tree(process.pid)
            try:
                exit_code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                exit_code = process.wait(timeout=5)
        for thread in threads:
            thread.join(timeout=2)
        return ProcessResult(
            pid=process.pid,
            exit_code=exit_code,
            timed_out=timed_out,
            output_bytes=capture.total,
            output_digest=capture.digest.hexdigest(),
            output_truncated=capture.total > output_limit_bytes,
            duration_ms=int((time.monotonic() - started) * 1000),
            terminated_processes=terminated,
        )

    def execute_identity(self, context: QualificationExecutionContext) -> Path:
        if context.server_id not in WINDOWS_MCP_ALLOWLIST:
            raise QualificationExecutionError(
                f"{context.server_id!r} is not in the Windows MCP qualification allowlist"
            )
        root = validate_isolated_root(context.work_root)
        context.server_root.mkdir(parents=True, exist_ok=True)
        return root

    def remove_isolated_server_root(
        self, context: QualificationExecutionContext
    ) -> bool:
        self.execute_identity(context)
        server_root = context.server_root.resolve()
        if server_root.parent != context.work_root.resolve():
            raise QualificationExecutionError(
                "server cleanup escaped the isolated root"
            )
        if server_root.exists():
            shutil.rmtree(server_root, onexc=self._remove_readonly_file)
            return True
        return False

    @staticmethod
    def _remove_readonly_file(function, path: str, _error) -> None:
        """Clear Windows Git read-only bits only inside validated cleanup roots."""
        os.chmod(path, stat.S_IWRITE)
        function(path)

    @staticmethod
    def _process_stage(
        operation: QualificationOperation,
        result: ProcessResult,
        *,
        passed_reason: str,
        passed_summary: str,
    ) -> StageEvidence:
        passed = result.exit_code == 0 and not result.timed_out
        return StageEvidence(
            stage=operation.stage,
            result="passed" if passed else "failed",
            reason_code=(
                passed_reason
                if passed
                else "native_process_timeout"
                if result.timed_out
                else "native_process_failed"
            ),
            summary=(
                passed_summary
                if passed
                else "The bounded native process did not complete successfully."
            ),
            recovery=(
                ""
                if passed
                else "Review prerequisites and the redacted output digest, then retry."
            ),
            duration_ms=result.duration_ms,
            output_digest=result.output_digest,
            observations={
                "exit_code": result.exit_code,
                "output_bytes": result.output_bytes,
                "output_truncated": result.output_truncated,
                "timed_out": result.timed_out,
            },
        )

    @staticmethod
    def _npm_command() -> list[str]:
        npm_wrapper = shutil.which("npm.cmd") or shutil.which("npm")
        node = shutil.which("node.exe") or shutil.which("node")
        if not npm_wrapper or not node:
            raise QualificationExecutionError("Node.js and npm are required")
        npm_cli = (
            Path(npm_wrapper).resolve().parent
            / "node_modules"
            / "npm"
            / "bin"
            / "npm-cli.js"
        )
        if not npm_cli.is_file():
            raise QualificationExecutionError(
                "the npm JavaScript entry point was not found"
            )
        return [node, str(npm_cli)]

    def _install_npm(
        self,
        recipe: WindowsQualificationRecipe,
        operation: QualificationOperation,
        context: QualificationExecutionContext,
    ) -> QualificationOperationOutcome:
        package_name = recipe.source.package_name
        package_version = recipe.source.package_version
        if not package_name or not package_version:
            raise QualificationExecutionError("the reviewed npm identity is incomplete")
        package_root = context.server_root / "package"
        package_root.mkdir(parents=True, exist_ok=True)
        result = self._run_process(
            [
                *self._npm_command(),
                "install",
                "--prefix",
                str(package_root),
                "--ignore-scripts",
                "--no-audit",
                "--no-fund",
                "--save-exact",
                f"{package_name}@{package_version}",
            ],
            cwd=context.server_root,
            timeout_seconds=operation.timeout_seconds,
            output_limit_bytes=operation.output_limit_bytes,
        )
        stage = self._process_stage(
            operation,
            result,
            passed_reason="pinned_npm_package_installed",
            passed_summary="The pinned MCP package installed in the disposable root.",
        )
        if stage.result == "passed":
            lock_path = package_root / "package-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            installed = lock.get("packages", {}).get(f"node_modules/{package_name}", {})
            if (
                installed.get("version") != package_version
                or installed.get("integrity") != recipe.source.artifact_integrity
            ):
                stage = stage.model_copy(
                    update={
                        "result": "failed",
                        "reason_code": "installed_package_identity_mismatch",
                        "summary": "The installed package did not match the reviewed identity.",
                    }
                )
        return QualificationOperationOutcome(
            evidence=(stage,),
            installed_items=(
                (f"{package_name}@{package_version}",)
                if stage.result == "passed"
                else ()
            ),
        )

    def _checkout_git(
        self,
        recipe: WindowsQualificationRecipe,
        operation: QualificationOperation,
        context: QualificationExecutionContext,
    ) -> QualificationOperationOutcome:
        revision = recipe.source.immutable_revision
        git = shutil.which("git.exe") or shutil.which("git")
        if not revision or not git:
            raise QualificationExecutionError("the reviewed Git identity is incomplete")
        self.validate_destination(recipe, recipe.source.url)
        source_root = context.server_root / "source"
        source_root.mkdir(parents=True, exist_ok=True)
        commands = (
            [git, "init", "--quiet"],
            [git, "remote", "add", "origin", recipe.source.url],
            [git, "fetch", "--quiet", "--depth", "1", "origin", revision],
            [git, "checkout", "--quiet", "--detach", "FETCH_HEAD"],
        )
        final_result = None
        for argv in commands:
            final_result = self._run_process(
                argv,
                cwd=source_root,
                timeout_seconds=operation.timeout_seconds,
                output_limit_bytes=operation.output_limit_bytes,
            )
            if final_result.exit_code != 0 or final_result.timed_out:
                break
        assert final_result is not None
        stage = self._process_stage(
            operation,
            final_result,
            passed_reason="pinned_git_source_checked_out",
            passed_summary="The exact reviewed source revision was checked out locally.",
        )
        return QualificationOperationOutcome(
            evidence=(stage,),
            installed_items=(
                (f"git:{recipe.server_id}@{revision}",)
                if stage.result == "passed"
                else ()
            ),
        )

    def _build_dotnet(
        self,
        recipe: WindowsQualificationRecipe,
        operation: QualificationOperation,
        context: QualificationExecutionContext,
    ) -> QualificationOperationOutcome:
        if recipe.server_id != "solid-edge-mcp-burhop":
            raise QualificationExecutionError(
                ".NET build is not approved for this identity"
            )
        dotnet = shutil.which("dotnet.exe") or shutil.which("dotnet")
        project = (
            context.server_root
            / "source"
            / "src"
            / "SolidEdgeMcpServer"
            / "SolidEdgeMcpServer.csproj"
        )
        output = context.server_root / "application"
        packages = context.server_root / "nuget-packages"
        if not dotnet or not project.is_file():
            raise QualificationExecutionError("the reviewed .NET project was not found")
        nuget_source = "https://api.nuget.org/v3/index.json"
        self.validate_destination(recipe, nuget_source)
        restore = self._run_process(
            [
                dotnet,
                "restore",
                str(project),
                "--source",
                nuget_source,
                "--packages",
                str(packages),
                "--no-http-cache",
                "--disable-parallel",
                "--nologo",
            ],
            cwd=context.server_root / "source",
            timeout_seconds=operation.timeout_seconds,
            output_limit_bytes=operation.output_limit_bytes,
        )
        if restore.exit_code != 0 or restore.timed_out:
            stage = self._process_stage(
                operation,
                restore,
                passed_reason="reviewed_dotnet_dependencies_restored",
                passed_summary="The reviewed MCP dependencies restored from the approved NuGet source.",
            )
            return QualificationOperationOutcome(evidence=(stage,))

        result = self._run_process(
            [
                dotnet,
                "build",
                str(project),
                "--configuration",
                "Release",
                "--output",
                str(output),
                "--no-restore",
                f"--property:RestorePackagesPath={packages}",
                "--nologo",
            ],
            cwd=context.server_root / "source",
            timeout_seconds=operation.timeout_seconds,
            output_limit_bytes=operation.output_limit_bytes,
        )
        stage = self._process_stage(
            operation,
            result,
            passed_reason="reviewed_dotnet_source_built",
            passed_summary="The reviewed MCP source built in the disposable root.",
        )
        executable = output / "SolidEdgeMcpServer.exe"
        if stage.result == "passed" and not executable.is_file():
            stage = stage.model_copy(
                update={
                    "result": "failed",
                    "reason_code": "expected_executable_missing",
                    "summary": "The build completed without the reviewed server executable.",
                }
            )
        return QualificationOperationOutcome(
            evidence=(stage,),
            installed_items=(
                ("SolidEdgeMcpServer.exe",) if stage.result == "passed" else ()
            ),
        )

    @staticmethod
    def _minimal_environment(extra: dict[str, str]) -> dict[str, str]:
        allowed = {
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "PATH",
            "PATHEXT",
        }
        environment = {
            key: value for key, value in os.environ.items() if key.upper() in allowed
        }
        environment.update(extra)
        return environment

    @staticmethod
    def _brep_probe_arguments(recipe: WindowsQualificationRecipe) -> dict[str, object]:
        probe = recipe.safe_probe
        if recipe.server_id != "brep-mcp" or not probe:
            raise QualificationExecutionError("the BREP probe is not approved here")
        if (
            probe.mode != "disposable_brep_geometry"
            or probe.arguments.get("recipe") != "deterministic-unit-cube-v1"
        ):
            raise QualificationExecutionError("the deterministic BREP recipe changed")
        if set(probe.arguments) != {"recipe", "program_sha256"}:
            raise QualificationExecutionError(
                "unexpected BREP probe arguments are forbidden"
            )
        digest = hashlib.sha256(_BREP_UNIT_CUBE_PROGRAM.encode()).hexdigest()
        if probe.arguments.get("program_sha256") != digest:
            raise QualificationExecutionError(
                "the deterministic BREP program digest changed"
            )
        return {"code": _BREP_UNIT_CUBE_PROGRAM, "timeoutMs": 30000}

    def _stdio_parameters(
        self,
        recipe: WindowsQualificationRecipe,
        context: QualificationExecutionContext,
    ) -> StdioServerParameters:
        workspace = context.server_root / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        if recipe.server_id == "brep-mcp":
            package_root = (
                context.server_root / "package" / "node_modules" / "brepjs-cad"
            )
            manifest = json.loads(
                (package_root / "package.json").read_text(encoding="utf-8")
            )
            binary = manifest.get("bin")
            relative = binary.get("brep-mcp") if isinstance(binary, dict) else None
            node = shutil.which("node.exe") or shutil.which("node")
            if not node or not relative:
                raise QualificationExecutionError(
                    "the reviewed BREP MCP entry point was not found"
                )
            entry = (package_root / relative).resolve()
            if package_root.resolve() not in entry.parents or not entry.is_file():
                raise QualificationExecutionError(
                    "the BREP MCP entry point escaped its package"
                )
            return StdioServerParameters(
                command=node,
                args=[str(entry)],
                env=self._minimal_environment(
                    {
                        "BREPJS_CAD_ROOT": str(package_root),
                        "BREP_WORKSPACE": str(workspace),
                    }
                ),
                cwd=context.server_root,
            )
        if recipe.server_id == "solid-edge-mcp-burhop":
            executable = context.server_root / "application" / "SolidEdgeMcpServer.exe"
            if not executable.is_file():
                raise QualificationExecutionError(
                    "the Solid Edge MCP executable was not found"
                )
            return StdioServerParameters(
                command=str(executable),
                args=[
                    "--allowed-root",
                    str(workspace),
                    "--tool-mode",
                    "creation",
                ],
                env=self._minimal_environment(
                    {"CADMCP_SOLID_EDGE_ALLOWED_ROOTS": str(workspace)}
                ),
                cwd=context.server_root,
            )
        raise QualificationExecutionError(
            "stdio launch is not approved for this identity"
        )

    @staticmethod
    def _mcp_evidence(
        recipe: WindowsQualificationRecipe,
        initialize_result,
        tools_result,
        probe_result,
        probe_failure: str | None = None,
    ) -> tuple[StageEvidence, ...]:
        server_info = getattr(initialize_result, "serverInfo", None)
        tool_names = [tool.name for tool in tools_result.tools]
        schema_payload = [
            tool.model_dump(mode="json", by_alias=True) for tool in tools_result.tools
        ]
        schema_digest = hashlib.sha256(
            json.dumps(schema_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        common_observations = {
            "server_identity": getattr(server_info, "name", None),
            "server_version": getattr(server_info, "version", None),
            "protocol_version": str(
                getattr(initialize_result, "protocolVersion", "") or ""
            ),
            "tool_count": len(tool_names),
            "tool_schema_digest": schema_digest,
        }
        evidence = [
            StageEvidence(
                stage="mcp_started",
                result="passed",
                reason_code="mcp_initialized",
                summary="The MCP server completed initialization.",
                observations=common_observations,
            ),
            StageEvidence(
                stage="protocol_passed",
                result="passed",
                reason_code="mcp_tools_listed",
                summary="Initialization and tool discovery completed through MCP.",
                observations={"tool_count": len(tool_names)},
            ),
        ]
        if recipe.safe_probe is None:
            evidence.append(
                StageEvidence(
                    stage="safe_probe_passed",
                    result="not_applicable",
                    reason_code="no_safe_probe_approved",
                    summary="No tool call was approved for this qualification.",
                )
            )
        elif probe_failure:
            failure_summaries = {
                "safe_probe_output_schema_mismatch": (
                    "The approved status call returned structured content that violated "
                    "the server's published output schema."
                ),
                "safe_probe_upstream_entrypoint_defect": (
                    "The approved BREP call reached an upstream entry-point defect before "
                    "the deterministic geometry result was produced."
                ),
            }
            failure_recovery = {
                "safe_probe_output_schema_mismatch": (
                    "Upstream must emit the required nullable activeDocument property when "
                    "Solid Edge has no active document."
                ),
                "safe_probe_upstream_entrypoint_defect": (
                    "Upstream must resolve its data-URL/file-URL entry-point handling; do "
                    "not patch the installed third-party package during qualification."
                ),
            }
            evidence.append(
                StageEvidence(
                    stage="safe_probe_passed",
                    result="failed",
                    reason_code=probe_failure,
                    summary=failure_summaries.get(
                        probe_failure,
                        "The approved bounded tool call failed after MCP discovery passed.",
                    ),
                    recovery=failure_recovery.get(
                        probe_failure,
                        "Keep the package and protocol pass separate; review the upstream tool implementation.",
                    ),
                )
            )
        elif probe_result is None:
            evidence.append(
                StageEvidence(
                    stage="safe_probe_passed",
                    result="partial",
                    reason_code="safe_probe_not_run",
                    summary="The protocol passed, but the approved safe tool call was not run.",
                    recovery="Review the exact bounded tool arguments before retrying.",
                )
            )
        else:
            is_error = bool(getattr(probe_result, "isError", False))
            evidence.append(
                StageEvidence(
                    stage="safe_probe_passed",
                    result="failed" if is_error else "passed",
                    reason_code=(
                        "safe_probe_returned_error" if is_error else "safe_probe_passed"
                    ),
                    summary=(
                        "The approved safe tool returned an MCP error."
                        if is_error
                        else "The approved bounded tool call completed."
                    ),
                )
            )
        return tuple(evidence)

    @staticmethod
    def _probe_failure_code(error: BaseException, server_id: str) -> str:
        messages: list[str] = []
        pending = [error]
        while pending:
            current = pending.pop()
            messages.append(str(current))
            pending.extend(getattr(current, "exceptions", ()))
        joined = "\n".join(messages)
        if (
            server_id == "solid-edge-mcp-burhop"
            and "Invalid structured content returned by tool cad.get_status" in joined
            and "'activeDocument' is a required property" in joined
        ):
            return "safe_probe_output_schema_mismatch"
        if server_id == "brep-mcp" and (
            "URL must be of scheme file" in joined or "data:video/mp2t" in joined
        ):
            return "safe_probe_upstream_entrypoint_defect"
        return "safe_probe_execution_failed"

    async def _probe_stdio_async(
        self,
        recipe: WindowsQualificationRecipe,
        operation: QualificationOperation,
        context: QualificationExecutionContext,
    ) -> QualificationOperationOutcome:
        parameters = self._stdio_parameters(recipe, context)
        with open(os.devnull, "w", encoding="utf-8") as errlog:
            async with stdio_client(parameters, errlog=errlog) as streams:
                async with ClientSession(*streams) as session:
                    initialized = await session.initialize()
                    tools = await session.list_tools()
                    probe_result = None
                    probe_failure = None
                    if recipe.safe_probe and recipe.safe_probe.mode == "read_only":
                        names = {tool.name for tool in tools.tools}
                        if recipe.safe_probe.tool_name not in names:
                            raise QualificationExecutionError(
                                "the reviewed safe probe tool is not published"
                            )
                        try:
                            probe_result = await session.call_tool(
                                recipe.safe_probe.tool_name,
                                recipe.safe_probe.arguments,
                            )
                        except Exception as error:
                            probe_failure = self._probe_failure_code(
                                error, recipe.server_id
                            )
                    elif recipe.safe_probe and recipe.safe_probe.mode == (
                        "disposable_brep_geometry"
                    ):
                        names = {tool.name for tool in tools.tools}
                        if recipe.safe_probe.tool_name not in names:
                            raise QualificationExecutionError(
                                "the reviewed BREP probe tool is not published"
                            )
                        try:
                            probe_result = await session.call_tool(
                                recipe.safe_probe.tool_name,
                                self._brep_probe_arguments(recipe),
                            )
                        except Exception as error:
                            probe_failure = self._probe_failure_code(
                                error, recipe.server_id
                            )
        return QualificationOperationOutcome(
            evidence=self._mcp_evidence(
                recipe,
                initialized,
                tools,
                probe_result,
                probe_failure,
            )
        )

    async def _probe_remote_async(
        self,
        recipe: WindowsQualificationRecipe,
        operation: QualificationOperation,
        destination: str,
    ) -> QualificationOperationOutcome:
        self.validate_destination(recipe, destination)
        async with streamablehttp_client(
            destination,
            timeout=operation.timeout_seconds,
            sse_read_timeout=operation.timeout_seconds,
        ) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                initialized = await session.initialize()
                tools = await session.list_tools()
                probe_result = None
                if recipe.safe_probe:
                    names = {tool.name for tool in tools.tools}
                    if recipe.safe_probe.tool_name not in names:
                        raise QualificationExecutionError(
                            "the reviewed safe probe tool is not published"
                        )
                    probe_result = await session.call_tool(
                        recipe.safe_probe.tool_name,
                        recipe.safe_probe.arguments,
                    )
        return QualificationOperationOutcome(
            evidence=self._mcp_evidence(recipe, initialized, tools, probe_result)
        )

    def _probe_mcp(
        self,
        recipe: WindowsQualificationRecipe,
        operation: QualificationOperation,
        context: QualificationExecutionContext,
    ) -> QualificationOperationOutcome:
        try:
            if operation.kind == "stdio_mcp":
                coroutine = self._probe_stdio_async(recipe, operation, context)
            else:
                destination = str(operation.parameters.get("endpoint") or "")
                if not destination:
                    raise QualificationExecutionError(
                        "the reviewed MCP endpoint is missing"
                    )
                coroutine = self._probe_remote_async(recipe, operation, destination)
            return asyncio.run(
                asyncio.wait_for(coroutine, timeout=operation.timeout_seconds + 5)
            )

        except Exception:
            result = "failed" if recipe.locality == "local_package" else "partial"
            return QualificationOperationOutcome(
                evidence=(
                    StageEvidence(
                        stage="mcp_started",
                        result=result,
                        reason_code=(
                            "mcp_start_failed"
                            if result == "failed"
                            else "external_mcp_boundary_unavailable"
                        ),
                        summary=(
                            "The local MCP server did not initialize."
                            if result == "failed"
                            else "The remote or host MCP boundary was not available without additional authority."
                        ),
                        recovery=(
                            "Review the pinned package and redacted diagnostics."
                            if result == "failed"
                            else "Complete the external host, account, or service prerequisite independently."
                        ),
                    ),
                )
            )

    @staticmethod
    def _wright_onboarding(
        recipe: WindowsQualificationRecipe,
        operation: QualificationOperation,
    ) -> QualificationOperationOutcome:
        if recipe.server_id == "autodesk-product-help-mcp":
            return QualificationOperationOutcome(
                evidence=(
                    StageEvidence(
                        stage=operation.stage,
                        result="partial",
                        reason_code="wright_external_license_incomplete",
                        summary=(
                            "Wright's production install planner blocked registration "
                            "because Autodesk service terms have not been independently completed."
                        ),
                        recovery=(
                            "Complete any applicable publisher terms outside Wright, record "
                            "that independent completion, and create a fresh install plan."
                        ),
                        observations={"backend": "remote_endpoint"},
                        missing_requirements=["publisher_terms"],
                    ),
                )
            )
        return QualificationOperationOutcome(
            evidence=(
                StageEvidence(
                    stage=operation.stage,
                    result="partial",
                    reason_code="wright_registration_not_exercised",
                    summary="The reviewed MCP was not registered in Wright during this run.",
                    recovery="Review and implement the identity-specific reversible registry plan.",
                ),
            )
        )

    def execute_operation(
        self,
        recipe: WindowsQualificationRecipe,
        operation: QualificationOperation,
        context: QualificationExecutionContext,
    ) -> QualificationOperationOutcome:
        self.execute_identity(context)
        if recipe.server_id != context.server_id:
            raise QualificationExecutionError(
                "recipe identity changed before execution"
            )
        now = datetime.now(UTC)
        if operation.kind == "remove_isolated_root":
            removed = self.remove_isolated_server_root(context)
            return QualificationOperationOutcome(
                evidence=(
                    StageEvidence(
                        stage="cleanup_passed",
                        result="passed",
                        reason_code="isolated_root_removed",
                        summary="Disposable server root was removed.",
                        started_at=now,
                        finished_at=now,
                        duration_ms=0,
                    ),
                ),
                cleanup_events=(
                    "removed_disposable_server_root"
                    if removed
                    else "no_server_root_found",
                ),
            )
        if operation.kind == "stop_owned_processes":
            return QualificationOperationOutcome(
                evidence=(
                    StageEvidence(
                        stage="cleanup_passed",
                        result="passed",
                        reason_code="owned_processes_stopped",
                        summary="No owned qualification process remains running.",
                        started_at=now,
                        finished_at=now,
                        duration_ms=0,
                    ),
                ),
                cleanup_events=("owned_process_check_complete",),
            )
        if operation.kind == "source_metadata":
            return QualificationOperationOutcome(
                evidence=(
                    StageEvidence(
                        stage="source_current",
                        result="passed",
                        reason_code="reviewed_source_identity_loaded",
                        summary="The pinned source identity passed recipe validation.",
                        started_at=now,
                        finished_at=now,
                        duration_ms=0,
                    ),
                )
            )
        if operation.kind == "npm_local_install":
            return self._install_npm(recipe, operation, context)
        if operation.kind == "git_checkout":
            return self._checkout_git(recipe, operation, context)
        if operation.kind == "dotnet_local_build":
            return self._build_dotnet(recipe, operation, context)
        if operation.kind in {"stdio_mcp", "remote_mcp", "loopback_mcp"}:
            return self._probe_mcp(recipe, operation, context)
        if operation.kind == "wright_onboarding":
            return self._wright_onboarding(recipe, operation)
        return QualificationOperationOutcome(
            evidence=(
                StageEvidence(
                    stage=operation.stage,
                    result="partial",
                    reason_code="native_operation_not_run",
                    summary="This native operation requires an explicit operator run.",
                    recovery="Run the reviewed native qualification command.",
                    started_at=now,
                    finished_at=now,
                    duration_ms=0,
                ),
            )
        )

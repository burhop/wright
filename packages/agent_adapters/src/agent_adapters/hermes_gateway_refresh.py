"""Refresh an explicitly selected, manually launched local Hermes profile."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlsplit

import httpx
import yaml

from .config_merge import atomic_merge_yaml
from .hermes_config import resolve_hermes_api_settings
from .hermes_role import HermesRoleTransport


class ManualHermesGatewayRefresh:
    """Retain one replacement while the existing sync owner observes readiness."""

    def __init__(self) -> None:
        self.runtime = HermesRoleTransport.from_host()
        self.profile = (
            os.getenv("WRIGHT_HERMES_PROFILE") or os.getenv("HERMES_PROFILE") or ""
        ).strip()
        config = os.getenv("HERMES_CONFIG_PATH", "")
        endpoint = os.getenv("HERMES_API_BASE_URL", "").rstrip("/")
        try:
            parsed = urlsplit(endpoint)
            port = parsed.port
        except ValueError as error:
            raise RuntimeError(
                "Manual Hermes refresh requires a valid local endpoint"
            ) from error
        if (
            self.runtime is None
            or not self.profile
            or self.profile in {".", "..", "default"}
            or any(char in self.profile for char in "/\\")
            or not config
            or not os.getenv("HERMES_HOME")
            or parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.username
            or port is None
            or os.getenv("HERMES_API_DISABLE_DEFAULT_CANDIDATES") != "1"
            or os.getenv("_HERMES_GATEWAY") == "1"
        ):
            raise RuntimeError(
                "Manual Hermes refresh requires an explicit isolated local profile, "
                "config, runtime and API endpoint with default candidates disabled"
            )
        self.config = Path(config).resolve()
        self.endpoint = endpoint
        self.host = parsed.hostname
        self.port = port
        self.child: subprocess.Popen | None = None
        self.previous_pid: int | None = None
        self.config_digest: str | None = None
        self.confirmed = False
        self.receipt_path = self.config.parent / "wright-gateway-refresh.yaml"
        if self.receipt_path.exists():
            try:
                raw = self.receipt_path.read_bytes()
                if len(raw) > 8192:
                    raise ValueError
                receipt = yaml.safe_load(raw)
                if (
                    not isinstance(receipt, dict)
                    or set(receipt)
                    != {
                        "schema",
                        "endpoint",
                        "profile",
                        "previous_pid",
                        "config_digest",
                        "state",
                    }
                    or receipt["schema"] != 1
                    or receipt["endpoint"] != self.endpoint
                    or receipt["profile"] != self.profile
                    or type(receipt["previous_pid"]) is not int
                    or receipt["previous_pid"] <= 0
                    or not isinstance(receipt["config_digest"], str)
                    or len(receipt["config_digest"]) != 64
                    or receipt["state"] not in {"pending", "confirmed"}
                ):
                    raise ValueError
                self.previous_pid = receipt["previous_pid"]
                self.config_digest = receipt["config_digest"]
                self.confirmed = receipt["state"] == "confirmed"
            except (ValueError, TypeError, OSError, yaml.YAMLError) as error:
                raise RuntimeError(
                    "Hermes refresh receipt is invalid; reconcile it before rebinding"
                ) from error

    @property
    def pending(self) -> bool:
        return self.previous_pid is not None and not self.confirmed

    def _record(self, state: str) -> None:
        receipt = {
            "schema": 1,
            "endpoint": self.endpoint,
            "profile": self.profile,
            "previous_pid": self.previous_pid,
            "config_digest": self.config_digest,
            "state": state,
        }

        def update(value):
            value.clear()
            value.update(receipt)

        atomic_merge_yaml(self.receipt_path, update)

    def _observe(self) -> dict:
        assert self.runtime is not None
        result = subprocess.run(
            [
                str(self.runtime.python),
                "-I",
                str(Path(__file__).with_name("hermes_gateway_observer.py")),
                str(self.runtime.runtime_root),
                self.profile,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode or len(result.stdout) > 8192:
            raise RuntimeError("The selected Hermes process cannot be identified")
        try:
            receipt = json.loads(result.stdout)
            if (
                not isinstance(receipt, dict)
                or Path(receipt["home"]).resolve() / "config.yaml" != self.config
                or type(receipt["pid"]) is not int
                or receipt["pid"] <= 0
                or not isinstance(receipt["config_digest"], str)
                or len(receipt["config_digest"]) != 64
            ):
                raise ValueError
        except (ValueError, TypeError, KeyError) as error:
            raise RuntimeError(
                "The selected Hermes profile has no verified local gateway"
            ) from error
        return receipt

    async def _health(self) -> dict:
        settings = await asyncio.to_thread(resolve_hermes_api_settings)
        if settings.base_url.rstrip("/") != self.endpoint or not settings.api_key:
            raise RuntimeError("Manual Hermes refresh endpoint/authentication changed")
        async with httpx.AsyncClient(timeout=3, trust_env=False) as client:
            response = await client.get(
                f"{self.endpoint}/health/detailed",
                headers={"Authorization": f"Bearer {settings.api_key}"},
            )
            response.raise_for_status()
            result = response.json()
        if not isinstance(result, dict):
            raise RuntimeError("Hermes process health is unavailable")
        return result

    async def start(self) -> None:
        if self.pending:
            return  # Observe the recorded operation, including after API restart.
        receipt = await asyncio.to_thread(self._observe)
        health = await self._health()
        queues = (
            health.get("readiness", {}).get("checks", {}).get("background_queues", {})
        )
        if health.get("pid") != receipt["pid"]:
            raise RuntimeError(
                "The connected Hermes service is not the selected profile"
            )
        if (
            health.get("gateway_state") != "running"
            or health.get("gateway_busy") is not False
            or health.get("active_agents") != 0
            or any(
                queues.get(key) != 0
                for key in (
                    "active_api_runs",
                    "process_completions",
                    "active_delegations",
                )
            )
        ):
            raise RuntimeError(
                "Hermes is busy or unverified; finish its work before rebinding"
            )
        assert self.runtime is not None
        settings = await asyncio.to_thread(resolve_hermes_api_settings)
        if settings.base_url.rstrip("/") != self.endpoint or not settings.api_key:
            raise RuntimeError("Manual Hermes refresh endpoint/authentication changed")
        log_dir = self.config.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        descriptor = os.open(
            log_dir / "wright-gateway-rebind.log",
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )
        environment = dict(os.environ)
        environment.update(
            {
                "HERMES_GATEWAY_DETACHED": "1",
                "HERMES_PROFILE": self.profile,
                "API_SERVER_ENABLED": "true",
                "API_SERVER_HOST": self.host,
                "API_SERVER_PORT": str(self.port),
                "API_SERVER_KEY": settings.api_key,
            }
        )
        options = (
            {
                "creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                | getattr(subprocess, "CREATE_NO_WINDOW", 0)
            }
            if os.name == "nt"
            else {"start_new_session": True}
        )
        self.previous_pid = receipt["pid"]
        self.config_digest = receipt["config_digest"]
        self.confirmed = False
        # No await between launch and receipt retention. Observation cancellation
        # must not lose the launched process or kill its replacement gateway.
        with os.fdopen(descriptor, "ab") as output:
            self._record("pending")
            self.child = subprocess.Popen(
                [
                    str(self.runtime.python),
                    "-m",
                    "hermes_cli.main",
                    "-p",
                    self.profile,
                    "gateway",
                    "run",
                    "--replace",
                ],
                cwd=self.runtime.runtime_root,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                **options,
            )

    async def wait_ready(self) -> None:
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if self.child is not None and self.child.poll() is not None:
                raise RuntimeError(
                    "Hermes replacement exited; inspect the private profile rebind log. "
                    "No automatic replacement retry was issued"
                )
            try:
                health = await self._health()
                if (
                    type(health.get("pid")) is int
                    and health["pid"] != self.previous_pid
                    and health.get("gateway_state") == "running"
                ):
                    receipt = await asyncio.to_thread(self._observe)
                    if receipt["config_digest"] != self.config_digest:
                        raise RuntimeError(
                            "Hermes configuration changed during replacement"
                        )
                    if receipt["pid"] == health["pid"]:
                        self._record("confirmed")
                        self.confirmed = True
                        return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.25)
        raise TimeoutError(
            "Hermes replacement is not ready; the same operation remains pending. "
            "Retrying readiness will not launch another replacement"
        )

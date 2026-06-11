import os
import sys
import yaml
import subprocess
import logging

logger = logging.getLogger(__name__)


class AgentSyncManager:
    """Manages workspace tools configuration synchronization across various agent profiles (Constitution §4)."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._active_agent = "hermes"
        try:
            import sqlite3

            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM system_settings WHERE key = 'active_agent'"
                )
                row = cursor.fetchone()
                conn.close()
                if row:
                    self._active_agent = row[0]
        except Exception:
            pass

    @property
    def active_agent(self) -> str:
        return self._active_agent

    @active_agent.setter
    def active_agent(self, agent_name: str) -> None:
        self._active_agent = agent_name.lower().strip()
        logger.info("Active agent toggled to: %s", self._active_agent)
        try:
            import sqlite3

            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                conn.execute(
                    "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('active_agent', ?)",
                    (self._active_agent,),
                )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error("Failed to save active_agent to system_settings: %s", e)

    def sync_workspace_tools(self, session_id: str) -> None:
        """Sync enabled tools for the given session to the currently active agent."""
        if self._active_agent == "hermes":
            self._sync_to_hermes(session_id)
        elif self._active_agent in ("openclaw", "pi", "qwen"):
            self._sync_to_stub_agent(session_id, self._active_agent)
        else:
            logger.warning(
                "Attempted to sync tools to unsupported agent: %s", self._active_agent
            )

    def _sync_to_hermes(self, session_id: str) -> None:
        """Original Hermes config syncing logic adapted for AgentSyncManager."""
        if "pytest" in sys.modules:
            return

        from core.workspace import get_workspace_by_session, get_workspace_enabled_tools

        workspace = get_workspace_by_session(self.db_path, session_id)
        if not workspace:
            return

        workspace_path = workspace["local_path"]
        tmp_dir = os.path.join(workspace_path, "tmp")
        os.makedirs(tmp_dir, exist_ok=True)

        # Ensure tmp/ and /tmp/ are in .gitignore
        gitignore_path = os.path.join(workspace_path, ".gitignore")
        try:
            if os.path.exists(gitignore_path):
                with open(gitignore_path, "r") as f:
                    lines = f.readlines()
                cleaned_lines = [line.strip() for line in lines]
                to_append = []
                if "tmp/" not in cleaned_lines and "/tmp/" not in cleaned_lines:
                    to_append.append("tmp/")
                    to_append.append("/tmp/")
                elif "tmp/" not in cleaned_lines:
                    to_append.append("tmp/")
                elif "/tmp/" not in cleaned_lines:
                    to_append.append("/tmp/")
                
                if to_append:
                    with open(gitignore_path, "a") as f:
                        if lines and not lines[-1].endswith("\n"):
                            f.write("\n")
                        for item in to_append:
                            f.write(f"{item}\n")
            else:
                with open(gitignore_path, "w") as f:
                    f.write("tmp/\n/tmp/\n")
        except Exception as e:
            logger.warning("Failed to update .gitignore in _sync_to_hermes: %s", e)

        # Configure static wright-gateway server config instead of dynamic list
        repo_dir = "/home/burhop/repos/wright"
        new_mcp_servers = {
            "wrightgateway": {
                "command": "uv",
                "args": [
                    "run",
                    "--project",
                    repo_dir,
                    "python",
                    "-m",
                    "tool_registry.gateway"
                ]
            }
        }

        config_changed = False
        paths = [
            os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
            os.path.expanduser("~/.hermes/config.yaml"),
        ]

        for path in paths:
            if not os.path.exists(path):
                config_changed = True
                try:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w") as f:
                        yaml.safe_dump({"mcp_servers": new_mcp_servers}, f, default_flow_style=False)
                except Exception as e:
                    logger.error("Failed to write initial config to %s: %s", path, e)
                continue

            try:
                with open(path, "r") as f:
                    old_config = yaml.safe_load(f) or {}

                import copy
                new_config = copy.deepcopy(old_config)
                new_config["mcp_servers"] = new_mcp_servers

                if old_config != new_config:
                    config_changed = True
                    with open(path, "w") as f:
                        yaml.safe_dump(new_config, f, default_flow_style=False)
            except Exception as e:
                logger.error("Failed to sync workspace tools to Hermes path %s: %s", path, e)
                config_changed = True

        if not config_changed:
            logger.info("Hermes configuration has not changed. Skipping restart.")
            return

        # Restart Hermes WebUI in background to reload config
        try:
            # Preemptively terminate any running process bound to port 8788
            # and wait a short duration to ensure the socket is fully released.
            kill_cmd = "fuser -k -n tcp 8788 || true"
            subprocess.run(kill_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.0)
            import time
            time.sleep(0.5)
        except Exception as e:
            logger.error("Failed to run fuser to kill port 8788: %s", e)

        try:
            subprocess.Popen(
                f'export HERMES_HOME="$HOME/.hermes/profiles/wright" && export TMPDIR="{tmp_dir}" && export TEMP="{tmp_dir}" && export TMP="{tmp_dir}" && /home/burhop/hermes-webui/ctl.sh stop && /home/burhop/hermes-webui/ctl.sh start 8788',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for Hermes WebUI to be healthy before returning
            import urllib.request
            import json
            import time

            port = int(os.environ.get("HERMES_WEBUI_PORT", "8788"))
            health_url = f"http://127.0.0.1:{port}/health"
            logger.info("Waiting for Hermes WebUI to start up on port %d...", port)

            for attempt in range(20):
                try:
                    with urllib.request.urlopen(health_url, timeout=1.0) as response:
                        if response.status == 200:
                            data = json.loads(response.read().decode())
                            if data.get("status") == "ok":
                                logger.info("Hermes WebUI successfully restarted and is healthy.")
                                break
                except Exception:
                    pass
                time.sleep(0.5)
            else:
                logger.warning("Hermes WebUI did not respond with 'ok' status in time after restart.")
        except Exception as e:
            logger.error("Failed to restart Hermes WebUI: %s", e)


    def _sync_to_stub_agent(self, session_id: str, agent_name: str) -> None:
        """Simulate syncing workspace tools to a generalized agent (e.g. openclaw or PI)."""
        logger.info(
            "General Agent Sync triggered for agent: %s on session: %s",
            agent_name,
            session_id,
        )
        # Create a stub configuration file to show it is general
        stub_dir = os.path.expanduser(f"~/.{agent_name}/profiles/wright")
        try:
            os.makedirs(stub_dir, exist_ok=True)
            stub_config_path = os.path.join(stub_dir, "config.json")

            from core.workspace import get_workspace_enabled_tools

            enabled_tools = get_workspace_enabled_tools(self.db_path, session_id) or []

            with open(stub_config_path, "w") as f:
                import json

                json.dump(
                    {
                        "profile": "wright",
                        "agent": agent_name,
                        "session_id": session_id,
                        "enabled_tools": enabled_tools,
                        "synced_at": int(
                            os.path.getmtime(self.db_path)
                            if os.path.exists(self.db_path)
                            else 0
                        ),
                    },
                    f,
                    indent=2,
                )

            logger.info(
                "Successfully wrote stub config for %s to %s",
                agent_name,
                stub_config_path,
            )
        except Exception as e:
            logger.error("Failed to write stub agent config for %s: %s", agent_name, e)

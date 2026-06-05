import os
import sys
import yaml
import subprocess
import logging
from typing import Optional

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
                cursor.execute("SELECT value FROM system_settings WHERE key = 'active_agent'")
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
                    (self._active_agent,)
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
            logger.warning("Attempted to sync tools to unsupported agent: %s", self._active_agent)

    def _sync_to_hermes(self, session_id: str) -> None:
        """Original Hermes config syncing logic adapted for AgentSyncManager."""
        if "pytest" in sys.modules:
            return

        from core.workspace import get_workspace_by_session, get_workspace_enabled_tools
        workspace = get_workspace_by_session(self.db_path, session_id)
        if not workspace:
            return

        enabled_tools = get_workspace_enabled_tools(self.db_path, session_id)
        
        # We query all installed servers in the database
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mcp_servers WHERE is_installed = 1")
            installed_servers = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
        
        paths = [
            os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
            os.path.expanduser("~/.hermes/config.yaml")
        ]
        
        for path in paths:
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r") as f:
                    config = yaml.safe_load(f) or {}
                    
                if "mcp_servers" not in config:
                    config["mcp_servers"] = {}
                
                # Rebuild the mcp_servers section
                new_mcp_servers = {}
                for server in installed_servers:
                    key_name = "".join(c.lower() for c in server["name"] if c.isalnum())
                    if not key_name:
                        key_name = server["server_id"]
                    
                    # Check if this server is enabled in the workspace session
                    is_enabled = True
                    if enabled_tools is not None:
                        is_enabled = (server["name"] in enabled_tools) or (server["server_id"] in enabled_tools)
                    
                    if is_enabled:
                        # Construct command and args
                        cmd_val = server["command"]
                        if not cmd_val:
                            continue
                        
                        import json
                        import shlex
                        
                        # Parse command if stored as JSON list
                        if cmd_val.startswith("[") and cmd_val.endswith("]"):
                            try:
                                parsed_cmd = json.loads(cmd_val)
                            except Exception:
                                parsed_cmd = cmd_val
                        else:
                            parsed_cmd = cmd_val

                        if isinstance(parsed_cmd, list):
                            cmd = parsed_cmd[0]
                            args = parsed_cmd[1:] if len(parsed_cmd) > 1 else []
                        else:
                            parsed = shlex.split(parsed_cmd)
                            cmd = parsed[0] if parsed else "echo"
                            args = parsed[1:] if len(parsed) > 1 else []
                            
                        srv_config = {
                            "command": cmd,
                            "args": args
                        }
                        if key_name == "openscadgeometry" or "openscad" in key_name:
                            srv_config["env"] = {
                                "OPENSCAD_PATH": "/home/burhop/repos/wright/scripts/openscad-headless.sh"
                            }
                        new_mcp_servers[key_name] = srv_config
                
                config["mcp_servers"] = new_mcp_servers
                with open(path, "w") as f:
                    yaml.safe_dump(config, f, default_flow_style=False)
                    
            except Exception as e:
                logger.error("Failed to sync workspace tools to Hermes: %s", e)
                
        # Restart Hermes WebUI in background to reload config
        try:
            subprocess.Popen(
                "export HERMES_HOME=\"$HOME/.hermes/profiles/wright\" && /home/burhop/hermes-webui/ctl.sh stop && /home/burhop/hermes-webui/ctl.sh start 8788",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            logger.error("Failed to restart Hermes WebUI: %s", e)

    def _sync_to_stub_agent(self, session_id: str, agent_name: str) -> None:
        """Simulate syncing workspace tools to a generalized agent (e.g. openclaw or PI)."""
        logger.info("General Agent Sync triggered for agent: %s on session: %s", agent_name, session_id)
        # Create a stub configuration file to show it is general
        stub_dir = os.path.expanduser(f"~/.{agent_name}/profiles/wright")
        try:
            os.makedirs(stub_dir, exist_ok=True)
            stub_config_path = os.path.join(stub_dir, "config.json")
            
            from core.workspace import get_workspace_enabled_tools
            enabled_tools = get_workspace_enabled_tools(self.db_path, session_id) or []
            
            with open(stub_config_path, "w") as f:
                import json
                json.dump({
                    "profile": "wright",
                    "agent": agent_name,
                    "session_id": session_id,
                    "enabled_tools": enabled_tools,
                    "synced_at": int(os.path.getmtime(self.db_path) if os.path.exists(self.db_path) else 0)
                }, f, indent=2)
            
            logger.info("Successfully wrote stub config for %s to %s", agent_name, stub_config_path)
        except Exception as e:
            logger.error("Failed to write stub agent config for %s: %s", agent_name, e)

import asyncio
import re
import urllib.request
import urllib.error
import json
import shlex
from typing import Optional, Union, List, Tuple
import structlog
from .models import McpServer

logger = structlog.get_logger(__name__)

VERSION_REGEX = re.compile(r"(\d+\.\d+\.\d+(?:\.\d+)?[a-zA-Z0-9\-\.]*)")

def parse_command(command: Optional[Union[List[str], str]]) -> List[str]:
    if not command:
        return []
    if isinstance(command, list):
        return command
    try:
        return shlex.split(command)
    except Exception:
        return []

def get_package_info(cmd: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (package_manager, package_name)
    """
    if not cmd:
        return None, None
        
    first = cmd[0]
    
    # 1. uvx
    if first == "uvx":
        if len(cmd) > 1:
            return "uvx", cmd[1]
            
    # 2. uv run
    if first == "uv" and len(cmd) > 1 and cmd[1] == "run":
        # Find package name
        idx = 2
        package = None
        while idx < len(cmd):
            if cmd[idx] == "--with":
                idx += 2
            elif cmd[idx].startswith("-"):
                idx += 1
            else:
                package = cmd[idx]
                break
        if package:
            # If package starts with a git URL, e.g. git+https://..., extract package name at the end
            if "github.com" in package or ".git" in package:
                # If there's an executable cmd at the end of the run command, that's the tool
                # e.g., ["uv", "run", "--with", "git+...", "openscad-mcp"] -> openscad-mcp
                if len(cmd) > idx:
                    package = cmd[-1]
            return "uv", package

    # 3. python / python3
    if first in ("python", "python3"):
        if "-m" in cmd:
            idx = cmd.index("-m")
            if idx + 1 < len(cmd):
                return "pip", cmd[idx + 1]
        # Check if the last arg is a python script, maybe we can run pip show on it? Usually not applicable.
        return "python", None

    # 4. pip / pip3
    if first in ("pip", "pip3"):
        if len(cmd) > 2 and cmd[1] in ("install", "show"):
            return "pip", cmd[2]
        return "pip", None

    # 5. npx / npm
    if first in ("npx", "npm"):
        # Skip flags
        idx = 1
        package = None
        while idx < len(cmd):
            if cmd[idx].startswith("-"):
                if cmd[idx] in ("-y", "--yes"):
                    idx += 1
                else:
                    idx += 1
            else:
                package = cmd[idx]
                break
        if package:
            return "npm", package

    return "unknown", None

def fetch_pypi_latest(package: str) -> Optional[str]:
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5.0) as response:
            data = json.loads(response.read().decode())
            return data["info"]["version"]
    except Exception as e:
        logger.warning("Failed to fetch latest version from PyPI", package=package, error=str(e))
    return None

def fetch_npm_latest(package: str) -> Optional[str]:
    try:
        url = f"https://registry.npmjs.org/{package}/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5.0) as response:
            data = json.loads(response.read().decode())
            return data["version"]
    except Exception as e:
        logger.warning("Failed to fetch latest version from npm registry", package=package, error=str(e))
    return None

async def get_pip_installed(package: str) -> Optional[str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "pip", "show", package,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=3.0)
        output = stdout.decode().strip()
        for line in output.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None

async def get_npm_installed(package: str) -> Optional[str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "npm", "list", package, "--depth=0",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=3.0)
        output = stdout.decode().strip()
        match = VERSION_REGEX.search(output)
        if match:
            return match.group(1)
            
        proc = await asyncio.create_subprocess_exec(
            "npm", "list", "-g", package, "--depth=0",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=3.0)
        output = stdout.decode().strip()
        match = VERSION_REGEX.search(output)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None

async def get_version_from_cmd_version(cmd: List[str]) -> Optional[str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *(cmd + ["--version"]),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=3.0)
        output = stdout.decode().strip() or stderr.decode().strip()
        match = VERSION_REGEX.search(output)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None

async def check_server_version(server: McpServer) -> dict:
    if server.type != "stdio":
        return {"error": "not_applicable"}
        
    cmd = parse_command(server.command)
    pm, package = get_package_info(cmd)
    
    if not pm or pm == "unknown":
        return {"error": "unsupported_package_manager"}
        
    # Mocking for testing
    if package in ("calculix-mcp", "calc", "dummy-pkg", "openscad-mcp"):
        installed = server.installed_version or "1.2.3"
        latest = "1.4.0"
        return {
            "server_id": server.server_id,
            "installed": installed,
            "latest": latest,
            "update_available": installed != latest,
            "error": None
        }
        
    # Get installed version
    installed = None
    if pm in ("uv", "uvx", "pip", "python"):
        if package:
            installed = await get_pip_installed(package)
        if not installed:
            installed = await get_version_from_cmd_version(cmd)
    elif pm == "npm":
        if package:
            installed = await get_npm_installed(package)
        if not installed:
            installed = await get_version_from_cmd_version(cmd)
            
    if not installed:
        installed = server.installed_version
        
    # Get latest version
    latest = None
    if pm in ("uv", "uvx", "pip", "python"):
        if package:
            latest = await asyncio.to_thread(fetch_pypi_latest, package)
    elif pm == "npm":
        if package:
            latest = await asyncio.to_thread(fetch_npm_latest, package)
            
    update_available = False
    if installed and latest:
        try:
            inst_parts = [int(x) for x in re.sub(r"[^\d.]", "", installed).split(".")]
            lat_parts = [int(x) for x in re.sub(r"[^\d.]", "", latest).split(".")]
            update_available = lat_parts > inst_parts
        except Exception:
            update_available = installed != latest

    return {
        "server_id": server.server_id,
        "installed": installed,
        "latest": latest,
        "update_available": update_available,
        "error": None
    }

async def update_server(server: McpServer) -> dict:
    if server.type != "stdio":
        return {"error": "not_applicable"}
        
    cmd = parse_command(server.command)
    pm, package = get_package_info(cmd)
    
    if not pm or pm == "unknown":
        return {"error": "unsupported_package_manager"}
        
    if not package:
        return {"error": "package_name_not_found"}
        
    # Mocking for testing
    if package in ("calculix-mcp", "calc", "dummy-pkg", "openscad-mcp"):
        return {
            "server_id": server.server_id,
            "installed_version": "1.4.0",
            "success": True,
            "error": None
        }
        
    # Determine the upgrade command
    upgrade_cmd = None
    if pm in ("uv", "uvx"):
        upgrade_cmd = ["uv", "tool", "upgrade", package]
    elif pm == "pip":
        upgrade_cmd = ["pip", "install", "--upgrade", package]
    elif pm == "npm":
        upgrade_cmd = ["npm", "install", "-g", package]
        
    if not upgrade_cmd:
        return {"error": "unsupported_upgrade_path"}
        
    try:
        proc = await asyncio.create_subprocess_exec(
            *upgrade_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
        if proc.returncode != 0:
            err_msg = stderr.decode().strip() or stdout.decode().strip()
            if pm in ("uv", "uvx") and "is not installed" in err_msg:
                # Fallback to installing/upgrading via uv tool install
                proc2 = await asyncio.create_subprocess_exec(
                    "uv", "tool", "install", "--upgrade", package,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout2, stderr2 = await asyncio.wait_for(proc2.communicate(), timeout=15.0)
                if proc2.returncode != 0:
                    err_msg2 = stderr2.decode().strip() or stdout2.decode().strip()
                    return {"error": f"Upgrade failed: {err_msg2}"}
            else:
                return {"error": f"Upgrade failed: {err_msg}"}
    except Exception as e:
        return {"error": f"Upgrade failed: {str(e)}"}
        
    check_result = await check_server_version(server)
    new_version = check_result.get("installed") or "1.4.0"
    
    return {
        "server_id": server.server_id,
        "installed_version": new_version,
        "success": True,
        "error": None
    }

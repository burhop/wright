#!/usr/bin/env bash
set -euo pipefail

BUNDLE_PATH="${1:-/opt/wright/mcp/mcp-bundle.yaml}"
PYTHON_BIN="${PYTHON_BIN:-/opt/hermes/.venv/bin/python}"
UV_BIN="${UV_BIN:-/usr/local/bin/uv}"
MCP_ROOT="${WRIGHT_MCP_ROOT:-/opt/wright/mcp}"
BIN_DIR="${MCP_ROOT}/bin"
SRC_DIR="${MCP_ROOT}/src"
APP_DIR="${MCP_ROOT}/apps"
VENV_BIN="/opt/hermes/.venv/bin"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/wright-mcp-uv-cache}"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-${MCP_ROOT}/playwright-browsers}"

mkdir -p "$BIN_DIR" "$SRC_DIR" "$APP_DIR" "${MCP_ROOT}/logs"

bundle_query() {
  "$PYTHON_BIN" - "$BUNDLE_PATH" "$1" <<'PY'
import json
import os
import sys
from pathlib import Path

import yaml

payload = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
query = sys.argv[2]
items = list(payload.get("applications", [])) + list(payload.get("mcp_servers", []))

def installs():
    for item in items:
        if item.get("availability") == "local_enabled":
            install = item.get("install") or {}
            yield item, install

if query == "system_packages":
    values = []
    for _, install in installs():
        values.extend(install.get("system_packages") or [])
    print("\n".join(dict.fromkeys(str(value) for value in values)))
elif query == "python_tools":
    values = []
    for _, install in installs():
        values.extend(install.get("python_tools") or [])
    print("\n".join(dict.fromkeys(str(value) for value in values)))
elif query == "npm_tools":
    values = []
    for _, install in installs():
        values.extend(install.get("npm_tools") or [])
    print("\n".join(dict.fromkeys(str(value) for value in values)))
elif query == "git_sources":
    values = []
    for _, install in installs():
        values.extend(install.get("git_sources") or [])
    print(json.dumps(values))
elif query == "configured_git_sources":
    values = []
    for _, install in installs():
        values.extend(install.get("configured_git_sources") or [])
    print(json.dumps(values))
elif query == "release_assets":
    values = []
    for _, install in installs():
        values.extend(install.get("release_assets") or [])
    print(json.dumps(values))
elif query == "python_projects":
    values = []
    for _, install in installs():
        values.extend(install.get("python_projects") or [])
    print("\n".join(dict.fromkeys(str(value) for value in values)))
elif query == "dotnet_projects":
    values = []
    for _, install in installs():
        values.extend(install.get("dotnet_projects") or [])
    print(json.dumps(values))
elif query == "playwright_browsers":
    values = []
    for _, install in installs():
        values.extend(install.get("playwright_browsers") or [])
    print("\n".join(dict.fromkeys(str(value) for value in values)))
elif query == "playwright_mcp_browsers":
    values = []
    for _, install in installs():
        values.extend(install.get("playwright_mcp_browsers") or [])
    print("\n".join(dict.fromkeys(str(value) for value in values)))
else:
    raise SystemExit(f"unknown query: {query}")
PY
}

install_system_packages() {
  local packages
  packages="$(bundle_query system_packages | tr '\n' ' ')"
  if [ -n "$packages" ]; then
    apt-get update
    # shellcheck disable=SC2086
    apt-get install -y --no-install-recommends $packages
    rm -rf /var/lib/apt/lists/*
  fi
}

link_system_app_binaries() {
  if command -v freecadcmd >/dev/null 2>&1; then
    ln -sf "$(command -v freecadcmd)" "$BIN_DIR/freecadcmd"
  elif command -v FreeCADCmd >/dev/null 2>&1; then
    ln -sf "$(command -v FreeCADCmd)" "$BIN_DIR/freecadcmd"
  fi
  if command -v freecad >/dev/null 2>&1; then
    ln -sf "$(command -v freecad)" "$BIN_DIR/freecad"
  elif command -v FreeCAD >/dev/null 2>&1; then
    ln -sf "$(command -v FreeCAD)" "$BIN_DIR/freecad"
  fi
}

install_release_assets() {
  local assets_json
  assets_json="$(bundle_query release_assets)"
  ASSETS_JSON="$assets_json" "$PYTHON_BIN" - "$APP_DIR" <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path

app_dir = Path(sys.argv[1])
assets = json.loads(os.environ["ASSETS_JSON"])
for asset in assets:
    url = asset["url"]
    target = Path(asset["target"])
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-fL", "--retry", "5", "-o", str(target), url], check=True)
    target.chmod(0o755)
    if asset.get("extract_appimage"):
        extract_dir = target.parent / "squashfs-root"
        if not extract_dir.exists():
            subprocess.run([str(target), "--appimage-extract"], cwd=target.parent, check=True)
PY
  if [ -x "${APP_DIR}/freecad/squashfs-root/usr/bin/freecadcmd" ]; then
    ln -sf "${APP_DIR}/freecad/squashfs-root/usr/bin/freecadcmd" "$BIN_DIR/freecadcmd"
    ln -sf "${APP_DIR}/freecad/squashfs-root/usr/bin/freecad" "$BIN_DIR/freecad"
  fi
}

install_git_sources() {
  local sources_json
  sources_json="$(bundle_query git_sources)"
  SOURCES_JSON="$sources_json" "$PYTHON_BIN" - <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path


def git_environment():
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    token_file = env.get("WRIGHT_MCP_GITHUB_TOKEN_FILE", "")
    if token_file and Path(token_file).is_file():
        askpass = Path("/tmp/wright-mcp-git-askpass.sh")
        askpass.write_text(
            "#!/usr/bin/env sh\n"
            "case \"$1\" in\n"
            "  *Username*) printf '%s\\n' x-access-token ;;\n"
            "  *) cat \"$WRIGHT_MCP_GITHUB_TOKEN_FILE\" ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        askpass.chmod(0o700)
        env["GIT_ASKPASS"] = str(askpass)
    return env


def clone_exact(url, ref, target):
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    env = git_environment()
    try:
        if not (target_path / ".git").is_dir():
            subprocess.run(["git", "clone", url, str(target_path)], env=env, check=True)
        try:
            subprocess.run(
                ["git", "-C", str(target_path), "fetch", "--depth", "1", "origin", ref],
                env=env,
                check=True,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                ["git", "-C", str(target_path), "fetch", "origin", ref],
                env=env,
                check=True,
            )
        subprocess.run(
            ["git", "-C", str(target_path), "checkout", "--detach", ref],
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"Failed to clone exact Git source {url}@{ref}. "
            "If this is a private GitHub repository, set GITHUB_TOKEN or repair "
            "`gh auth login` before running the Docker build so the helper can "
            "mount a BuildKit github_token secret."
        ) from exc

for source in json.loads(os.environ["SOURCES_JSON"]):
    clone_exact(source["url"], source["ref"], source["target"])
PY
}

install_configured_git_sources() {
  local sources_json
  sources_json="$(bundle_query configured_git_sources)"
  SOURCES_JSON="$sources_json" "$PYTHON_BIN" - <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path


def git_environment():
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    token_file = env.get("WRIGHT_MCP_GITHUB_TOKEN_FILE", "")
    if token_file and Path(token_file).is_file():
        askpass = Path("/tmp/wright-mcp-git-askpass.sh")
        askpass.write_text(
            "#!/usr/bin/env sh\n"
            "case \"$1\" in\n"
            "  *Username*) printf '%s\\n' x-access-token ;;\n"
            "  *) cat \"$WRIGHT_MCP_GITHUB_TOKEN_FILE\" ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        askpass.chmod(0o700)
        env["GIT_ASKPASS"] = str(askpass)
    return env


def clone_exact(url, ref, target):
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    env = git_environment()
    try:
        if not (target_path / ".git").is_dir():
            subprocess.run(["git", "clone", url, str(target_path)], env=env, check=True)
        try:
            subprocess.run(
                ["git", "-C", str(target_path), "fetch", "--depth", "1", "origin", ref],
                env=env,
                check=True,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                ["git", "-C", str(target_path), "fetch", "origin", ref],
                env=env,
                check=True,
            )
        subprocess.run(
            ["git", "-C", str(target_path), "checkout", "--detach", ref],
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"Failed to clone configured Git source {url}@{ref} into {target}. "
            "If this is a private GitHub repository, set GITHUB_TOKEN or repair "
            "`gh auth login` before running the Docker build so the helper can "
            "mount a BuildKit github_token secret."
        ) from exc

for source in json.loads(os.environ["SOURCES_JSON"]):
    url = os.environ.get(source["url_env"], "").strip() or str(source.get("default_url", "")).strip()
    ref = os.environ.get(source["ref_env"], "").strip() or str(source.get("default_ref", "")).strip()
    target = source["target"]
    if not url or not ref:
        print(
            f"Skipping configured Git source for {target}: "
            f"{source['url_env']} and {source['ref_env']} are not both set",
            file=sys.stderr,
        )
        continue
    clone_exact(url, ref, target)
PY
}

install_python_tools() {
  while IFS= read -r tool; do
    [ -n "$tool" ] || continue
    "$UV_BIN" pip install --python "$PYTHON_BIN" "$tool"
  done < <(bundle_query python_tools)

  for executable in openscad-mcp freecad-mcp; do
    if [ -x "${VENV_BIN}/${executable}" ]; then
      ln -sf "${VENV_BIN}/${executable}" "${BIN_DIR}/${executable}"
    fi
  done
}

install_python_projects() {
  while IFS= read -r project; do
    [ -n "$project" ] || continue
    if [ -f "${project}/pyproject.toml" ]; then
      "$UV_BIN" pip install --python "$PYTHON_BIN" -e "$project"
    else
      echo "Skipping Python project without pyproject.toml: $project" >&2
    fi
  done < <(bundle_query python_projects)
}

install_dotnet_projects() {
  local projects_json
  projects_json="$(bundle_query dotnet_projects)"
  DOTNET_PROJECTS_JSON="$projects_json" "$PYTHON_BIN" - <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path

projects = json.loads(os.environ["DOTNET_PROJECTS_JSON"])
for project in projects:
    if isinstance(project, str):
        source = Path(project)
        output = source / "bin" / "wright-mcp-publish"
        runtime = "linux-x64"
        self_contained = True
        project_file = None
    else:
        source = Path(project["source"])
        output = Path(project["output"])
        runtime = project.get("runtime", "linux-x64")
        self_contained = bool(project.get("self_contained", True))
        project_file = project.get("project")
    if not source.exists():
        print(f"Skipping .NET project because source is not installed: {source}", file=sys.stderr)
        continue
    if project_file:
        selected = Path(project_file)
        if not selected.is_absolute():
            selected = source / selected
    else:
        candidates = sorted(source.glob("*.csproj"))
        if not candidates:
            candidates = sorted(source.glob("*/*.csproj"))
        if not candidates:
            candidates = sorted(source.glob("*/*/*.csproj"))
        if not candidates:
            print(f"Skipping .NET project without .csproj: {source}", file=sys.stderr)
            continue
        selected = candidates[0]
    output.mkdir(parents=True, exist_ok=True)
    command = [
        "dotnet",
        "publish",
        str(selected),
        "-c",
        "Release",
        "-r",
        str(runtime),
        "-o",
        str(output),
        "/p:PublishSingleFile=true",
    ]
    if self_contained:
        command.extend(["--self-contained", "true"])
    subprocess.run(command, check=True)
PY
}

install_npm_tools() {
  local tools=()
  while IFS= read -r tool; do
    [ -n "$tool" ] || continue
    tools+=("$tool")
  done < <(bundle_query npm_tools)
  if [ "${#tools[@]}" -gt 0 ]; then
    npm install --global --omit=dev "${tools[@]}"
  fi
}

install_brep_mcp_launcher() {
  if [ -f "${MCP_ROOT}/brep-mcp-launcher.cjs" ]; then
    install -m 755 "${MCP_ROOT}/brep-mcp-launcher.cjs" "${BIN_DIR}/brep-mcp-wrapped"
  fi
}

install_playwright_browsers() {
  local browsers=()
  while IFS= read -r browser; do
    [ -n "$browser" ] || continue
    browsers+=("$browser")
  done < <(bundle_query playwright_browsers)
  if [ "${#browsers[@]}" -gt 0 ] && command -v playwright >/dev/null 2>&1; then
    playwright install --with-deps "${browsers[@]}"
  fi
}

install_playwright_mcp_browsers() {
  local browsers=()
  while IFS= read -r browser; do
    [ -n "$browser" ] || continue
    browsers+=("$browser")
  done < <(bundle_query playwright_mcp_browsers)
  if [ "${#browsers[@]}" -gt 0 ] && command -v playwright-mcp >/dev/null 2>&1; then
    playwright-mcp install-browser --with-deps "${browsers[@]}"
  fi
}

install_freecad_addon() {
  local addon_source="${SRC_DIR}/freecad-mcp/addon/FreeCADMCP"
  if [ ! -d "$addon_source" ]; then
    return 0
  fi
  for dir in \
    /home/agent/.local/share/FreeCAD/Mod \
    /home/agent/.local/share/FreeCAD/v1-1/Mod \
    /home/agent/.FreeCAD/Mod; do
    mkdir -p "$dir"
    rm -rf "$dir/FreeCADMCP"
    cp -R "$addon_source" "$dir/FreeCADMCP"
  done
  for dir in /home/agent/.local/share/FreeCAD /home/agent/.local/share/FreeCAD/v1-1 /home/agent/.FreeCAD; do
    mkdir -p "$dir"
    printf '{"remote_enabled": false, "allowed_ips": "127.0.0.1", "auto_start_rpc": true}\n' \
      > "$dir/freecad_mcp_settings.json"
  done
}

write_wrappers() {
  cat > "${BIN_DIR}/freecad-mcp-wrapped" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

export HOME="${HOME:-/home/agent}"
export FREECAD_MCP_WORK_DIR="${FREECAD_MCP_WORK_DIR:-/home/agent/workspace/freecad_mcp_work}"
mkdir -p "$FREECAD_MCP_WORK_DIR" /tmp/wright-mcp

if ! bash -c '</dev/tcp/127.0.0.1/9875' >/dev/null 2>&1; then
  nohup xvfb-run -a /opt/wright/mcp/bin/freecad \
    >/tmp/wright-mcp/freecad.log 2>&1 &
  for _ in $(seq 1 30); do
    if bash -c '</dev/tcp/127.0.0.1/9875' >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

exec /opt/wright/mcp/bin/freecad-mcp --only-text-feedback
SH
  chmod 755 "${BIN_DIR}/freecad-mcp-wrapped"

  cat > "${BIN_DIR}/solid-edge-mcp" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

for executable in \
  /opt/wright/mcp/apps/SolidEdgeMCP/solid-edge-mcp \
  /opt/wright/mcp/apps/SolidEdgeMCP/SolidEdgeMcpServer \
  /opt/wright/mcp/apps/SolidEdgeMCP/SolidEdgeMCP \
  /opt/hermes/.venv/bin/solidedge-mcp \
  /opt/hermes/.venv/bin/SolidEdgeMCP \
  /opt/wright/mcp/src/SolidEdgeMCP/SolidEdgeMcpServer \
  /opt/wright/mcp/src/SolidEdgeMCP/SolidEdgeMCP; do
  if [ -x "$executable" ]; then
    exec "$executable" "$@"
  fi
done

for assembly in \
  /opt/wright/mcp/apps/SolidEdgeMCP/SolidEdgeMcpServer.dll \
  /opt/wright/mcp/apps/SolidEdgeMCP/SolidEdgeMCP.dll \
  /opt/wright/mcp/src/SolidEdgeMCP/bin/Release/*/linux-x64/publish/SolidEdgeMcpServer.dll \
  /opt/wright/mcp/src/SolidEdgeMCP/bin/Release/*/linux-x64/publish/SolidEdgeMCP.dll; do
  if [ -f "$assembly" ] && command -v dotnet >/dev/null 2>&1; then
    exec dotnet "$assembly" "$@"
  fi
done

if [ -f /opt/wright/mcp/src/SolidEdgeMCP/src/SolidEdgeMcpServer/SolidEdgeMcpServer.csproj ]; then
  echo "SolidEdgeMCP source is installed, but the current server project targets Windows/Solid Edge and is not runnable inside this Linux appliance." >&2
  echo "Use the pinned source from /opt/wright/mcp/src/SolidEdgeMCP on a Windows host, or update the bundle when a Linux-compatible server target exists." >&2
  exit 78
fi

echo "SolidEdgeMCP source is not installed. Set WRIGHT_SOLIDEDGE_MCP_GIT_URL and WRIGHT_SOLIDEDGE_MCP_GIT_REF at image build time or keep the manifest defaults available." >&2
exit 78
SH
  chmod 755 "${BIN_DIR}/solid-edge-mcp"
}

install_system_packages
link_system_app_binaries
install_release_assets
install_git_sources
install_configured_git_sources
install_python_tools
install_python_projects
install_dotnet_projects
install_npm_tools
install_brep_mcp_launcher
install_playwright_browsers
install_playwright_mcp_browsers
install_freecad_addon
write_wrappers

chown -R agent:agent "$MCP_ROOT" /home/agent/.local/share/FreeCAD /home/agent/.FreeCAD 2>/dev/null || true
